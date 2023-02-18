# -*- coding: utf-8 -*-
"""
    This file will contain the functions necessary for returning a random number as needed for different
    actions within the game. For some random actions, this number will be picked from a normal distribution
    (like a bell curve). For other actions, it will be more like a dice roll. Some actions will have a mixture
    of both in practice.
    
    Learning & progression of skills/talents/abilities/spells will be possible in Delusion of Grandeur only by
    using that skill/talent/ability/spell or observing the same. The trigger for having a chance to learn will
    be critical successees or critical failures in this randomness controller file. The theory is we learn best
    spectacular successes and major failures.
"""
    
import numpy as np
import random
from evennia.utils.logger import log_file
    
# simplest distribution curve based check
def distro_return_a_roll(number):
    """
    Takes in a number (integer, float, etc)
    and outputs a random number from a normal distribution
    with the skill rating at the mean.
    Generally, scores should be around 100 for human "normal". They'll be
    higher than 100 for exceptionally skilled or talented individuals. For
    example, someone that powerlifts might have a strength score approaching
    200 or 300.
    Ability scores and item durability are a good use for this function.
    """
    roll = int(np.random.default_rng().normal(loc=number, scale=number/10))
    log_file("Distribution roller. Input: {number} Output: {roll}")
    return roll
        