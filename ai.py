# -*- coding: utf-8 -*-

# python imports
import random
from enum import Enum
from math import inf
import time
import os
import copy
import sys

from space import Action, CustomAgent, State

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import ECell, EDirection, Position
from ks.commands import ChangeDirection, ActivateWallBreaker

# my imports
from space import State, CustomAgent
import space

direct = {
    EDirection.Right: Action.Right,
    EDirection.Left: Action.Left,
    EDirection.Up: Action.Up,
    EDirection.Down: Action.Down
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


class AI(RealtimeAI):
    counter = 0

    def __init__(self, world):
        super(AI, self).__init__(world)

    def initialize(self):
        print('initialize')
        my_agent = space.CustomAgent(
            self.my_side,
            self.world.agents[self.my_side].direction,
            self.world.agents[self.my_side].position,
            self.world.scores[self.my_side],
            False,
            True,
            self.world.agents[self.my_side].wall_breaker_cooldown,
            self.world.agents[self.my_side].wall_breaker_rem_time,
            self.world.agents[self.my_side].health
        )
        enemy_agant = CustomAgent(
            self.other_side,
            self.world.agents[self.other_side].direction,
            self.world.agents[self.other_side].position,
            self.world.scores[self.other_side],
            False,
            True,
            self.world.agents[self.other_side].wall_breaker_cooldown,
            self.world.agents[self.other_side].wall_breaker_rem_time,
            self.world.agents[self.other_side].health
        )
        self.state = State(
            self.world.board,
            my_agent,
            enemy_agant
        )
        space.init_health = self.world.constants.init_health
        space.wall_breaker_cooldown = self.world.constants.wall_breaker_cooldown
        space.wall_breaker_duration = self.world.constants.wall_breaker_duration
        space.wall_score_coefficients = self.world.constants.wall_score_coefficient
        space.area_wall_crash_score = self.world.constants.area_wall_crash_score
        space.my_wall_crash_score = self.world.constants.my_wall_crash_score
        space.enemy_wall_crash_score = self.world.constants.enemy_wall_crash_score
        space.max_cycles = self.world.constants.max_cycles

        print(space.init_health)
        print(space.wall_breaker_cooldown)
        print(space.wall_breaker_duration)
        print(space.wall_score_coefficients)
        print(space.area_wall_crash_score)
        print(space.my_wall_crash_score)
        print(space.enemy_wall_crash_score)
        print(space.max_cycles)

    def decide(self):
        t1 = time.time()
        my_agent = space.CustomAgent(
            self.my_side,
            self.world.agents[self.my_side].direction,
            self.world.agents[self.my_side].position,
            self.world.scores[self.my_side],
            self.world.agents[self.my_side].wall_breaker_rem_time > 0,
            self.world.agents[self.my_side].wall_breaker_rem_time == 0 and
            self.world.agents[self.my_side].wall_breaker_cooldown == 0,
            self.world.agents[self.my_side].wall_breaker_cooldown,
            self.world.agents[self.my_side].wall_breaker_rem_time,
            self.world.agents[self.my_side].health
        )
        enemy_agant = CustomAgent(
            self.other_side,
            self.world.agents[self.other_side].direction,
            self.world.agents[self.other_side].position,
            self.world.scores[self.other_side],
            self.world.agents[self.other_side].wall_breaker_rem_time > 0,
            self.world.agents[self.other_side].wall_breaker_rem_time == 0 and
            self.world.agents[self.other_side].wall_breaker_cooldown == 0,
            self.world.agents[self.other_side].wall_breaker_cooldown,
            self.world.agents[self.other_side].wall_breaker_rem_time,
            self.world.agents[self.other_side].health
        )
        self.state = State(
            self.world.board,
            my_agent,
            enemy_agant
        )

        t2 = time.time()
        print('\t\t\tdecide', t2 - t1)

        act = self.state.alpha_beta_search(12)
        try:
            direct = direct_reverse[act]
            if act.value[2] == 1:
                self.send_command(ActivateWallBreaker())
            self.send_command(ChangeDirection(direct))
        except:
            pass

        print(time.time() - t2)

        space.print_board(self.state)

# remtime = cooldown = 0 ==> can active breaker
