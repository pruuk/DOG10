# coding=utf-8
"""
Menus for editing room objects.
"""
from evennia.contrib.base_systems.building_menu import BuildingMenu
from evennia.utils import lazy_property
from world.handlers.traits import TraitHandler
from evennia.utils.logger import log_file

MAP_SYMBOLS = {
    'Crossroads' : ['|155╬|n','|255╬|n','|355╬|n','|455╬|n','|555╬|n'],
    'EW Road' : ['|155═|n', '|255═|n', '|355═|n', '|455═|n', '|555═|n'],
    'NS Road' : ['|155║|n', '|255║|n', '|355║|n', '|455║|n', '|555║|n'],
    'NW Road' : ['|155╗|n', '|255╗|n', '|355╗|n', '|455╗|n', '|555╗|n'],
    'SW Road' : ['|155╝|n', '|255╝|n', '|355╝|n', '|455╝|n', '|555╝|n'],
    'NE Road' : ['|155╔|n', '|255╔|n', '|355╔|n', '|455╔|n', '|555╔|n'],
    'SE Road' : ['|155╚|n', '|255╚|n', '|355╚|n', '|455╚|n', '|555╚|n'],
    'WT Road' : ['|155╣|n', '|255╣|n', '|355╣|n', '|455╣|n', '|555╣|n'],
    'ET Road' : ['|155╠|n', '|255╠|n', '|355╠|n', '|455╠|n', '|555╠|n'],
    'NT Road' : ['|155╩|n', '|255╩|n', '|355╩|n', '|455╩|n', '|555╩|n'],
    'ST Road' : ['|155╦|n', '|255╦|n', '|355╦|n', '|455╦|n', '|555╦|n'],
    'Plains' : ['|155■|n', '|255■|n', '|355■|n', '|455■|n', '|555■|n'],
    'Forest' : ['|043¡|n', '|143¡|n', '|243¡|n', '|343¡|n', '|443¡|n'],
    'Jungle' : ['|043▓|n', '|143▓|n', '|243▓|n', '|343▓|n', '|443▓|n'],
    'Mountains/Hills' : ['|110^|n', '|210^|n', '|310^|n', '|410^|n', '|510^|n'],
    'Desert/Badlands' : ['|110°|n', '|210°|n', '|310°|n', '|410°|n', '|510°|n'],
    'Taiga' : ['|155¶|n', '|255¶|n', '|355¶|n', '|455¶|n', '|555¶|n'],
    'Tundra' : ['|155≡|n', '|255≡|n', '|355≡|n', '|455≡|n', '|555≡|n'],
    'Swamp' : ['|040§|n', '|140§|n', '|240§|n', '|340§|n', '|440§|n'],
    'Savannah' : ['|120░|n', '|220░|n', '|320░|n', '|420░|n', '|520░|n'],
    'Shore' : ['|025▄|n', '|024▄|n', '|023▄|n', '|022▄|n', '|021▄|n',],
    'Water' : ['|001█|n', '|002█|n', '|003█|n', '|004█|n', '|005█|n',],
    'Fields' : ['|041▒|n', '|141▒|n', '|241▒|n', '|341▒|n', '|441▒|n',],
    'City' : ['|155©|n', '|255©|n', '|355©|n', '|455©|n', '|555©|n'],
    'Indoors' : ['|155:|n', '|255:|n', '|355:|n', '|455:|n', '|555:|n'],
    'Cave': ['|155Ç|n', '|255Ç|n', '|355Ç|n', '|455Ç|n', '|555Ç|n'],
}


class RoomSculptingMenu(BuildingMenu):

    """
    Building menu to edit a room.
    """

    @lazy_property
    def traits(self):
        """TraitHandler that manages room traits."""
        return TraitHandler(self)

    def init(self, room):
        self.room = room
        self.add_choice("|=zTitle|n", key="1", attr="key", glance="|y{obj.key}|n", text="""
                -------------------------------------------------------------------------------
                Editing the title of {{obj.key}}(#{{obj.id}})
                You can change the title simply by entering it.
                Use |y{back}|n to go back to the main menu.
                Current title: |c{{obj.key}}|n
        """.format(back="|n or |y".join(self.keys_go_back)))
        self.add_choice_edit("|=zDescription|n", "2")
        self.add_choice("|=zExits|n", "3", glance=glance_exits, text=text_exits,
            on_nomatch=nomatch_exits)
        self.add_choice("|=zInfo Attributes|n", "4", glance=glance_info_attrs,
            text=text_info, on_nomatch=nomatch_info)
        self.add_choice("|=zTraits|n", "5", glance=glance_traits,
            text=text_traits, on_nomatch=nomatch_traits)
        self.add_choice("|=zBiomes|n", "6", glance=glance_biomes,
            text=text_biomes, on_nomatch=nomatch_biomes)
        self.add_choice("|=zChoose Map Symbol (from a list)|n", "7",
            glance="\n  {obj.db.map_symbol}",
            text=text_map_symbol, on_nomatch=nomatch_map_symbol)
        self.add_choice("|=zUpdate the Room to Current Spec|n", "8",
            glance=glance_update, on_enter=update_on_enter)


# Menu functions
def glance_exits(room, caller):
    """Show the room exits."""
    if room.exits:
        glance = ""
        for exit in room.exits:
            glance += "\n  |y{exit}|n".format(exit=exit.key)
    else:
        glance += "\n  |gNo exit yet|n"
    # get adjacent rooms if this isn't the origin room (#2) and coords are not set to 0,0
    if not (room.traits.xcord.current == 0 and room.traits.ycord.current == 0) \
        or room.id == 2:
            adjacent_rooms = find_adjacent_room_ids(room, caller)
    else:
        adjacent_rooms = None
    missing_exits_to = []
    glance += "\n\n  |yAdjacent Rooms (by Coordinates):|n"
    if adjacent_rooms:
        for room_id, cardinal in adjacent_rooms:
            glance += f"\n    |yRoom Id: |Y{room_id} |yDirection: |Y{cardinal}"
        missing_exits_to = check_adjacent_rooms_for_missing_exits(room, adjacent_rooms)
    else:
        glance += "\n    |YNone|n"
    glance += "\n  |yList of potentially missing exits:|n"
    if missing_exits_to:
        for room_id, cardinal in missing_exits_to:
            glance += f"\n    |yRoom Id: |Y{room_id} |yDirection: |Y{cardinal}"
    else:
        glance += "\n    |YNone|n"

    return glance


def glance_info_attrs(room):
    """Show the info Attributes"""
    if room.db.info:
        glance = ""
        for info_attr, info_value in room.db.info.items():
            glance += f"\n  |y{info_attr}: |Y{info_value}|n"
        return glance
    return "\n No valid info attributes. Please update room to current base spec."


def glance_traits(room):
    """Show the Room's Traits"""
    glance = ""
    if room.traits:
        glance += f"\n  |yRoom Size (in Square Meters): |Y{room.traits.size.current}|n"
        glance += f"\n  |yRoom Elevation (in Meters Above Sea Level): |Y{room.traits.elev.current}|n"
        glance += f"\n  |yX Coordinate: |Y{room.traits.xcord.current}|n"
        glance += f"\n  |yY Coordinate: |Y{room.traits.ycord.current}|n"
        glance += f"\n  |yY Ruggedness of Terrain (Slope from 0 = flat to 1 = vertical): |Y{room.traits.rot.current}|n"
    else:
        glance += "No traits defined."
    return glance

def glance_biomes(room):
    """Show the room biomes"""
    glance = ""
    if room.biomes:
        for biome, data in room.biomes.all_dict.items():
            if data['base'] != 0:
                glance += f"\n|y  {biome}|n: |y{data['base']}"
    if len(glance) == 0:
        glance += "|y  None|n"
    return glance


def glance_update(room):
    """ Show the glance warning text for updating """
    glance = ""
    glance += "|y\n  Updating the object will overwrite all of the room's current values"
    glance += "\n  and update the room to have the standard set of properties that any"
    glance += "\n  brand new room will have.|n"
    glance += "\n  |YNOTE: Updating the room will execute the command and exit you from"
    glance += "\n  the sculpting menu.|n"
    return glance


def text_biomes(room):
    """Show the room biomes"""
    text = "\n  |YBiomes:|n"
    if room.biomes:
        for biome, data in room.biomes.all_dict.items():
            text += f"\n    |y{biome}|n: |y{data['base']}"
    text += "\n\n  |yNOTE: The value for biomes is a number between 0 and 1"
    text += "\n     Thus a value of 1 means the entire room is that biome."
    text += "\n     Please ensure all your biome values add up to 1.|n"

    text += "\n\n  |YTo change a biome value, enter <biome name> <value>"
    text += "\n  For example, forest 0.4"
    text += "\n  would make 40% of the room forest type."
    text += "\n\n type @ to return to the previous menu."
    return text


def text_exits(caller, room):
    """Show the room exits in the choice itself."""
    text = "-" * 79
    text += "\n\nRoom exits:"
    text += "\n Use tunnel or dig commands (outside these menus) to create new rooms."
    text += "\n To open an exit to "
    text += "\n Use @ to return to the previous menu."
    text += "\n To edit a specific exit use something like '@3 east'"
    text += "\n\nExisting exits:"
    if room.exits:
        for exit in room.exits:
            text += "\n  |y@3 {exit}|n".format(exit=exit.key)
            if exit.aliases.all():
                text += " (|y{aliases}|n)".format(aliases="|n, |y".join(
                        alias for alias in exit.aliases.all()))
            if exit.destination:
                text += " toward {destination}".format(destination=exit.get_display_name(caller))
    else:
        text += "\n\n |gNo exit has yet been defined.|n"

    # get adjcent rooms
    adjacent_rooms = find_adjacent_room_ids(room, caller)
    missing_exits_to = []
    text += "\n\n  |yAdjacent Rooms (by Coordinates):|n"
    if adjacent_rooms:
        for room_id, cardinal in adjacent_rooms:
            text += f"\n    |yRoom Id: |Y{room_id} |yDirection: |Y{cardinal}"
        missing_exits_to = check_adjacent_rooms_for_missing_exits(room, adjacent_rooms)
    else:
        text += "\n    |YNone|n"
    text += "\n  |yList of potentially missing exits:|n"
    if missing_exits_to:
        for room_id, cardinal in missing_exits_to:
            text += f"\n    |yRoom Id: |Y{room_id} |yDirection: |Y{cardinal}"
    else:
        text += "\n    |YNone|n"

    text += "\n  To open a new exit to and from an adjacent room, type: "
    text += "\n     |yconnect_to_<room id number>"

    return text


def text_info(caller,room):
    """ Show the room info attrs in the main menu """
    text = "-" * 79
    text += "\n\nRoom Attributes:"
    index_num = 0
    if room.db.info:
        for info_attr, info_value in room.db.info.items():
            index_num += 1
            text += f"\n {index_num}. |y{info_attr}: |Y{info_value}|n"
        text += "\n\n To edit an item, type in something like:"
        text += "\n 1. True"
        text += "\n This example will set the Non-Combat boolean to True"
    else:
        text += "\n\n |gNo room attributes have been defined.|n"
    text += "\n  Type |y@|n to return to the main menu."
    return text


def text_traits(caller, room):
    """ Show the traits info as a textual submenu"""
    text = "-" * 79
    text += "\n\nEditable Room Traits:"
    text += f"\n  1. |yRoom Size (in Square Meters): |Y{room.traits.size.current}|n"
    text += f"\n  2. |yRoom Elevation (in Meters Above Sea Level): |Y{room.traits.elev.current}|n"
    text += f"\n  3. |yX Coordinate: |Y{room.traits.xcord.current}|n"
    text += f"\n  4. |yY Coordinate: |Y{room.traits.ycord.current}|n"
    text += f"\n  5. |yY Ruggedness of Terrain (Slope from 0 = flat to 1 = vertical): |Y{room.traits.rot.current}|n"
    text += "\n\n  Note: Changing the size of a room will also change its carrying capacity."
    text += "\n\n  Example: 3. 1 will change the X Coordinate to 1"
    text += "\n  Type |y@|n to return to the main menu."
    return text


def text_map_symbol(caller, room):
    """ Show the Map Symbol Options """
    text = "-" * 79
    text += "\n\nPossible Map Symbols:"
    for biome, map_symbols in MAP_SYMBOLS.items():
        text += f"\n  |y{biome}|n : {str(map_symbols)}"
    text += "\n\n  |YNote: The biome should generally match the map symbol"
    text += "\n  The symbols are arranged in order by how they would appear"
    text += "\n  on the map if the room was lower or higher in elevation in"
    text += "\n  relation to the map viewer's location."
    text += "\n  |yType in <biome name> to select a symbol set Ex: Jungle"
    text += "\n  Type |y@|n to return to the main menu."
    return text


def nomatch_biomes(menu, caller, room, string):
    """
    The user types something into the submenu for biomes
    """
    if len(string) > 2:
        split_text = string.split()
        if len(split_text) == 2:
            biome_name = split_text[0]
            biome_val = float(split_text[1])
            caller.msg(f"Trying to set {biome_name} to {biome_val}")
            if biome_name in MAP_SYMBOLS.keys():
                room.biomes.road.base = biome_val
    return


def nomatch_map_symbol(menu, caller, room, string):
    """
    The user types in something for the map symbol
    """
    if len(string) > 2:
        caller.msg(f"You typed in {string}. Checking against dictionary of map symbols.")
        if string in MAP_SYMBOLS.keys():
            room.db.map_symbol = MAP_SYMBOLS[string]
            caller.msg(f"Map Symbol set to: {MAP_SYMBOLS[string]}")


def nomatch_traits(menu, caller, room, string):
    """
    The user types in something.
    """
    cmd_str = string[3:]
    if len(string) > 2:
        if string[:1] == '1':
            room.traits.size.base = int(cmd_str)
            room.traits.enc.base = room.traits.size.current ** 2
            caller.msg(f"Set Size to: {room.traits.size.current}")
        elif string[:1] == '2':
            room.traits.elev.base = int(cmd_str)
            caller.msg(f"Set Elevation to: {room.traits.elev.current}")
        elif string[:1] == '3':
            room.traits.xcord.base = int(cmd_str)
            caller.msg(f"Set X Coordinate to: {room.traits.xcord.current}")
        elif string[:1] == '4':
            room.traits.ycord.base = int(cmd_str)
            caller.msg(f"Set Y Coordinate to: {room.traits.ycord.current}")
        elif string[:1] == '5':
            room.traits.rot.base = float(cmd_str)
            caller.msg(f"Set Ruggedness of Terrain to: {room.traits.rot.current}")
        else:
            caller.msg("Unknown Command")
            return False
    return


def nomatch_info(menu, caller, room, string):
    """
    The user types in something.
    """
    cmd_str = string[3:]
    if len(string) > 0:
        if string[:1] == '1':
            caller.execute_cmd(f"set here/info['Non-Combat Room'] = {cmd_str}")
        elif string[:1] == '2':
            caller.execute_cmd(f"set here/info['Outdoor Room'] = {cmd_str}")
        elif string[:1] == '3':
            caller.execute_cmd(f"set here/info['Zone'] = {cmd_str}")
        else:
            caller.msg("Unknown Command")
            return False
    return


def nomatch_exits(menu, caller, room, string):
    """
    The user typed something in the list of exits.  Maybe an exit name?
    """
    # check first if we're trying to open exits to a new adjacent room
    log_file(f"Before 11 is: {string[:11]}", filename='room_build_debug.log')
    if string[:11] == 'connect_to_':
        cmd_string = string[11:]
        # get adjcent rooms
        adjacent_rooms = find_adjacent_room_ids(room, caller)
        missing_exits_to = []
        if adjacent_rooms:
            missing_exits_to = check_adjacent_rooms_for_missing_exits(room, adjacent_rooms)
            if missing_exits_to:
                for room_id, cardinal in missing_exits_to:
                    if str(room_id) == cmd_string:
                        direction_string = get_return_dir_string(cardinal)
                        caller.execute_cmd(f"open {direction_string} = #{room_id}")
                        caller.msg(f"Opening a new exit to: #{room_id}")
        return
    else:
        string = string[3:]
        exit = caller.search(string, candidates=room.exits)
        if exit is None:
            return

    # Open a sub-menu, using nested keys
    caller.msg("Editing: {}".format(exit.key))
    menu.open_submenu("commands.building.room_building.ExitBuildingMenu", exit, parent_keys=["3"])
    return False


def update_on_enter(caller):
    """
    The user can update the room to current base spec.
    """
    caller.execute_cmd("update here")
    return


def find_adjacent_room_ids(room, caller):
    """
    This func uses the temp variable nearby_rooms on the caller and compares
    the X,Y Coordinates of the rooms in the nearby room list to find rooms
    that are adjecent. This will be used with other functions to create linked
    exits between adjacent rooms if the builder chooses to do so.
    """
    log_file(f"Checking for adjacent rooms for: {room.id}", filename='room_build_debug.log')
    if room.ndb.nearby_rooms:
        adjacent_rooms = []
        for room_id in room.ndb.nearby_rooms:
            search_string = f"#{room_id}"
            adj_room_candidate = caller.search(search_string)
            if adj_room_candidate:
                if adj_room_candidate.traits.xcord.current == room.traits.xcord.current:
                    # matching X coordinate, check to north and south
                    if int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) + 1:
                        # X matches, Y is 1 room north of room we're editing
                        adjacent_rooms.append([adj_room_candidate.id, 'north'])
                    if int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) - 1:
                        # X matches, Y is 1 room south of room we're editing
                        adjacent_rooms.append([adj_room_candidate.id, 'south'])
                elif adj_room_candidate.traits.ycord.current == room.traits.ycord.current:
                    # matching Y coordinate, check to west and east
                    if int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) + 1:
                        # Y matches, X is 1 room east of room we're editing
                        adjacent_rooms.append([adj_room_candidate.id, 'east'])
                    if int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) - 1:
                        # Y matches, X is 1 room west of room we're editing
                        adjacent_rooms.append([adj_room_candidate.id, 'west'])
                elif int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) + 1  and \
                    int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) + 1:
                    adjacent_rooms.append([adj_room_candidate.id, 'northeast'])
                elif int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) + 1  and \
                    int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) - 1:
                    adjacent_rooms.append([adj_room_candidate.id, 'northwest'])
                elif int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) - 1  and \
                    int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) + 1:
                    adjacent_rooms.append([adj_room_candidate.id, 'southeast'])
                elif int(adj_room_candidate.traits.ycord.current) == int(room.traits.ycord.current) - 1  and \
                    int(adj_room_candidate.traits.xcord.current) == int(room.traits.xcord.current) - 1:
                    adjacent_rooms.append([adj_room_candidate.id, 'southwest'])
        log_file(f"List of adjacent rooms: {adjacent_rooms}", filename='room_build_debug.log' )
        return adjacent_rooms
    else:
        return None


def check_adjacent_rooms_for_missing_exits(room, adjacent_rooms):
    """
    Takes in the adjacent rooms list produced by the func above and checks to
    see if we have missing exit candidates. Returns those candidates.
    """
    # get exits
    exit_keys = []
    missing_exits_to = []
    if room.exits:
        log_file(f"Checking Exits: {room.exits}", filename='room_build_debug.log' )
        for exit in room.exits:
            exit_keys.append(exit.key)
            log_file(f"Exit Keys: {exit_keys}", filename='room_build_debug.log')
    for room_id, cardinal in adjacent_rooms:
        log_file(f"Checking if {room_id} that is {cardinal} of this room has an exit", filename='room_build_debug.log')
        if cardinal not in exit_keys:
            # we're missing an exit to the adjacent room
            missing_exits_to.append([room_id, cardinal])
    return missing_exits_to


def get_return_dir_string(cardinal):
    """ Gets the aliases for a cardinal direction and the return direction."""
    if cardinal in ['north', 'south', 'east', 'west', 'northwest', 'northeast', \
                    'southeast', 'southwest']:
        if cardinal == 'north':
            return 'north;n,south;s'
        if cardinal == 'south':
            return 'south;s,north;n'
        if cardinal == 'east':
            return 'east;e,west;w'
        if cardinal == 'west':
            return 'west;w,east;e'
        if cardinal == 'northwest':
            return 'northwest;nw,southeast;se'
        if cardinal == 'southeast':
            return 'southeast;se,northwest;nw'
        if cardinal == 'northeast':
            return 'northeast;ne,southwest;sw'
        if cardinal == 'southwest':
            return 'southwest;sw,northeast;ne'
    else:
        return None


class ExitBuildingMenu(BuildingMenu):
    """
    Building submenu to edit an exit.
    """

    def init(self, exit):
        self.add_choice("key", key="1", attr="key", glance="{obj.key}")
        self.add_choice_edit("description", "2")