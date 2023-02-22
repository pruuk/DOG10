# coding=utf-8
"""
This file contains the functions to create combat maps consisting of a number
of room subsections (we're using a room subclass for these). 

The code here is
borrowed heavily from Evennia contribs mapbuilder contributed by Cloudkeeper
in 2016. See:
https://github.com/evennia/evennia/blob/main/evennia/contrib/grid/mapbuilder/mapbuilder.py
for the original contrib.

Build a combat map from a 2D ASCII map. I will only be building maps using the version with
exits. I'm going to represent the rooms using standard symbols rather than individual room
icon types. I'll build a different function for regular rooms.



"""
from evennia import create_object
from typeclasses.rooms import CombatRoomsection
from typeclasses import rooms, exits
from random import randint
import random
from evennia.utils.logger import log_file
from django.conf import settings
from evennia.utils import utils

SMALL_COMBAT_MAP = '''
* * * * *

* X-X-X *
  | | |
* X-O-X *
  | | |
* X-X-X *

* * * * *
'''

MEDIUM_COMBAT_MAP = '''
* * * * * * *

* X-X-X-X-X *
  | | | | |
* X-X-X-X-X *
  | | | | |
* X-X-O-X-X *
  | | | | |
* X-X-X-X-X *
  | | | | |
* X-X-X-X-X *

* * * * * * *
'''

LARGE_COMBAT_MAP = '''
* * * * * * * * *

* X-X-X-X-X-X-X *
  | | | | | | |
* X-X-X-X-X-X-X *
  | | | | | | |
* X-X-X-X-X-X-X *
  | | | | | | |
* X-X-X-O-X-X-X *
  | | | | | | |
* X-X-X-X-X-X-X *
  | | | | | | |
* X-X-X-X-X-X-X *
  | | | | | | |
* X-X-X-X-X-X-X *

* * * * * * * * *
'''

# Include your trigger characters and build functions in a legend dict.
LEGEND = {
    ("X", "O"): build_room_subsection_for_combat,
    ("|"): build_verticle_exit,
    ("-"): build_horizontal_exit,
}

def build_room_subsection_for_combat(x, y, parent, combat_handler **kwargs):
    """
    Builds a room subsection for the purposes of determining
    where players are on the battlefield and displaying the combat map.

    Args:
        x (int): X coordinate of the room subsection
        y (int): Y coordinate of the room subsection
        parent (Room Object): the parent room the subsections are a part of
    """
    
    # If on anything other than the first iteration - Do nothing.
    if kwargs["iteration"] > 0:
        return None
    
    room_section = create_object(rooms.CombatRoomsection, key=f"section of {parent.key} at {str(x)}, {str(y)}"
                                    )
    room_section.db.desc= f"Battlefield room subsection of {parent.name}."
    # add the room objects to the dictionary for the handler
    # move the room subsection into the parent room (all objects are containers)
    room_section.move_to(parent, quiet=True)
    if combat_handler.db.battlefield_room_section_dict:
        combat_handler.db.battlefield_room_section_dict[str(x), str{y}] = room_section, None
    else:
        combat_handler.db.battlefield_room_section_dict = {}
        combat_handler.db.battlefield_room_section_dict[str(x), str{y}] = room_section, None
    
    # TODO: Apply coordinates to the battlefield sections with the center being 0,0
    
    log_file(f"Created combat room section: {room_section.key}", filename='map_debug.log')
    
    return room_section

def build_vertical_exit(x, y, ** kwargs):
    """
    
    Creates two exits between room subsections to allow travel
    between the sections during combat.

    Args:
        x (int): Y coordinate of the exit
        y (int): Y coordinate of the exit
    """
    # If on the first iteration - Do nothing.
    if kwargs["iteration"] == 0:
        return
    
    north_room_section = kwargs["room_section_dict"][(x, y - 1)]
    south_room_section = kwargs["room_section_dict"][(x, y + 1)]
    
    # create exits in the rooms
    create_object(
        exits.Exit, key="south", aliases=["s"], location=north_room_section, destination=south_room_section
    )
    create_object(
        exits.Exit, key="north", aliases=["n"], location=south_room_section, destination=north_room_section
    )
    log_file(f"Created combat room section exits between: {north_room_section.key} & {south_room_section.key}", \
                filename='map_debug.log')
    

def build_horizontal_exit(x, y, ** kwargs):
    """
    
    Creates two exits between room subsections to allow travel
    between the sections during combat.

    Args:
        x (int): Y coordinate of the exit
        y (int): Y coordinate of the exit
    """
    # If on the first iteration - Do nothing.
    if kwargs["iteration"] == 0:
        return
    
    west_room_section = kwargs["room_section_dict"][(x - 1, y)]
    east_room_section = kwargs["room_section_dict"][(x + 1, y)]
    
    # create exits in the rooms
    create_object(
        exits.Exit, key="east", aliases=["e"], location=west_room_section, destination=east_room_section
    )
    create_object(
        exits.Exit, key="west", aliases=["w"], location=east_room_section, destination=west_room_section
    )
    log_file(f"Created combat room section exits between: {west_room_section.key} & {east_room_section.key}", \
                filename='map_debug.log')


# helper function for readability
def _map_to_list(game_map):
    """
    Splits multi line map string into list of rows.
    Args:
        game_map (str): An ASCII map
    Returns:
        list (list): The map split into rows
    """
    return game_map.split("\n")

def build_battlefield_map(combat_handler, parent_room, battlefield_map, iteralions=1, build_exists=True):
    """
    
    Receives the fetched map and legend vars provided by the combat handler

    Args:
        combat_handler (script): The ID for the combat handler controlling combat in the parent room
        parent_room (room object): The parent room in which the combat is being carried out. This function
                                    creates subsections of that room that are used by combatants to move
                                    around in during combat.
        battlefield_map (str): ASCII map string representing the battlefield
        iteralions (int, optional): The number of iteration passes. Defaults to 1.
        build_exists (bool, optional): Create exits between rooms (or not). Defaults to True.
        
        
     Notes:
        The battlefield map
        is iterated over character by character, comparing it to the trigger
        characters in the legend var and executing the build instructions on
        finding a match. The map is iterated over according to the `iterations`
        value and exits are optionally generated between adjacent rooms according
        to the `build_exits` value.
    """
    
    # Split map string to list of rows and create reference list.
    log_file(f"Creating battlefield map for: {battlefield_map}", \
                filename='map_debug.log')
    battlefield_map= _map_to_list(battlefield_map)
    
    # Create a reference dictionary which be passed to build functions and
    # will store obj returned by build functions so objs can be referenced.
    room_section_dict = {}
    
    log_file("Iterating through map...", filename='map_debug.log')
    for iteration in range(iteralions):
        for y in range(len(battlefield_map)):
            for x in range(len(battlefield_map[y])):
                for key in legend:
                    # obs - we must use == for strings
                    if battlefield_map[y][x] == key:
                        room_section = legend[key](
                            x, y, iteration=iteration, room_section_dict=room_section_dict, \
                                combat_handler=combat_handler, parent_room=parent_room
                        )
                        if iteration == 0:
                            room_section_dict[(x, y)] = room_section
                            
    if build_exists:
        # Creating exits. Assumes single room section object in dict entry
        log_file("Connecting room subsections with exits", \
                filename='map_debug.log')
        for loc_key, location in room_section_dict.items():
            x = loc_key[0]
            y = loc_key[1]

            # north
             if (x, y - 1) in room_section_dict:
                if room_section_dict[(x, y - 1)]:
                    create_object(
                        exits.Exit,
                        key="north",
                        aliases=["n"],
                        location=location,
                        destination=room_section_dict[(x, y - 1)],
                    )
            # east
            if (x + 1, y) in room_section_dict:
                if room_section_dict[(x + 1, y)]:
                    create_object(
                        exits.Exit,
                        key="east",
                        aliases=["e"],
                        location=location,
                        destination=room_section_dict[(x + 1, y)],
                    )

            # south
            if (x, y + 1) in room_section_dict:
                if room_section_dict[(x, y + 1)]:
                    create_object(
                        exits.Exit,
                        key="south",
                        aliases=["s"],
                        location=location,
                        destination=room_section_dict[(x, y + 1)],
                    )

            # west
            if (x - 1, y) in room_section_dict:
                if room_section_dict[(x - 1, y)]:
                    create_object(
                        exits.Exit,
                        key="west",
                        aliases=["w"],
                        location=location,
                        destination=room_section_dict[(x - 1, y)],
                    )        
        
    log_file("Map created!", \
                filename='map_debug.log')                

def call_map_funcs_and_build_battlefield_map(combat_handler, parent_room, battlefield_map, map_size='Small'):
    """
    
    Replaces original command in map builder. This function will be called by the combat handler
    to create the battlefield map

    Args:
        combat_handler (_type_): _description_
        parent_room (_type_): _description_
        battlefield_map (_type_): _description_
        map_size (_type_): _description_
        iteralions (int, optional): _description_. Defaults to 1.
        build_exists (bool, optional): _description_. Defaults to True.
    """
    
    # set up map & legend variables
    # TODO: augment this for situations where we might want to send in a custom map
    if map_size == 'Large':
        battlefield_map = LARGE_COMBAT_MAP
    elif map_size == 'Medium':
        battlefield_map = MEDIUM_COMBAT_MAP
    elif map_size -- 'Small':
        battlefield_map = SMALL_COMBAT_MAP
    else:
        log_file(f"Custom map inputted by combat handler", filename='map_debug.log')
    legend = LEGEND
    
    iterations= 2
    build_exists= False
    
    # pass map & legend to the battlefield map builder function
    build_battlefield_map(combat_handler, parent_room, battlefield_map, iteralions, build_exists)