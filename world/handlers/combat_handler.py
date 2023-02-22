# coding=utf-8
""""
This script file will contain the combat handler that will orchestrate combat that is held within a single
room. This will include generating the room's battlefield map of subroom sections at the start of combat,
adding combtants, spawn actionhandlers for indivuduals' single round of actions, and then cleaning up after
combat has ceased.
"""
import random
from evennia import DefaultScript
from evennia.utils.logger import log_file
from evennia import create_object, create_script
from evennia import utils

class CombatHandler(DefaultScript):
    """
    This implements the combat handler script.
    """
    # standard script hooks
    def at_script_creation(self):
        "Called when script is first created"
        
        self.key = "combat_handler_%i" % random.randint(1, 1000000)
        self.desc = "handles combat"
        self.interval = 5  # five second timeout
        self.start_delay = False
        self.persistent = False
        
        # store all combatants
        self.db.characters = {}
        # store all room subsections for the room's battlefield. This will be a named dictionary of all
        # subroom section objects, the combatants in those subroom sections (if any)
        self.db.battlefield_map = {}
        # store all actions for each turn
        self.db.turn_actions = {}
        # store all temp vars for the characters
        # NOTE: to begin with, these will be stored on the character, but
        # later we will move these to the handler or to the mini-script
        # for carrying out each attack.
        self.db.char_temp_vars = {}
        # keep track of round # so it is easier to debug
        self.db.round_count = 1
        
    def _init_character(self, character):
        """
        This initializes handler back-reference
        and combat cmdset on a character
        """
        character.ndb.combat_handler = self
        character.cmdset.add("commands.combat_commands.CombatCmdSet")
        log_file(f"Added backref for {self.name} to {character.name}.", \
                 filename='combat_step.log')
        
    def _cleanup_character(self, character):
        """
        Remove character from handler and clean
        it of the back-reference and cmdset
        """
        log_file(f"Starting cleanup for {character.name}.", \
                 filename='combat_step.log')
        character.cmdset.delete("commands.combat_commands.CombatCmdSet")
        character.db.info['In Combat'] = False
        character.db.info['Position'] = 'standing'
        
    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to
        all characters as well as re-assign the cmdset.
        """
        for character in self.db.characters.values():
            self._init_character(character)
    
    def at_stop(self):
        "Called just before the script is stopped/destroyed."
        log_file("start of char cleanup func", filename='combat_step.log')
        for character in list(self.db.characters.values()):
            # note: the list() call above disconnects list from database
            self._cleanup_character(character)
        del self.db.characters[dbref]
        del self.db.turn_actions[dbref]
        del self.db.char_temp_vars[dbref]
        
     def at_repeat(self):
        """
        This is called every self.interval seconds (turn timeout) or
        when force_repeat is called.
        At repeat, the plan is to use up an action from the queue of actions
        for each character. The action will then be converted into a smaller
        script for that action of a type related to the action type. For example,
        a character wanting to grapple will create a grapple action script,
        which will then carry out the action and self delete.
        """
        for character in self.db.characters.values():
            dbref = character.id
            # update the char variables
            log_file("*********************************************************************", \
                     filename='combat.log')
            log_file(f"START OF ROUND: {self.db.round_count} FOR {character.name}", \
                     filename='combat_step.log')
            # TODO: Implement overhead map updates
            # TODO: Implenment range checks
            # TODO: Implement character position checks
            # TODO: Implement character death, yield, flee, & mercy checks
            # TODO: Implement refresh of temporary combat variables
            # TODO: Implement footwork checks
            # TODO: Implement other combat validity checks
            # TODO: Implement combat action picker
            # TODO: Implement combat action handler for individual character actions
            # TODO: Implement communication of combat outcomes for the round to all parties in the room
            log_file(f"END OF AT_REPEAT FOR {character.name}.", filename='combat_step.log')
        self.db.round_count += 1
        
    # combat handler methods
    def add_character(self, character):
        "Add combatant to handler"
        dbref = character.id
        self.db.characters[dbref] = character
        self.db.turn_actions[dbref] = [(character.db.info['Default Attack'])]
        log_file(f"Added {character.name} to {self.name}", \
                 filename='combat_step.log')
        # set up back-reference
        self._init_character(character)
        # set character to be in combat
        character.db.info['In Combat'] = True
        
    def remove_character(self, character):
        "Remove combatant from handler"
        if character.id in self.db.characters:
            self._cleanup_character(character)
        if not self.db.characters:
            # if no more characters in battle, kill this handler
            self.stop()
        elif len(self.db.characters) < 2:
            # less than 2 chars in combat, ending combat
            log_file("less than 2 characters in combat. killing handler", \
                      filename='combat_step.log')
            self.stop()
            
    def add_action(self, action, character):
        """
        Called by combat commands to register an action with the handler.
         action - string identifying the action, like "hit" or "parry"
         character - the character performing the action
         target - the target character or None
        actions are stored in a dictionary keyed to each character, each
        of which holds a list of max 2 actions. An action is stored as
        a tuple (character, action, target).
        """
        log_file(f"{self.key} - Start of add_action method for {character.name}.",
                 filename='combat_step.log')
        dbref = character.id
        self.db.turn_actions[dbref].insert(0, action)
        log_file(f"Added action: {action} for {character.name}", \
                 filename='combat_step.log')
        return

    def remove_action(self, character):
        """
        Pops off the action in the zero position if appropriate.
        Returns the desired action for the round.
        """
        log_file("start of remove action func", filename='combat_step.log')
        dbref = character.id
        if len(self.db.turn_actions[dbref]) > 0:
            log_file(f"Action at top of queue: {self.db.turn_actions[dbref][0]}", \
                 filename='combat_step.log')
        else:
            log_file(f"No Actions in queue: {self.db.turn_actions[dbref]}", \
                 filename='combat_step.log')
            return character.db.info['Default Attack']
        if self.db.turn_actions[dbref][0] == character.db.info['Default Attack']:
            return character.db.info['Default Attack']
        elif self.db.turn_actions[dbref][0] in ['flee', 'yield', 'disengage']:
            # for flee type actions, we won't pop it off. keep trying until we succeed
            return self.db.turn_actions[dbref][0]
        else:
            popped_action = self.db.turn_actions[dbref].pop(0)
            log_file(f"Returning action: {popped_action}", filename='combat_step.log')
            return popped_action