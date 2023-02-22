# coding=utf-8
"""
Map handler
This file contains an object class that 'worms' through the local environment
and displayus an overhead map dynamically to the players. The worm will be
determining the overhead map based upon a number of factors, including:
- The biome of the rooms
- The relative elevation of the rooms
- The weather (affects visibility)
- Status effects on the character, such as blindness
- The time of day
- Indoor vs. outdoor
- Has the character been in the room recently?
- Is the character flying?
All rooms in DOG have a coordinate trait. Outdoor rooms have a self-consistent
set of coordinates that apply globally. Indoor rooms have coordinates that are
self consistent within the local zone.
The room the character is currently occupying will have the '@' symbol in it.
Rooms that are visible from the character's current perspective, but are of an
unknown type will have a '.' symbol for outdoor rooms and '[.]' for indoor
rooms.
Color is used to establish the relative elevation of a room the character can
perceive in relation to where they are standing.
"""
from evennia import create_object
from evennia import DefaultObject
from evennia.utils.logger import log_file
from statistics import median
from evennia import EvForm, EvTable
import random

# Base map info we're going to need to map a normal room
BASE_MAP_GRID = """\
█████████████████████
██████████·██████████
████████·····████████
████████·····████████
██████·········██████
██████·········██████
████·············████
████·············████
██·················██
██·················██
█·········@·········█
██·················██
██·················██
████·············████
████·············████
██████·········██████
██████·········██████
████████·····████████
████████·····████████
██████████·██████████
█████████████████████
"""

MAPPABLE_ROOM_COORDS = \
[[10,10],[8,10],[6,10],[4,10], [2,10], [0,10], [12,10], [14,10], [16,10], \
[18,10],[20,10], [10,8],[10,6],[10,4],[10,2],[10,0],[10,12],[10,14],[10,16], \
[10,18],[10,20],[8,2],[12,2],[6,4],[8,4],[12,4],[14,4],[4,6],[6,6],[8,6],[12,6], \
[14,6],[16,6],[2,8],[4,8],[6,8],[8,8],[12,8],[14,8],[16,8],[18,8], [8,18], \
[12,18],[6,16],[8,16],[12,16],[14,16],[4,14],[6,14],[8,14],[12,14], \
[14,14],[16,14],[2,12],[4,12],[6,12],[8,12],[12,12],[14,12],[16,12],[18,12]]

# the symbol is identified with a key "sector_type" on the
# Room. Keys None and "you" must always exist.
# TODO: Expand the symbols dictionary to include nested dicts for all of the
# factors listed above
SYMBOLS = { None : ' . ', # unknown room or connection type
            'CHAR_INDOOR' : '|505@|n', # the room we're in, if we're indoors
            'CHAR_OUTDOOR' : '|500@|n', # the room we're in, if we're indoors
            'CROSSROADS': '╬',
            'SECT_INSIDE': '.',
            'ENEMY_COMBATANT': '◙',
            'NON_COMBATANT_OBSERVER': '○'}

# base map info we'll need for the combat maps
LARGE_COMBAT_MAP_GRID = """\
█████████████████████
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█·········@·········█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█████████████████████
"""

MAPPABLE_LARGE_COMBAT_ROOM_COORDS = \
[[10,10], [8,10], [6,10], [4,10], [2,10], [0,10], [12,10], [14,10], [16,10], [18,10], [20,10], \
[10,8], [8,8], [6,8], [4,8], [2,8], [0,8], [12,8], [14,8], [16,8], [18,8], [20,8], \
[10,6], [8,6], [6,6], [4,6], [2,6], [0,6], [12,6], [14,6], [16,6], [18,6], [20,6], \
[10,4], [8,4], [6,4], [4,4], [2,4], [0,4], [12,4], [14,4], [16,4], [18,4], [20,4], \
[10,2], [8,2], [6,2], [4,2], [2,2], [0,2], [12,2], [14,2], [16,2], [18,2], [20,2], \
[10,12], [8,12], [6,12], [4,12], [2,12], [0,12], [12,12], [14,12], [16,12], [18,12], [20,12], \
[10,14], [8,14], [6,14], [4,14], [2,14], [0,14], [12,14], [14,14], [16,14], [18,14], [20,14], \
[10,16], [8,16], [6,16], [4,16], [2,16], [0,16], [12,16], [14,16], [16,16], [18,16], [20,16], \
[10,18], [8,18], [6,18], [4,18], [2,18], [0,18], [12,18], [14,18], [16,18], [18,18], [20,18], \
[10,20], [8,20], [6,20], [4,20], [2,20], [0,20], [12,20], [14,20], [16,20], [18,20], [20,20]]

MEDIUM_COMBAT_MAP_GRID = """\
█████████████████████
█████████████████████
█████████████████████
█████████████████████
████·············████
████·············████
████·············████
████·············████
████·············████
████·············████
████······@······████
████·············████
████·············████
████·············████
████·············████
████·············████
████·············████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
"""

MAPPABLE_MEDIUM_COMBAT_ROOM_COORDS = \
[[10,10], [8,10], [6,10], [4,10], [12,10], [14,10], [16,10], \
[10,8], [8,8], [6,8], [4,8], [12,8], [14,8], [16,8], \
[10,6], [8,6], [6,6], [4,6], [12,6], [14,6], [16,6], \
[10,4], [8,4], [6,4], [4,4], [12,4], [14,4], [16,4], \
[10,12], [8,12], [6,12], [4,12], [12,12], [14,12], [16,12], \
[10,14], [8,14], [6,14], [4,14], [12,14], [14,14], [16,14], \
[10,16], [8,16], [6,16], [4,16], [12,16], [14,16], [16,16]]

SMALL_COMBAT_MAP_GRID = """\
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
████████·····████████
████████·····████████
████████··@··████████
████████·····████████
████████·····████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
█████████████████████
"""

MAPPABLE_SMALL_COMBAT_ROOM_COORDS = \
[[10,10], [8,10], [12,10], \
[10,8], [8,8], [12,8], \
[10,12], [8,12], [12,12]]


class Map(object):
    """
    Creates a map object that contains functions for mapping the area around the
    observer and displaying the visible rooms and exits nearby.
    
    This class should be used for regular overhead map displays. Use the subclass
    CombatMap for overhead maps during combat.

    """
    def __init__(self, caller, max_width=21, max_length=21):
        log_file("Starting __init__ func", filename='map_debug.log')
        self.caller = caller
        # check if the caller is in combat. If they are, we want to provide a combat map
        # if not, we'll display a regular overhead map
        self.in_combat_check()
        self.max_width = max_width
        self.max_length = max_length
        self.worm_has_mapped = {}
        self.worm_has_mapped_room_ids = []
        self.curX = None
        self.curY = None

        # we actually have to store the grid into a variable
        self.grid = self.create_grid()
        #
        self.draw_room_on_map(caller.location,
                             ((min(max_width, max_length) -1 ) / 2))
        self.caller.ndb.nearby_rooms = self.worm_has_mapped_room_ids
        
        # for when we're in combat
        

    def update_pos(self, room, exit_name):
        # this ensures the pointer variables always
        # stays up to date to where the worm is currently at.
        self.curX, self.curY = \
           self.worm_has_mapped[room][0], self.worm_has_mapped[room][1]

        # now we have to actually move the pointer
        # variables depending on which 'exit' it found
        ## NOTE: The X and Y are the opposite of how you would think of the map
        ## coordinates because we're referencing indexes within a list, not an
        ## X Y on the map
        if exit_name == 'east':
            self.curY += 2
        elif exit_name == 'west':
            self.curY -= 2
        elif exit_name == 'north':
            self.curX -= 2
        elif exit_name == 'south':
            self.curX += 2
        elif exit_name == 'northeast':
            self.curX -= 2
            self.curY += 2
        elif exit_name == 'southeast':
            self.curX += 2
            self.curY += 2
        elif exit_name == 'northwest':
            self.curX -= 2
            self.curY -= 2
        elif exit_name == 'southwest':
            self.curX += 2
            self.curY -= 2

    def draw_room_on_map(self, room, max_distance):
        self.draw(room)

        if max_distance == 0:
            return

        for exit in room.exits:
            if exit.name not in ("north", "east", "west", "south", "northeast", \
                                 "northwest", "southeast", "southwest"):
                # we only map in the cardinal directions. Mapping up/down would be
                # an interesting learning project for someone who wanted to try it.
                continue
            if self.has_drawn(exit.destination):
                # we've been to the destination already, skip ahead.
                continue

            self.update_pos(room, exit.name.lower())
            self.draw_room_on_map(exit.destination, max_distance - 1)


    def draw(self, room):
        # draw initial caller location on map first!
        if room == self.caller.location:
            self.start_loc_on_grid()
            self.worm_has_mapped[room] = [self.curX, self.curY]
            self.worm_has_mapped_room_ids.append(self.caller.location.id)
        else:
            # map all other rooms
            self.worm_has_mapped[room] = [self.curX, self.curY]
            # this will use the sector_type Attribute or None if not set.
            if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                for exit in room.exits:
                    if exit.name == 'east':
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('horizontal', self.curX, self.curY + 1)
                    elif exit.name == 'west':
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('horizontal', self.curX, self.curY - 1)
                    elif exit.name == 'north':
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('vertical', self.curX - 1, self.curY)
                    elif exit.name == 'south':
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('vertical', self.curX + 1, self.curY)
                    elif exit.name == "northeast":
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('nesw', (self.curX - 1), (self.curY + 1))
                    elif exit.name == "southwest":
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('nesw', (self.curX + 1), (self.curY - 1))
                    elif exit.name == "northwest":
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('nwse', (self.curX - 1), (self.curY - 1))
                    elif exit.name == "southeast":
                        if [self.curX, self.curY] in MAPPABLE_ROOM_COORDS:
                            self.draw_exit('nwse', (self.curX + 1), (self.curY + 1))

                if room.db.map_symbol:
                    log_file(f"Draw... Checking X: {self.curX}, Y: {self.curY}", filename='map_debug.log')
                    self.worm_has_mapped_room_ids.append(room.id)

                    if len(room.db.map_symbol) == 1:
                        self.grid[self.curX][self.curY] = room.db.map_symbol
                    else:
                        self.grid[self.curX][self.curY] = room.db.map_symbol[self.get_elev_index(room)]
                else:
                    if not room.db.info['outdoor room']:
                        # this is an indoor room. Check to see if we have exits up or down
                        if 'up' in room.exits and 'down' in room.exits:
                            self.grid[self.curX][self.curY] = '|w±|n'
                        elif 'up' in room.exits:
                            self.grid[self.curX][self.curY] = '|w+|n'
                        elif 'down' in room.exits:
                            self.grid[self.curX][self.curY] = '|w-|n'
                        else:
                            self.grid[self.curX][self.curY] = '|W:|n'
                    self.grid[self.curX][self.curY] = SYMBOLS[room.db.sector_type]


    def get_elev_index(self, room):
        """
        Returns an elevation index for the room in relation to the character's
        current location. If the room is lower in elevation than the character's
        current location, a map symbol lower in the index will be chosen. This
        will have the effect of showing a color gradient on the map with
        elevations relative to the observer.
        """
        elevation_diff = room.traits.elev.current -self.caller_location.traits.elev.current
        if elevation_diff < -125:
            return 0
        elif -125 <= elevation_diff < -25:
            return 1
        elif -25 <= elevation_diff <= 25:
            return 2
        elif 25 <= elevation_diff < 125:
            return 3
        elif elevation_diff > 125:
            return 4


    def draw_exit(self, type, ExitX, ExitY):
        if 0 < ExitX < self.max_width and 0 < ExitY < self.max_length:
            # draw in the exits
            if type == 'vertical':
                self.grid[ExitX][ExitY] = '|'
            elif type == 'horizontal':
                self.grid[ExitX][ExitY] = '─'
            elif type == 'nesw':
                self.grid[ExitX][ExitY] = '/'
            elif type == 'nwse':
                self.grid[ExitX][ExitY] = '\\'
            else:
                log_file("Unknown exit type", filename='map_debug.log')


    def median(self, num):
        list_of_slots = sorted(range(0, num))
        return median(list_of_slots)


    def start_loc_on_grid(self):
        x = self.median(self.max_width)
        y = self.median(self.max_length)
        # x and y are floats by default, can't index lists with float types
        x, y = int(x), int(y)

        if self.caller_location.db.info['outdoor room']:
            self.grid[x][y] = SYMBOLS['CHAR_OUTDOOR']
        else:
            self.grid[x][y] = SYMBOLS['CHAR_INDOOR']
        self.curX, self.curY = x, y # updating worms current location


    def has_drawn(self, room):
        return True if room in self.worm_has_mapped.keys() else False


    def create_grid(self):
        # pull in base map grid and split it so the individual positions
        # can be called by index number
        board = self.map_grid.split('\n')
        index = 0
        for line in board:
        	line = list(line)
        	board[index] = line
        	index += 1

        return board


    def show_map(self):
        map_string = ""
        for row in self.grid:
            map_string += " ".join(row)
            map_string += "\n"

        return map_string
    
    
    def in_combat_check(self):
        """
        Check to see if the caller is in combat. If they are, we're going to want to generate
        a completely different map than if the caller is not in combat, in which case we'll
        generate a map displaying nearby rooms that are connected.
        """
         # Determine if the observer is in combat or not. If they are, we're going to
        # want to use a combat map instead of the base map grid
        if self.caller.ndb.combat_handler and self.caller.db.info['in combat']:
            # both of these should be true if the caller is in combat
            # determine room size
            if self.caller.location.traits.size.current >= 2500:
                # room is large or larger 50m squared plus
                self.map_grid = LARGE_COMBAT_MAP_GRID
                self.mappable_coords = MAPPABLE_LARGE_COMBAT_ROOM_COORDS
            elif self.caller.location.traits.size.current >= 225:
                # room is medium or larger 15m squared plus
                self.map_grid = MEDIUM_COMBAT_MAP_GRID
                self.mappable_coords = MAPPABLE_MEDIUM_COMBAT_ROOM_COORDS
            else:
                # room is small or of an undefined size
                self.map_grid = SMALL_COMBAT_MAP_GRID
                self.mappable_coords = MAPPABLE_SMALL_COMBAT_ROOM_COORDS
            # since the caller is in combat, we don't want to use room locations
            # we're going to want to give room sub-sections instead
            # We'll loop through the mappable locations and create a grid of
            # sections. Some will be randomly accessible, and some will not
            # to start, this will be truly random, but later, will be affected
            # by the room's biomes (forests would have fewer accessible rooms
            # than a plains room, for example). For now, we'll make 95% of them
            # usable subsections
            self.mappable_coords = random.sample(self.mappable_coords, int(len(self.mappable_coords) * .95))
            log_file(f"Mappable coords for combat room that are accessible: {self.mappable_coords}", filename="map_debug.log")
            # now that we have a the mappable coordinates, we'll go through and assign sub-sections to the grid
            # and "exits" between the accessible sections
            self.start_loc_on_grid = random.choice(self.mappable_coords)
            
            
                    
        
        else:
            # caller is not in combat. They should be getting a normal basemap grid
            self.map_grid = BASE_MAP_GRID
            self.mappable_coords = MAPPABLE_ROOM_COORDS
            self.caller_location = self.caller.location
        
        
            
# code I played around with to get the exits in the room below
MAPPABLE_LARGE_COMBAT_ROOM_COORDS = \
[[10,10], [8,10], [6,10], [4,10], [2,10], [12,10], [14,10], [16,10], [18,10], \
[10,8], [8,8], [6,8], [4,8], [2,8], [12,8], [14,8], [16,8], [18,8], \
[10,6], [8,6], [6,6], [4,6], [2,6], [12,6], [14,6], [16,6], [18,6],  \
[10,4], [8,4], [6,4], [4,4], [2,4], [12,4], [14,4], [16,4], [18,4],  \
[10,2], [8,2], [6,2], [4,2], [2,2], [12,2], [14,2], [16,2], [18,2],  \
[10,12], [8,12], [6,12], [4,12], [2,12], [12,12], [14,12], [16,12], [18,12], \
[10,14], [8,14], [6,14], [4,14], [2,14], [12,14], [14,14], [16,14], [18,14], \
[10,16], [8,16], [6,16], [4,16], [2,16], [12,16], [14,16], [16,16], [18,16], \
[10,18], [8,18], [6,18], [4,18], [2,18], [12,18], [14,18], [16,18], [18,18]]

LARGE_COMBAT_MAP_GRID = """\
█████████████████████
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█·········@·········█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█···················█
█████████████████████
"""

sampled_mappable = random.sample(MAPPABLE_LARGE_COMBAT_ROOM_COORDS, int(len(MAPPABLE_LARGE_COMBAT_ROOM_COORDS)*.85))

print(sampled_mappable)
exit_coords = {}

for coord in sampled_mappable:
    if [coord[0], coord[1] - 2] in sampled_mappable:
        exit_coords[coord[0], coord[1] - 1] = '|'
    if [coord[0], coord[1] + 2] in sampled_mappable:
        exit_coords[coord[0], coord[1] + 1] = '|'
    if [coord[0] + 2, coord[1]] in sampled_mappable:
        exit_coords[coord[0] + 1, coord[1]] = '─'
    if [coord[0] - 2, coord[1]] in sampled_mappable:
        exit_coords[coord[0] - 1, coord[1]] = '─'
        
print(exit_coords)

board = LARGE_COMBAT_MAP_GRID.split('\n')
print(board)


new_board = []
for index, row in enumerate(board):
    row = list(row)
    for coord in sampled_mappable:
        if index == coord[1] and coord != [10,10]:
            row[coord[0]] = 'X'
    for coord, map_icon in exit_coords.items():
        if index == coord[1]:
            row[coord[0]] = map_icon

    row = "".join(row)
    #print(index, row)
    new_board.append(row)

            
print(new_board)         