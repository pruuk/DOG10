# coding=utf-8
"""
Generic item classes and their base functions.
"""

from typeclasses.objects import Object
from typeclasses.rooms import BuildingEntrance
from evennia import create_object
from evennia.prototypes.spawner import spawn
from evennia.utils.logger import log_file
from evennia.utils import lazy_property
from world.handlers.traits import TraitHandler
from evennia import utils as utils

class Item(Object):
    """
    Typeclass for Items.
    Attributes:
        value (int): monetary value of the item in CC
        weight (float): weight of the item
    """
    value = 1 # default value in copper coins
    mass = 0.5 # default mass in kilograms

    @lazy_property
    def traits(self):
        """TraitHandler that manages item traits."""
        return TraitHandler(self)

    @lazy_property
    def status_effects(self):
        """TraitHandler that manages item status effects."""
        return TraitHandler(self, db_attribute='status_effects')


    @lazy_property
    def talents(self):
        """TraitHandler that manages room talents."""
        # note: These will be used rarely for rooms
        return TraitHandler(self, db_attribute='talents')

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.traits.clear()
        self.locks.add(";".join(("puppet:perm(Builder)",
                                 "equip:false()",
                                 "get:all()"
                                 )))
        self.traits.add(key='val', name='Monetary Value', type='static', \
                        base=self.value)
        self.traits.add(key='mass', name='Mass (in Kilograms)', type='static', \
                        base=float(self.mass))
        self.traits.add(key="hp", name="Health Points", type="gauge", \
                        base=10, extra={'learn' : 0})
        # Add a measure of quality of the item from 0.01 (basically trash) to 1
        # (superbly master crafted item)
        self.traits.add(key="qual", name="Quality", type="static", \
                        base=0.25, extra={'learn' : 0})
        # Add a trait that measures the condition of the item. This can and will
        # degrade over time for most items. Scale is from 0 (broken) to 1 (new)
        self.traits.add(key="cond", name="Condition", type="static", \
                        base=1, extra={'learn' : 0})
        # carrying capacity of the item. Useful for chairs, quivers, or any
        # item that might have another item in its inventory
        self.traits.add(key="cap", name="Container Capacity", type="static", \
                        base=10, extra={'learn' : 0})
        # attribute that stores which items in this item's inventory are 'parts'
        # or components of this item. Ex. a chair might have legs, seat, and
        # a back. Or it may just be a single object. This is entirely up to the
        # builder
        self.db.parts = []


    def at_before_move(self, getter):
        """
        Called when a character or NPC tries to get the item. Checks to see if
        adding this amount of weight will make the character/NPC overencumbered.
        """
        log_file(f"trying to move {self.key} to {getter.name}", filename='item_moves.log')
        if getter.traits.enc.current + self.traits.mass.current > getter.traits.enc.max:
            if utils.inherits_from(obj, 'typeclasses.npcs.NPC') or utils.inherits_from(obj, 'typeclasses.characters.Character'):
                # this item is too heavy for the getter to pick up, cancel move
                log_file(f"{self.name} is too heavy for {getter.name} to pick up.", \
                         filename='item_moves.log')
                getter.msg(f"{self.name} is too heavy for you to pick up.")
                return False
            # getter is a non-character. We're trying to put something in something else
            else:
                log_file(f"{getter.name} is a non character/NPC and doesn't have room to fit {self.name}.", \
                         filename='item_moves.log')
                return False

        else:
            log_file(f"{getter.name} calculating new enc value.", \
                     filename='item_moves.log')
            getter.calculate_encumberance()
            log_file(f"{getter.name} Enc: {getter.traits.enc.current}", \
                     filename='item_moves.log')
            return True

    def at_get(self, getter):
        "Called just after getter picks up the object"
        getter.calculate_encumberance()

    def at_drop(self, dropper):
        "Called just after dropper drops this object"
        dropper.calculate_encumberance()

    def at_break(self):
        """ Item has been broken. Replace it with broken bits of """
        self.location.msg_contents(f"{self.key} has broken!")
        broken_junk = create_object('typeclasses.items.Trash',
                             key=f'Broken pieces of {self.key}',
                             location=self.location,
                             parent_materials=self.material.all_dict)
        self.delete()

    def change_condition(self, amount):
        """ Called when condition of the item is degraded or repaired """
        self.traits.cond.mod + amount
        if self.traits.cond.current <= 0:
            self.at_break()


class Trash(Item):
    """
    Any item that has been completely broken. Worthless, other than it can be
    canibalized for parts (maybe).
    """
    value = 0

    def at_object_creation(self, parent_materials):
        "Only called at creation and forced update"
        super().at_object_creation()
        for material, data in parent_materials.items():
            self.materials.add(key=data[key])


class Bundable(Item):
    """
    Items that can be bundled together as stored as a single object to make it
    easier on the db infra.
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.db.bundle_size = 999
        self.db.prototype_name = None

    # TODO: Add in function for at_get and at_drop that includes bundling


class Bundle(Item):
    """Typeclass for bundles of Items."""
    def expand(self):
        """Expands a bundle into its component items."""
        for i in list(range(self.db.quantity)):
            p = self.db.prototype_name
            spawn(dict(prototype=p, location=self.location))
        self.delete()


class Equippable(Item):
    """
    Typeclass for equippable Items.
    Attributes:
        slots (str, list[str]): list of slots for equipping
        multi_slot (bool): operator for multiple slots. False equips to
            first available slot; True requires all listed slots available.
    """
    slots = None
    multi_slot = False

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.locks.add("puppet:false();equip:true()")
        self.db.slots = self.slots
        self.db.multi_slot = self.multi_slot
        self.db.used_by = None

    def at_equip(self, character):
        """
        Hook called when an object is equipped by character.
        Args:
            character: the character equipping this object
        """
        pass

    def at_remove(self, character):
        """
        Hook called when an object is removed from character equip.
        Args:
            character: the character removing this object
        """
        pass

    def at_drop(self, dropper):
        super(Equippable, self).at_drop(dropper)
        if self in dropper.equip:
            dropper.equip.remove(self)
            self.at_remove(dropper)


class Tool(Equippable):
    """
    Class for tools that can be used to do a specific task, such as hammers,
    shovels, pickaxes, saws, etc.
    """
    slots = ['hand']
    multi_slot = False

    # Most tools can be used as improvised weapons
    pdamage = 1.03 # this is a multiplier!
    sdamage = 1
    cdamage= 1
    handedness = 1
    minrange = 0
    maxrange = 1

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.traits.add(key='minran', name='Minimum Weapon Range', type='static', \
                        base=self.minrange)
        self.traits.add(key='maxran', name='Maximum Weapon Range', type='static', \
                        base=self.maxrange)
        self.traits.add(key='pdamm', name='Base Weapon Physical Damage Multiplier', \
                        type='static', base=self.pdamage, extra={'learn' : 0})
        self.traits.add(key='sdamm', name='Base Weapon Stamina Damage Multiplier', \
                        type='static', base=self.sdamage, extra={'learn' : 0})
        self.traits.add(key='cdamm', name='Base Weapon Conviction Damage Multiplier', \
                        type='static', base=self.cdamage, extra={'learn' : 0})
        self.db.handedness = self.handedness
        self.db.combat_cmdset = 'commands.combat.MeleeWeaponCmdSet'
        self.db.combat_descriptions = {
        'hit': "hits for",
        'miss': "misses",
        'dodged': 'attacks, but is dodged by',
        'blocked': 'attacks, but is blocked by'
        }


class Furnishing(Item):
    """
    Typeclass for furnishing items.
    Some furnishings can be sat on, or serve as a bed (or both).
    When a player or NPC is using a furnishing in this fashion, they are
    in the furnishing's inventory.
    NOTE: It is important to change the carrying capacity and sit/bed
    values as appropriate after a furnishing has been created if you want
    characters and NPCs to sit in them
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        # Can this be sat upon? Can it be used as a bed?
        self.db.sit = False
        self.db.bed = False
        self.db.hang = False # can this hang on a wall? ex: painting
        # trait for how comfortable this furnishing is to sit or lay on. The
        # higher this value, the more a character or NPC recovers. Scale is from
        # 0 (no comfort) to 1 (most comfortable in the world)
        self.traits.add(key="comfort", name="Comfort", type="static", \
                        base=0.5, extra={'learn' : 0})
        # traits for furnishings that provide light. Will not provide light by
        # default
        self.traits.add(key="light", name='Light', type="static", \
                        base = 0, extra={'fuel' : None})
        self.db.lit = False
        self.db.powered_by = None # type of fuel if this is a light

    def at_sit(self, sitter):
        """ Called when someone tries to sit on this furnishing."""
        if self.db.sit:
            if sitter.traits.mass.current > self.traits.cap.current:
                # The sitter is too heavy, will break the item
                sitter.msg("You're too heavy! You've broken {self.key}!")
                self.at_break()
        else:
            sitter.msg(f"You try to sit on {self.key}, but can't figure out how.")

    def at_lay(self, layer):
        """ Called when someone tries to lay on this furnishing."""
        if self.db.bed:
            if sitter.traits.mass.current > self.traits.cap.current:
                # The layer is too heavy, will break the item
                sitter.msg("You're too heavy! You've broken {self.key}!")
                self.at_break()
        else:
            sitter.msg(f"You try to lay on {self.key}, but can't figure out how.")

    def at_hang(self, hanger):
        """ Called when someone wants to hang a funsihing on a wall"""
        if self.db.hang:
            self.location.msg_contents(f"{hanger.name} hangs {self.key} on the wall.")
            self.move_to(hanger.location)


class LightSource(Equippable):
    """
    Typeclass for Items that provide light AND can be equipped.
    Some furnishings also provide light
    """
    slots = ['hand']
    multi_slot = False

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.locks.add("puppet:false();equip:true()")
        self.db.slots = self.slots
        self.db.multi_slot = self.multi_slot
        self.db.used_by = None
        # scale for light is how large of an area will be lit (in square meters)
        self.traits.add(key="light", name='Light', type="static", \
                        base = 100, extra={'fuel' : 'oil'})
        # default fuel type is Oil. Other types include: wood, fat, gas, battery
        # and self (think of a torch)
        self.db.lit = False
        self.db.powered_by = None # type of fuel

    def at_light(self, lighter=None):
        """ Called when the object is lit """
        if lighter:
            lighter.location.msg_contents(f"{lighter.nanme} lights {self.key}.")
        else:
            self.location.msg_contents(f"{self.key} is lit.")
        self.db.lit = True

    def at_darken(self, darkener=None):
        """ Called when an item is extinguished or runs out of fuel """
        if darkener:
            darkener.location.msg_contents(f"{lighter.nanme} extinguishes {self.key}.")
        else:
            self.location.msg_contents(f"{self.key} is extinguished.")
        self.db.lit = False


class RoadsAndTrail(Item):
    """
    Typeclass for road and trail objects. These can be repaired and damaged by
    human activity. They can also be damaged by events like weather (via status
    effects).
    """

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.traits.mass.base=100000
        self.traits.hp.base=10000


class Component(Item):
    """
    Typeclass for items that can be gathered and then used as raw materials for
    crafting useful and/or equippable objects.
    """

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()

    def at_craft(self, crafter):
        """ These items are consumed as part of crafting. """
        crafter.msg(f"{self.key} is consumed during crafting.")
        self.delete()

class Consumnable(Item):
    """ Subtype of item that is consumed. May have a number of charges. """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.traits.add(key="charge", name="Charges", type="gauge", \
                        base=10, extra={'learn' : 0})

    def at_consume(self, charges_to_consume):
        """ Consume one or more charges """
        self.traits.charge.mod - charges_to_consume
        if self.traits.charge.current <= 0:
            self.at_consumed()

    def at_consumed(self):
        """ Consumable item is depleted """
        self.location.msg_contents(f"{self.key} is consumed.")
        self.delete()


class Building(Item):
    """
    Subtype of item that is a building that contains one or more rooms.
    Since the rooms will be indoor rooms, they will have a self-consistent
    set of map coordinates.
    When a building is created, a single room will be spawned that will be
    located in the room's inventory. That building itself will be in the
    inventory of a larger outside type room.
    It is REQUIRED that room direction cardinality be consistent within a
    building between the rooms in that building. Use the trait 'Elevation' to
    handle floors/levels inside the building; The entrance should generally
    default to 0 elevation.
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        # set several of the traits to match a building
        self.traits.mass.base = 100000
        self.traits.hp.base = 1000000
        self.traits.val.base = 25000
        self.traits.cap.base = 50000
        # make the first room inside the building
        self.make_building_entry_room()

    def make_building_entry_room(self):
        """
        Creates a room that is inside the Building object. This entry room
        can then have any number of rooms connected to it that should be set as
        indoor rooms. Floors within a building are indicated by the elevation
        trait (0 is ground floor, 1 is floor above, -1 is floor below). Please
        ensure the build description and attributes fit the number of rooms
        inside the building. To create additional exits and extrances for the
        building, use the Open command to make exits between an internal room
        and an outdoor one.
        """
        entryway_room = create_object('typeclasses.rooms.BuildingEntrance',
                    key=f'Entryway for {self.name}',
                    location=self,
                    home=self)
        # set the zone name to match the name of the building
        entryway_room.db.info['zone'] = str(self.key)
        self.db.entryway = entryway_room


class Town(Item):
    """
    Town object. Much like the building, this will be a self-contained zone
    that makes up the rooms in the town and will be built with a command to
    create an enter <townname> exit to the Town.
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        # set several of the traits to match a building
        self.traits.mass.base = 1000000
        self.traits.hp.base = 10000000
        self.traits.val.base = 250000
        self.traits.cap.base = 5000000
        # make the first room inside the building
        self.make_building_entry_room()

    def make_building_entry_room(self):
        """
        Creates a room that is inside the Town object. This will be the 0,0
        room for the town.
        """
        entryway_room = create_object('typeclasses.rooms.TownEntrance',
                    key=f'Entrance to {self.name}',
                    location=self,
                    home=self)
        # set the zone name to match the name of the building
        entryway_room.db.info['zone'] = str(self.key)
        self.db.entryway = entryway_room


class Vehicle(Item):
    """
    Subtype of item that can be used to carry large amounts of cargo from one
    place to another. Generally, most vehicles must travel on a road or a water
    body, but there are a few exceptions.
    Vehicles have a variety of power sources, including:
        Human power (rowing a boat)
        Animal power (an animal pulling a cart)
        Sail/Wind
        Psionic
        Tech
        Fuel
    In order to move the vehicle, you must have the required power source.
    """

    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        # set several of the traits to match a building
        self.traits.mass.base = 1000
        self.traits.hp.base = 10000
        self.traits.val.base = 1000
        self.traits.cap.base = 5000
        self.db.powered_by = None
        self.db.travel_mode = None # i.e road, water, air

    ## TODO: Add functrions for mounting/driving the vehicle, dismounting, fuel
    ## or power checks, vehicle getting stuck, vehicle breaking
    ## TODO: Add functions for driving a vehicle that prevent you from going
    ## "off-road" if the vehcile must stay on a certain travel_mode


class Key(Item):
    """
    A special subclass of item that can lock or unlock other items.
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.db.key_for = [] # This should be populated with an ID for a
        # locakble object or an exit to (and potentially from) a room
        # NOTE:
        #       locks are handled on exits using a line like:
        #       <obj>.locks.add("traverse:holds(key_name)")


class Trap(Item):
    """
    A special kind of item that applies status effects, usually of a type that
    do damage or immobilize the person caught by the trap
    """
    def at_object_creation(self):
        "Only called at creation and forced update"
        super().at_object_creation()
        self.traits.mass.base = 100
        self.traits.hp.base = 1000
        self.traits.val.base = 100
        self.traits.cap.base = 50
        self.db.armed = False
        self.db.status_effects = {} # dict of status effects, dice_to_hit
        self.db.triggered_by = {} # dict of triggering actions
        self.talents.add(
            key='sneak',
            type='static',
            base=100,
            mod=0,
            name='Sneak',
            extra={'learn' : 0}
        )

    def apply_status_effect(self, trappee):
        """
        Applies a status effect to a person caught im the trap.
        """
        pass
