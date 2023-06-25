from enum import Enum
from math import inf
from ks.models import ECell, EDirection, Position
from colorama import Fore, Style
import time
from math import ceil
from random import randint

init_health = 3
wall_breaker_cooldown = 12
wall_breaker_duration = 6
wall_score_coefficients = 1
area_wall_crash_score = -20
my_wall_crash_score = -40
enemy_wall_crash_score = -60
max_cycles = 300

full_block = "\u2588"

lightY = Fore.LIGHTGREEN_EX
lightB = Fore.LIGHTBLUE_EX
INF = chr(8734)


class Action(Enum):
    Right = [0, 1, 0]
    Left = [0, -1, 0]
    Up = [-1, 0, 0]
    Down = [1, 0, 0]
    RightBreak = [0, 1, 1]
    LeftBreak = [0, -1, 1]
    UpBreak = [-1, 0, 1]
    DownBreak = [1, 0, 1]


direct = {
    EDirection.Right: Action.Right,
    EDirection.Left: Action.Left,
    EDirection.Up: Action.Up,
    EDirection.Down: Action.Down,
}

direct_reverse = {
    Action.Right: EDirection.Right,
    Action.RightBreak: EDirection.Right,
    Action.Left: EDirection.Left,
    Action.LeftBreak: EDirection.Left,
    Action.Up: EDirection.Up,
    Action.UpBreak: EDirection.Up,
    Action.Down: EDirection.Down,
    Action.DownBreak: EDirection.Down,
}

side_wall = {"Blue": ECell.BlueWall, "Yellow": ECell.YellowWall}


class CustomAgent:
    def __init__(
            self,
            side,
            direction,
            pos: Position,
            point,
            is_breaker_active=False,
            can_active_breaker=True,
            breaker_cooldown=0,
            breaker_rem_time=0,
            health=init_health,
    ):
        self.side = side
        self.direction = direction
        self.pos = pos
        self.point = point
        self.is_breaker_active = is_breaker_active
        self.can_active_breaker = can_active_breaker
        self.breaker_cooldown = breaker_cooldown
        self.breaker_rem_time = breaker_rem_time
        self.health = health

    def update_breaker(self):
        if self.breaker_rem_time > 0:
            self.breaker_rem_time -= 1
            self.breaker_cooldown -= 1

        elif 0 < self.breaker_cooldown < wall_breaker_cooldown:
            self.breaker_cooldown -= 1

        if self.breaker_rem_time == 1:
            self.is_breaker_active = False

        if self.breaker_cooldown == 0:
            self.can_active_breaker = True

    def get_valid_actions(self) -> list[Action]:
        reti = list(Action)[: None if self.can_active_breaker else 4]
        act = direct[self.direction]

        for i in range(2 if self.can_active_breaker else 1):
            unavailable = Action([-act.value[0], -act.value[1], i])
            reti.remove(unavailable)

        return reti


class State:
    def __init__(
            self, board=None, me: CustomAgent = None, enemy: CustomAgent = None
    ) -> None:
        self.board = board
        self.me = me
        self.enemy = enemy

    def is_over(self):
        return \
                (self.me.health <= 0) or \
                (self.me.health <= 0) or \
                (self.me.pos.x == self.enemy.pos.x and self.me.pos.y == self.enemy.pos.y)
        # one less

    def f(self):
        difference = (self.me.point - self.enemy.point)
        if difference > 0 and self.is_over():
            return inf
        if difference < 0 and self.is_over():
            return -inf
        return difference + (self.me.health - self.enemy.health) * init_health

    def commit_action(self, agent: CustomAgent, act: Action):
        # returns: [curr_cell, curr_rem_time, curr_cooldown]  *curr = current

        new_pos = Position(
            agent.pos.x + act.value[1], agent.pos.y + act.value[0])

        # Breaker_rem_time and cooldown
        if act.value[2] == 1 and agent.can_active_breaker and not agent.is_breaker_active:
            agent.can_active_breaker = False
            agent.is_breaker_active = True
            agent.breaker_cooldown = wall_breaker_cooldown
            agent.breaker_rem_time = wall_breaker_duration + 1

        # we should make wall behind ourselves and get wall_score_coefficient for it:
        self.board[agent.pos.y][agent.pos.x] = side_wall[agent.side]
        agent.point += wall_score_coefficients

        # move in direction:
        new_cell = self.board[new_pos.y][new_pos.x]

        # check collapse with areaWall:
        if new_cell == ECell.AreaWall:
            agent.point += area_wall_crash_score
            agent.health = 0

        elif new_cell == ECell.BlueWall:
            if self.me.side == 'Blue':
                self.me.point -= 1
            else:
                self.enemy.point -= 1

            if not agent.is_breaker_active:  # not on wall breaker
                if agent.health == 1:
                    agent.point += (
                        my_wall_crash_score if agent.side == "Blue" else enemy_wall_crash_score
                    )
                agent.health -= 1

        elif new_cell == ECell.YellowWall:
            if self.enemy.side == 'Blue':
                self.me.point -= 1
            else:
                self.enemy.point -= 1

            if not agent.is_breaker_active:
                if agent.health == 1:
                    agent.point += (
                        enemy_wall_crash_score if agent.side == "Blue" else my_wall_crash_score
                    )
                agent.health -= 1

        # make new_cell an empty cell
        if agent.health > 0:
            self.board[new_pos.y][new_pos.x] = ECell.Empty
            agent.pos = new_pos
            agent.direction = direct_reverse[act]
            agent.update_breaker()

        return new_cell

    def reverse_action(self, old_agent: CustomAgent, agent: CustomAgent, last_cell):

        self.board[agent.pos.y][agent.pos.x] = last_cell

        if last_cell == ECell.BlueWall:
            if self.me.side == 'Blue':
                self.me.point += 1
            else:
                self.enemy.point += 1

        elif last_cell == ECell.YellowWall:
            if self.enemy.side == 'Blue':
                self.me.point += 1
            else:
                self.enemy.point += 1

        agent.can_active_breaker = old_agent.can_active_breaker
        agent.is_breaker_active = old_agent.is_breaker_active
        agent.breaker_cooldown = old_agent.breaker_cooldown
        agent.breaker_rem_time = old_agent.breaker_rem_time
        agent.direction = old_agent.direction
        agent.health = old_agent.health
        agent.point = old_agent.point
        agent.pos = old_agent.pos

        self.board[agent.pos.y][agent.pos.x] = ECell.Empty

    def alpha_beta_search(self, depth=8, alpha=-inf, beta=inf):
        v, minV = -inf, -inf
        agent = self.me
        act_to_do = None
        for act in agent.get_valid_actions():
            copyAgent = CustomAgent(
                None,
                agent.direction,
                agent.pos,
                agent.point,
                agent.is_breaker_active,
                agent.can_active_breaker,
                agent.breaker_cooldown,
                agent.breaker_rem_time,
                agent.health,
            )
            last_cell = self.commit_action(agent, act)
            minV = self.min_value(alpha, beta, depth - 1)
            if minV > v:
                act_to_do = act
                v = minV
            # elif minV == v:
            #     x = randint(0, 2)
            #     if x==1 and act.value[2]!=1:
            #         act_to_do = act 
            try:
                print('\t', act.name, (6 - len(act.name)) * ' ', '\t', f'-{INF}' if minV == -inf else minV, '\t')
            except:
                pass
            self.reverse_action(copyAgent, agent, last_cell)
            if v >= beta:
                return act_to_do
            alpha = max(alpha, v)
        # print_board(self)
        return act_to_do

    def min_value(self, alpha, beta, depth):
        if depth < 1:
            return self.f()

        v = inf
        agent = self.enemy
        for act in agent.get_valid_actions():
            copyAgent = CustomAgent(
                None,
                agent.direction,
                agent.pos,
                agent.point,
                agent.is_breaker_active,
                agent.can_active_breaker,
                agent.breaker_cooldown,
                agent.breaker_rem_time,
                agent.health,
            )
            last_cell = self.commit_action(agent, act)
            if self.is_over():
                v = min(self.f(), v)
            else:
                v = min(self.max_value(alpha, beta, depth - 1), v)
            self.reverse_action(copyAgent, agent, last_cell)
            if v <= alpha:
                return v
            beta = min(beta, v)

        return v

    def max_value(self, alpha, beta, depth):
        if depth < 1:
            return self.f()

        v = -inf
        agent = self.me
        for act in agent.get_valid_actions():
            copyAgent = CustomAgent(
                None,
                agent.direction,
                agent.pos,
                agent.point,
                agent.is_breaker_active,
                agent.can_active_breaker,
                agent.breaker_cooldown,
                agent.breaker_rem_time,
                agent.health,
            )
            last_cell = self.commit_action(agent, act)
            v = max(self.min_value(alpha, beta, depth - 1), v)
            self.reverse_action(copyAgent, agent, last_cell)

            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def hope(self, side: str) -> int:
        pass


"""
1.  Breaker_rem_time and coolDown
2.  Make Wall in Current Position
3.  Move in Direction
4.  Check Collapse With Opponent Then AreaWall
5.  Check Collapse With Players Walls and Destroying them Or Dying
"""


def eval_color(cell: ECell, x: int, y: int, blue: Position, yellow: Position):
    if cell == ECell.AreaWall:
        return Fore.LIGHTRED_EX
    if cell == ECell.BlueWall:
        return lightB
    if cell == ECell.YellowWall:
        return lightY
    else:
        if x == blue.x and y == blue.y:
            return Fore.BLUE
        if x == yellow.x and y == yellow.y:
            return Fore.GREEN
        return Fore.WHITE


def print_properties(property_name: str, blue: str, yellow: str):
    print(f'  {property_name}\t{lightB}{blue}\t{lightY}{yellow}', end='')


def print_board(state: State):
    board, blue, yellow = state.board, None, None

    if state.me.side == 'Blue':
        blue = state.me
        yellow = state.enemy
    else:
        blue = state.enemy
        yellow = state.me

    print("", end=" " * 3)
    for i in range(len(board[0])):
        print(f" {i}", end=" " if i < 10 else '')
    print()
    for i in range(len(board)):
        print(f" {Fore.RESET}{i}", end="  " if i < 10 else " ")
        for j in range(len(board[i])):
            print(
                eval_color(board[i][j], j, i, blue.pos,
                           yellow.pos) + full_block * 3,
                end=Fore.RESET,
            )

        if i == 0:
            print_properties('Health', blue.health, yellow.health)
        elif i == 1:
            print_properties('Point ', blue.point, yellow.point)
        elif i == 3:
            print_properties('RemTime', blue.breaker_rem_time,
                             yellow.breaker_rem_time)
        elif i == 4:
            print_properties('CoolDown', blue.breaker_cooldown,
                             yellow.breaker_cooldown)
        elif i == 6:
            mapp = {True: 'T', False: 'F'}
            print_properties('Breaker', mapp[blue.is_breaker_active],
                             mapp[yellow.is_breaker_active])
        print()


def make_board(N):
    boarder = [0, N - 1]
    center = [N // 2, N // 2 - 1]
    board = []
    for i in range(N):
        inner = []
        for j in range(N):
            if j in boarder or i in boarder:
                inner.append(ECell.AreaWall)
            elif j in center and i in center:
                inner.append(ECell.AreaWall)
            else:
                inner.append(ECell.Empty)
        board.append(inner)
    return board


def show_options(agent: CustomAgent):
    counter = 1
    actions = list(Action)
    valid = agent.get_valid_actions()
    invalid = []

    for i in actions:
        if i not in valid:
            print(Fore.RED + Style.DIM, end='')
            invalid.append(counter)
        else:
            print(Fore.LIGHTWHITE_EX + Style.BRIGHT, end='')
        print(f'\t\t{counter}) {i.name}')
        print(Fore.RESET + Style.RESET_ALL, end='')
        counter += 1
    while (True):
        try:
            i = int(input('Enter a Number\t')) - 1
            if i + 1 in invalid:
                print('Xkholi')
                continue
            return actions[i]
        except:
            continue


if __name__ == "__main__":

    print('\n' * 20)
    N = 20
    blueAgent = CustomAgent("Blue", EDirection.Down, Position(1, 1), 0)
    yellowAgent = CustomAgent(
        "Yellow", EDirection.Left, Position(N - 2, N - 2), 0)
    state = State(board=make_board(N), me=blueAgent, enemy=yellowAgent)

    print_board(state)

    while (True):
        x = time.time()
        ai_act = state.alpha_beta_search(6)
        print(Fore.LIGHTMAGENTA_EX + '%.3f' % (time.time() - x) + Fore.RESET)
        state.commit_action(state.me, ai_act)

        act = show_options(state.enemy)
        state.commit_action(state.enemy, act)

        print_board(state)
