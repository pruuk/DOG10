"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property
from .objects import ObjectParent
from evennia.utils import utils as utils
from world.handlers.traits import TraitHandler
from evennia.utils.logger import log_file
from world.handlers.randomness_handler import distro_return_a_roll_sans_crit as distroll


class Character(ObjectParent, DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_post_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    # pull in handlers for traits and trait like attributes associated with the character
    @lazy_property
    def traits(self):
        """TraitHandler that manages room traits."""
        return TraitHandler(self)
    
    @lazy_property
    def talents(self):
        """TraitHandler that manages room talents."""
        # note: These will be used rarely for rooms
        return TraitHandler(self, db_attribute='talents')
    
    @lazy_property
    def status_effects(self):
        """TraitHandler that manages room status effects."""
        return TraitHandler(self, db_attribute='status_effects')
    
    def at_object_creation(self):
        "Called only at object creation and with update command."
        # clear traits and trait-like containers
        self.traits.clear()
        self.talents.clear()
        self.status_effects.clear()
        
        # set primary attribute scores
        self.traits.add(key='Dex', name='Dexterity', type='static', \
                        base=distroll(100), extra={'learn' : 0})
        self.traits.add(key='Str', name='Strength', type='static', \
                        base=distroll(100), extra={'learn' : 0})
        self.traits.add(key='Vit', name='Vitality', type='static', \
                        base=distroll(100), extra={'learn' : 0})
        self.traits.add(key='Per', name='Perception', type='static', \
                        base=distroll(100), extra={'learn' : 0})
        self.traits.add(key='FOP', name='Force of Personality', type='static', \
                        base=distroll(100), extra={'learn' : 0})
    
