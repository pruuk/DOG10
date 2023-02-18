"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom
from evennia.utils import lazy_property
from .objects import ObjectParent
from evennia.utils import utils as utils
from world.handlers.traits import TraitHandler
from evennia.utils.logger import log_file
from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    # pull in handler for traits & trait-like attributes associated with the room
    @lazy_property
    def traits(self):
        """TraitHandler that manages room traits."""
        return TraitHandler(self)
    
    @lazy_property
    def biomes(self):
        """TraitHandler that manages room biomes."""
        return TraitHandler(self, db_attribute='biome')
    
    @lazy_property
    def status_effects(self):
        """TraitHandler that manages room status effects."""
        return TraitHandler(self, db_attribute='status_effects')
    
    def at_object_creation(self):
        "Called only at object creation and with update command."
        # clear traits and trait-like containers
        self.traits.clear()
        self.biomes.clear()
        self.status_effects.clear()
        
        # Add traits for the standard room. We'll add more room types as
        # subclasses and subclasses to give devs some stock rooms to wor from

        # size is measured in square meters. Default is a large outdoor room
        self.traits.add(key="size", name='Room Size', type='static', base=10000)
        ## note that base encumberance, carrying capacity of a room is set
        ## as a square of the room size
        self.traits.add(key="enc", name="Encumberance", type='counter', \
                        base=0, max=(self.traits.size.current ** 2), \
                        extra={'learn' : 0})
        # Elevation is measure in meters above sea level outdoors. Inside, the
        # 'ground' floor is 0. Every floor below is -N and above is +N floors
        self.traits.add(key='elev', name='Elevation Above Sea Level', \
                        type='static', base=100)
        # rather than using latitude and longitude, we're using a coordinate
        # system based upon the number of outdoor rooms away from the main
        # entrance and exit of the newbie school. That room will be 0,0 and all
        # other outdoor rooms *must* confirm to this standard. Indoor rooms
        # will have their own grid that is internally consistent
        self.traits.add(key='xcord', name='X Coordinate', type='static', \
                        base=0) # PLEASE CHANGE THIS AFTER CREATING A ROOM!
        self.traits.add(key='ycord', name='Y Coordinate', type='static', \
                        base=0) # PLEASE CHANGE THIS AFTER CREATING A ROOM!
        # rot is a masure of how steep the terrain is in this room on average
        # This should be a value between 0 and 1. For most rooms, this value
        # shouldn't exceed .25; Only the most extreme environments would be
        # more rugged than that
        self.traits.add(key='rot', name='Ruggedness of Terrain', \
                        type='static', base=0.03)
         # maximum number of tracks to store. Some terrain allows for tracks to
        # be readable even with a large amount of foot traffic.
        self.traits.add(key="trackmax", name="Maximum Readable Tracks", \
                        type="static", base=(round(self.traits.size.actual / 500))) # default of 20
        # boolean info attributes of the room
        self.db.info = {'non-combat room': False, 'outdoor room': True, \
                        'zone': 'The Outdoors'}
        # empty db attribute dictionary for storing tracks
        self.db.tracks = {}

        # add the overhead map symbol we want to use
        self.db.map_symbol = ['|043¡|n', '|143¡|n', '|243¡|n', '|343¡|n', '|443¡|n']

