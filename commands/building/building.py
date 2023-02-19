# coding=utf-8
"""
Building commands
This will be the set of commands that will open menus for those with permission
to edit in-game objects to do so. The menus will be a series of nested numbered
options that a builder can select until they get to a point where they are
editing a specific value on an object.
"""
from evennia.contrib.base_systems.building_menu import BuildingMenu
from commands.command import MuxCommand, Command
from commands.building.room_building import RoomSculptingMenu
from commands.building.item_building import ItemMakingMenu, ItemSculptingMenu
from evennia import create_object, default_cmds
from typeclasses.objects import Object
from typeclasses.items import Building
from evennia.utils.logger import log_file
from evennia import utils as utils
from world.handlers.biomes import apply_biomes
from django.conf import settings


# overwrite create and destroy commands
class CmdCreate( default_cmds.CmdCreate, MuxCommand):
    """
    create new objects
    Usage:
      create[/drop] <objname>[;alias;alias...][:typeclass], <objname>...
    switch:
       drop - automatically drop the new object into your current
              location (this is not echoed). This also sets the new
              object's home to the current location rather than to you.
    Creates one or more new objects. If typeclass is given, the object
    is created as a child of this typeclass. The typeclass script is
    assumed to be located under types/ and any further
    directory structure is given in Python notation. So if you have a
    correct typeclass 'RedButton' defined in
    types/examples/red_button.py, you could create a new
    object of this type like this:
       create/drop button;red : examples.red_button.RedButton
    Note: Create has been disabled. Please use 'form', which opens an item
    creation menu.
    """

    key = "create"
    switch_options = ("drop",)
    locks = "cmd:id(1)"
    help_category = "Building"

    # lockstring of newly created objects, for easy overloading.
    # Will be formatted with the {id} of the creating object.
    new_obj_lockstring = "control:id({id}) or perm(Admin);delete:id({id}) or perm(Admin)"

    def func(self):
        """
        Creates the object.
        """
        super().func()
        return


class CmdDestroy(MuxCommand, default_cmds.CmdDestroy):
    """
    permanently delete objects
    Usage:
       destroy[/switches] [obj, obj2, obj3, [dbref-dbref], ...]
    Switches:
       override - The destroy command will usually avoid accidentally
                  destroying account objects. This switch overrides this safety.
       force - destroy without confirmation.
    Examples:
       destroy house, roof, door, 44-78
       destroy 5-10, flower, 45
       destroy/force north
    Destroys one or many objects. If dbrefs are used, a range to delete can be
    given, e.g. 4-10. Also the end points will be deleted. This command
    displays a confirmation before destroying, to make sure of your choice.
    You can specify the /force switch to bypass this confirmation.
    NOTE: You cannot delete the room you're in or your own character object
    """
    key = "destroy"
    aliases = ["delete", "del"]
    switch_options = ("override", "force")
    locks = "cmd:perm(destroy) or perm(Builder)"
    help_category = "Building"

    confirm = True  # set to False to always bypass confirmation
    default_confirm = "yes"  # what to assume if just pressing enter (yes/no)

    def parse(self):
        """
        This method is called by the cmdhandler once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from self.func() (see below)
        The following variables are available for our use when entering this
        method (from the command definition, and assigned on the fly by the
        cmdhandler):
           self.key - the name of this command ('look')
           self.aliases - the aliases of this cmd ('l')
           self.permissions - permission string for this command
           self.help_category - overall category of command
           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following self.cmdstring.
           self.cmdset - the cmdset from which this command was picked. Not
                         often used (useful for commands like 'help' or to
                         list all available commands etc)
           self.obj - the object on which this command was defined. It is often
                         the same as self.caller.
        A MUX command has the following possible syntax:
          name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]
        The 'name[ with several words]' part is already dealt with by the
        cmdhandler at this point, and stored in self.cmdname (we don't use
        it here). The rest of the command is stored in self.args, which can
        start with the switch indicator /.
        This parser breaks self.args into its constituents and stores them in the
        following variables:
          self.switches = [list of /switches (without the /)]
          self.raw = This is the raw argument input, including switches
          self.args = This is re-defined to be everything *except* the switches
          self.lhs = Everything to the left of = (lhs:'left-hand side'). If
                     no = is found, this is identical to self.args.
          self.rhs: Everything to the right of = (rhs:'right-hand side').
                    If no '=' is found, this is None.
          self.lhslist - [self.lhs split into a list by comma]
          self.rhslist - [list of self.rhs split into a list by comma]
          self.arglist = [list of space-separated args (stripped, including '=' if it exists)]
          All args and list members are stripped of excess whitespace around the
          strings, but case is preserved.
        """
        super(MuxCommand, self).parse()

    def after_parse(self):
        """
        Run after parse() and before func()
        """
        if lhslist:
            for arg in lhslist:
                target = self.caller.search(self.arg)
                if target:
                    if target == self.caller:
                        self.caller.msg("You cannot delete yourself. Aborting")
                        return
                    if target == self.caller.location:
                        self.caller.msg("You cannot delete the room you're standing in. Aborting")
                        return


class CmdDig(default_cmds.CmdDig, MuxCommand):
    """
    build new rooms and connect them to the current location
    Usage:
      dig[/switches] <roomname>[;alias;alias...][:typeclass]
            [= <exit_to_there>[;alias][:typeclass]]
               [, <exit_to_here>[;alias][:typeclass]]
    Switches:
       tel or teleport - move yourself to the new room
       indoor - indoor room at destination
       outdoor - outdoor room at destination
       samezone - destination will be in same zone as current location
       samemap - destination will have the same map symbol as current location
    Examples:
       dig kitchen = north;n, south;s
       dig house:myrooms.MyHouseTypeclass
       dig sheer cliff;cliff;sheer = climb up, climb down
    This command is a convenient way to build rooms quickly; it creates the
    new room and you can optionally set up exits back and forth between your
    current room and the new one. You can add as many aliases as you
    like to the name of the room and the exits in question; an example
    would be 'north;no;n'.
    """

    key = "dig"
    switch_options = ("teleport","indoor","outdoor", "samezone", "samemap")
    locks = "cmd:perm(dig) or perm(Builder)"
    help_category = "Building"

    # lockstring of newly created rooms, for easy overloading.
    # Will be formatted with the {id} of the creating object.
    new_room_lockstring = (
        "control:id({id}) or perm(Admin); "
        "delete:id({id}) or perm(Admin); "
        "edit:id({id}) or perm(Admin)"
    )

    def func(self):
        """Do the digging. Inherits variables from ObjManipCommand.parse()"""

        caller = self.caller

        if not self.lhs:
            string = "Usage: dig[/switch] <roomname>[;alias;alias...]" "[:parent] [= <exit_there>"
            string += "[;alias;alias..][:parent]] "
            string += "[, <exit_back_here>[;alias;alias..][:parent]]"
            caller.msg(string)
            return

        room = self.lhs_objs[0]

        if not room["name"]:
            caller.msg("You must supply a new room name.")
            return
        location = caller.location

        # Create the new room
        typeclass = room["option"]
        if not typeclass or 'outdoor' in self.switches:
            typeclass = 'typeclasses.rooms.Room'
        if 'indoor' in self.switches:
            typeclass = 'typeclasses.rooms.IndoorRoom'

        # create room
        new_room = create_object(
            typeclass, room["name"], aliases=room["aliases"], report_to=caller
        )
        if 'samezone' in self.switches:
            new_room.db.info['zone'] = self.caller.location.db.info['zone']
        if 'samemap' in self.switches:
            new_room.db.map_symbol = self.caller.location.db.map_symbol
        lockstring = self.new_room_lockstring.format(id=caller.id)
        new_room.locks.add(lockstring)
        alias_string = ""
        if new_room.aliases.all():
            alias_string = " (%s)" % ", ".join(new_room.aliases.all())
        room_string = "Created room %s(%s)%s of type %s." % (
            new_room,
            new_room.dbref,
            alias_string,
            typeclass,
        )
        # set coordinates of connected room based upon current room
        if self.rhs_objs:
            to_exit = self.rhs_objs[0]
            if to_exit["name"] == "north" or to_exit["name"] =="n":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base + 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base
            if to_exit["name"] == "east" or to_exit["name"] =="e":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base + 1
            if to_exit["name"] == "south" or to_exit["name"] =="s":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base - 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base
            if to_exit["name"] == "west" or to_exit["name"] =="w":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base - 1
            if to_exit["name"] == "northwest" or to_exit["name"] =="nw":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base + 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base - 1
            if to_exit["name"] == "northeast" or to_exit["name"] =="ne":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base + 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base + 1
            if to_exit["name"] == "southwest" or to_exit["name"] =="sw":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base - 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base - 1
            if to_exit["name"] == "southeast" or to_exit["name"] =="se":
                new_room.traits.ycord.base = self.caller.location.traits.ycord.base - 1
                new_room.traits.xcord.base = self.caller.location.traits.xcord.base + 1


        # create exit to room

        exit_to_string = ""
        exit_back_string = ""

        if self.rhs_objs:
            to_exit = self.rhs_objs[0]
            if not to_exit["name"]:
                exit_to_string = "\nNo exit created to new room."
            elif not location:
                exit_to_string = "\nYou cannot create an exit from a None-location."
            else:
                # Build the exit to the new room from the current one
                typeclass = to_exit["option"]
                if not typeclass:
                    typeclass = 'typeclasses.exits.Exit'

                new_to_exit = create_object(
                    typeclass,
                    to_exit["name"],
                    location,
                    aliases=to_exit["aliases"],
                    locks=lockstring,
                    destination=new_room,
                    report_to=caller,
                )
                alias_string = ""
                if new_to_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_to_exit.aliases.all())
                exit_to_string = "\nCreated Exit from %s to %s: %s(%s)%s."
                exit_to_string = exit_to_string % (
                    location.name,
                    new_room.name,
                    new_to_exit,
                    new_to_exit.dbref,
                    alias_string,
                )

        # Create exit back from new room

        if len(self.rhs_objs) > 1:
            # Building the exit back to the current room
            back_exit = self.rhs_objs[1]
            if not back_exit["name"]:
                exit_back_string = "\nNo back exit created."
            elif not location:
                exit_back_string = "\nYou cannot create an exit back to a None-location."
            else:
                typeclass = back_exit["option"]
                if not typeclass:
                    typeclass = 'typeclasses.exits.Exit'
                new_back_exit = create_object(
                    typeclass,
                    back_exit["name"],
                    new_room,
                    aliases=back_exit["aliases"],
                    locks=lockstring,
                    destination=location,
                    report_to=caller,
                )
                alias_string = ""
                if new_back_exit.aliases.all():
                    alias_string = " (%s)" % ", ".join(new_back_exit.aliases.all())
                exit_back_string = "\nCreated Exit back from %s to %s: %s(%s)%s."
                exit_back_string = exit_back_string % (
                    new_room.name,
                    location.name,
                    new_back_exit,
                    new_back_exit.dbref,
                    alias_string,
                )
        caller.msg("%s%s%s" % (room_string, exit_to_string, exit_back_string))
        if new_room and "teleport" in self.switches:
            caller.move_to(new_room)


class CmdTunnel(default_cmds.CmdTunnel, MuxCommand):
    """
    create new rooms in cardinal directions only
    Usage:
      tunnel[/switch] <direction>[:typeclass] [= <roomname>[;alias;alias;...][:typeclass]]
    Switches:
      oneway - do not create an exit back to the current location
      tel - teleport to the newly created room
      indoor - indoor room at destination
      outdoor - outdoor room at destination
      samezone - destination will be in same zone as current location
      samemap - destination will have the same map symbol as current location
    Example:
      tunnel n
      tunnel n = house;mike's place;green building
    This is a simple way to build using pre-defined directions:
     |wn,ne,e,se,s,sw,w,nw|n (north, northeast etc)
     |wu,d|n (up and down)
     |wi,o|n (in and out)
    The full names (north, in, southwest, etc) will always be put as
    main name for the exit, using the abbreviation as an alias (so an
    exit will always be able to be used with both "north" as well as
    "n" for example). Opposite directions will automatically be
    created back from the new room unless the /oneway switch is given.
    For more flexibility and power in creating rooms, use dig.
    """

    key = "tunnel"
    aliases = ["tun"]
    switch_options = ("oneway", "tel", "indoor","outdoor", "samezone", "samemap")
    locks = "cmd: perm(tunnel) or perm(Builder)"
    help_category = "Building"

    # store the direction, full name and its opposite
    directions = {
        "n": ("north", "s"),
        "ne": ("northeast", "sw"),
        "e": ("east", "w"),
        "se": ("southeast", "nw"),
        "s": ("south", "n"),
        "sw": ("southwest", "ne"),
        "w": ("west", "e"),
        "nw": ("northwest", "se"),
        "u": ("up", "d"),
        "d": ("down", "u"),
        "i": ("in", "o"),
        "o": ("out", "i"),
    }

    def func(self):
        """Implements the tunnel command"""

        if not self.args or not self.lhs:
            string = (
                "Usage: tunnel[/switch] <direction>[:typeclass] [= <roomname>"
                "[;alias;alias;...][:typeclass]]"
            )
            self.caller.msg(string)
            return

        # If we get a typeclass, we need to get just the exitname
        exitshort = self.lhs.split(":")[0]

        if exitshort in self.caller.location.exits:
            self.caller.msg("There is already an exit in that direction. Try a different one.")
            return

        if exitshort not in self.directions:
            string = "tunnel can only understand the following directions: %s." % ",".join(
                sorted(self.directions.keys())
            )
            string += "\n(use dig for more freedom)"
            self.caller.msg(string)
            return

        # retrieve all input and parse it
        exitname, backshort = self.directions[exitshort]
        backname = self.directions[backshort][0]

        # if we recieved a typeclass for the exit, add it to the alias(short name)
        if ":" in self.lhs:
            # limit to only the first : character
            exit_typeclass = ":" + self.lhs.split(":", 1)[-1]
            # exitshort and backshort are the last part of the exit strings,
            # so we add our typeclass argument after
            exitshort += exit_typeclass
            backshort += exit_typeclass

        roomname = "Some place"
        if self.rhs:
            roomname = self.rhs  # this may include aliases; that's fine.

        telswitch = ""
        if "tel" in self.switches:
            telswitch = "/teleport"
        backstring = ""
        if "oneway" not in self.switches:
            backstring = ", %s;%s" % (backname, backshort)
        more_switches = ""
        if 'indoor' in self.switches:
            more_switches += "/indoor"
        if 'outdoor' in self.switches:
            more_switches += "/outdoor"
        # default will be to pass in same zone and map symbol
        more_switches += "/samezone"
        more_switches += "/samemap"

        # build the string we will use to call dig
        digstring = "dig%s%s %s = %s;%s%s" % (telswitch, more_switches, roomname, exitname, exitshort, backstring)
        self.execute_cmd(digstring)



class SculptCmd(Command):
    """
    Sculpting command.
    Usage:
        @sculpt [object]
    Opens a building menu to edit the specified object. This menu allows
    a builder to edit specific information about this object.
    Examples:
        @sculpt here
        @sculpt <character name>
        @sculpt #142
    NOTE: Please be careful editing your own character object. You can cause
          issues with your character or the game. With great powers...
    """
    key = '@sculpt'
    locks = 'cmd:id(1) or perm(Builders)'
    help_category = 'Building'

    def func(self):
        if not self.args.strip():
            self.msg("|rYou should provide an argument to this function: the object to edit.|n")
            return

        obj = self.caller.search(self.args.strip(), global_search=True)
        if not obj:
            return
        if utils.inherits_from(obj, 'typeclasses.rooms.Room'):
            Menu = RoomSculptingMenu
        elif utils.inherits_from(obj, 'typeclasses.items.Item'):
            Menu = ItemSculptingMenu
        else:
            self.msg("|rThe object {} cannot be edited.|n".format(obj.get_display_name(self.caller)))
            return


        menu = Menu(self.caller, obj)
        menu.open()


class FormItemCmd(Command):
    """
    Forming Command.
    Usage:
        @form
    Opens a building menu to create item objects of various types. This menu
    will only allow you to create a base item of a given type with a name you
    have chosen. To edit that item, exit the forming menu and use the sculpt
    command on the item.
    """
    key = '@form'
    locks = 'cmd:id(1) or perm(Builders)'
    help_category = 'Building'

    def func(self):
        Menu = ItemMakingMenu
        menu = Menu(self.caller, self.caller.location)
        menu.open()



class CoordinatesWormCmd(Command):
    """
    Command to update room coordinates.
    NOTE: This command is dangerous! It will update the coordinates of every
          room that is connected to this one by cardinal directions, and will
          do so based upon the coordinates in the room you are standing! Do not
          run this command unless you are sure you want to do so! This will also
          cause all sorts of havoc if your zone is not self-consistent from a
          cardinal direction standpoint.
    Usage:
        coordworm [room]
    Examples:
        coordworm here
        coordworm #2
    """
    key='@coordworm'
    locks = 'cmd:id(1) or perm(Admins)'
    help_category = 'Building'

    def func(self):
        if not self.args.strip():
            self.msg("|rYou should provide an argument to this function: the object to edit.|n")
            return
        room = self.caller.search(self.args.strip(), global_search=True)
        if room and utils.inherits_from(room, 'typeclasses.rooms.Room'):
            worm = create_object('commands.building.building.CoordinateWorm',
                                 key='worm',
                                 location=room)
            coords_reset = len(worm.has_mapped_room_ids)
            self.msg(f"{coords_reset} rooms have been updated with fresh coordinates.")
            worm.delete()
        else:
            self.msg("Searched room not found. provide a valid room for the worm to map")


class CoordinateWorm(Object):
    """
    A worm that travels through a zone and sets the coordinates of the rooms.
    Called by the 'coordworm' command.
    """

    def at_object_creation(self):
        self.zone = self.location.db.info['zone']
        self.outdoors = self.location.db.info['outdoor room']
        self.has_mapped = {}
        self.has_mapped_room_ids = []
        self.curX = self.location.traits.xcord.current
        self.curY = self.location.traits.ycord.current
        self.explore_map(self.location)


    def explore_map(self, room):
        """
        Explores the map via exits.
        """
        self.set_room_coordinates(room)
        for exit in room.exits:
            if exit.name not in ("north", "east", "west", "south", "northeast", \
                                 "northwest", "southeast", "southwest"):
                # we only map in the cardinal directions. Mapping up/down would be
                # an interesting learning project for someone who wanted to try it.
                continue
            if exit.destination.id in self.has_mapped_room_ids:
                # we've been to the destination already, skip ahead.
                continue

            self.update_pos(room, exit.name.lower())
            self.explore_map(exit.destination)


    def set_room_coordinates(self, room):
        """
        Sets the X and Y Coordinate traits for the room to match CurX and CurY
        """
        if room == self.location:
            self.has_mapped[room] = [self.curX, self.curY]
            self.has_mapped_room_ids.append(room.id)
        else:
            self.has_mapped[room] = [self.curX, self.curY]
            self.has_mapped_room_ids.append(room.id)
            room.traits.xcord.base = self.curX
            room.traits.ycord.base = self.curY
            room.db.info['zone'] = self.zone
            room.db.info['outdoor room'] = self.outdoors


    def update_pos(self, room, exit_name):
        # this ensures the pointer variables always
        # stays up to date to where the worm is currently at.
        self.curX, self.curY = \
           self.has_mapped[room][0], self.has_mapped[room][1]

        # now we have to actually move the pointer
        # variables depending on which 'exit' it found
        if exit_name == 'east':
            self.curX += 1
        elif exit_name == 'west':
            self.curX -= 1
        elif exit_name == 'north':
            self.curY += 1
        elif exit_name == 'south':
            self.curY -= 1
        elif exit_name == 'northeast':
            self.curX += 1
            self.curY += 1
        elif exit_name == 'southeast':
            self.curX += 1
            self.curY -= 1
        elif exit_name == 'northwest':
            self.curX -= 1
            self.curY += 1
        elif exit_name == 'southwest':
            self.curX -= 1
            self.curY -= 1


class CreateBuildingCmd(Command):
    """
    This command creates a Building Item. When the building is created, this
    should in turn create and entry room inside the building object (which is
    in turn inside the caller's current location) and the exits between the
    new entryway room and the caller's current location.
    Usage:
        @createbuilding <building's name>
    Examples:
        @createbuilding A Large Stone Inn
    """
    key = '@createbuilding'
    locks = 'cmd:id(1) or perm(Builders)'
    help_category = 'Building'

    def func(self):
        if not self.args.strip():
            self.msg("|rYou should provide a name for the building!|n")
            return
        outdoor_room = self.caller.location.id
        building = create_object('typeclasses.items.Building',
                key=self.args.strip(),
                location=self.caller.location,
                home=self.caller.location)
        self.caller.execute_cmd(f"open enter building;enter,exit building;exit = #{building.db.entryway.id}")
        self.caller.msg("You create a building")


class CreateTownCmd(Command):
    """
    This command creates a Town Item. When the town is created, this
    should in turn create and entrance room inside the town object (which is
    in turn inside the caller's current location) and the exits between the
    new entrance room and the caller's current location.
    Usage:
        @createtown <town's name>
    Examples:
        @createtown Sheriff Beehan's Hamlet
    """
    key = '@createtown'
    locks = 'cmd:id(1) or perm(Builders)'
    help_category = 'Building'

    def func(self):
        if not self.args.strip():
            self.msg("|rYou should provide a name for the town!|n")
            return
        outdoor_room = self.caller.location.id
        town = create_object('typeclasses.items.Town',
                key=self.args.strip(),
                location=self.caller.location,
                home=self.caller.location)
        self.caller.execute_cmd(f"open enter {town.key};enter town;enter,exit {town.key};exit town;exit = #{town.db.entryway.id}")
        self.caller.msg(f"You create a town named {town.key}")