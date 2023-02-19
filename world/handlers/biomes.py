# coding=utf-8
"""
Biomes Handler file.
This file will contain the functions and containers for handling room
biomes. Generally, the map symbol set for a room should match the primary
biome type of the room, except when the room has a major road running
through it or the room is indoors.
Biome types will affect climate/weather, but will also be affected by other
factors such as elevation, time of year, climate/weather, the actions of
mobile characters & NPCs, etc.
Biomes are for use in outdoor rooms. Indoor rooms will just have objects
and status effects.
"""


# map symbols for overhead mapping. This is here as a reference.
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
    'City' : ['|155©|n', '|255©|n', '|355©|n', '|455©|n', '|555©|n']
}


_BIOME_DATA = {
    # Outdoor Biomes
    'road': {
        'name': 'Road',
        'type': 'Outdoor',
        'desc': ("|mRoad|n is the biome that indicates there is a road "
                 "running through the room. Although the road may only take up "
                 "a small percentage of the actual land area in the room, it "
                 "may be prominenant enough to warrant setting the overhead "
                 "map symbol to be a road type. Roads can degrade to trail "
                 "if they remain unrepaired for long enough."),
        'vegetation_min': 0,
        'vegetation_max': 0.25,
        'climate': ['temperate'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {'condition' : 1, # 0-1, 1 is perfect condition
                  'quality': .75, # 0-1, 1 is the best quality road known
                  'width': 5, # road width in meters
                  'road_type': 'pavement_stones'}
    },
    'trail': {
        'name': 'Trail',
        'type': 'Outdoor',
        'desc': ("|mTrail|n is the biome that indicates there is a trail "
                 "running through the room. Although the trail may only take up "
                 "a small percentage of the actual land area in the room, it "
                 "may be prominenant enough to warrant setting the overhead "
                 "map symbol to be a road/trail type. Roads can degrade to trail"
                 "if they remain unrepaired for long enough and trails can "
                 "degrade to sonme other biome given enough time."),
        'vegetation_min': 0,
        'vegetation_max': 0.35,
        'climate': ['temperate'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {'condition' : 1, # 0-1, 1 is perfect condition
                  'quality': .75, # 0-1, 1 is the best quality trail known
                  'width': 2, # trail width in meters
                  'trail_type': 'compacted_earth'}
    },
    'plains': {
        'name': 'Plains',
        'type': 'Outdoor',
        'desc': ("|mPlains|n is a temperate grassland biome. The primary "
                 "vegetation type is grasses, but trees can be found in well "
                 "watered areas. Plains tend to be inhabited by herd animals, "
                 "small rodents, and some predators. Plains are often converted "
                 "into fields by human activity."),
        'vegetation_min': 0.1,
        'vegetation_max': 0.75,
        'climate': ['temperate'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'forest': {
        'name': 'Forest',
        'type': 'Outdoor',
        'desc': ("|mForest|n is a biome dominated by trees. The primary "
                 "vegetation type is trees, but other types can be found in "
                 "forest, usually underbrush and plants that prefer shade at "
                 "least some of the time. Forests are inhabited by many animals, "
                 "including some predators. Forests can be converted into fields "
                 "by human activity."),
        'vegetation_min': 0.35,
        'vegetation_max': 0.95,
        'climate': ['temperate'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'jungle': {
        'name': 'Jungle',
        'type': 'Outdoor',
        'desc': ("|mJungle|n is a biome dominated by trees. The primary "
                 "vegetation type is trees, but other types can be found in "
                 "jungle, usually underbrush and plants that prefer shade at "
                 "least some of the time. Jungle are inhabited by many animals, "
                 "including some predators. Jungle can be converted into fields "
                 "by human activity, but tends to grow back quickly."),
        'vegetation_min': 0.5,
        'vegetation_max': 0.95,
        'climate': ['tropical', 'subtropical'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'hills': {
        'name': 'Mountains & Hills',
        'type': 'Outdoor',
        'desc': ("|mMountains & Hills|n is a biome dominated by changes in "
                 "elevation. Climate can vary depending on elevation and "
                 "latitude. The primary vegetation type is trees at lower "
                 "elevation and middle latitudes, but other types can be found "
                 "in hills, Hills are inhabited by many animal types, "
                 "including some predators. Hills can be converted into fields "
                 "by human activity, but require a great deal of earth moving."),
        'vegetation_min': 0,
        'vegetation_max': 0.95,
        'climate': ['tropical', 'subtropical', 'temperate', 'alpine', 'subartic', 'artic'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'badlands': {
        'name': 'Badlands & Desert',
        'type': 'Outdoor',
        'desc': ("|mBadlands & Desert|n is a biome dominated by a lack of water. "
                 "Climate can vary depending on elevation. Vegetation type "
                 "varies a great deal depending on elevation and latitude. "
                 "Badlands can be converted into fields by human activity, but "
                 "require a great deal of irrigation."),
        'vegetation_min': 0,
        'vegetation_max': 0.15,
        'climate': ['arid', 'semiarid'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'tiaga': {
        'name': 'Tiaga',
        'type': 'Outdoor',
        'desc': ("|mTiaga|n is a biome found in far northern regions. It is "
                 "sometimes swampy, but tends to be dominated by conferious "
                 "trees. Tiaga is usually sandwiched between steppes (high "
                 "elevation desert) and tundra. Tiaga can be converted into "
                 "fields by human activity, but require a great deal of "
                 "draining, and tend to have short growing seasons and somewhat "
                 "poor soil."),
        'vegetation_min': 0.15,
        'vegetation_max': 0.95,
        'climate': ['subartic'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'tundra': {
        'name': 'Tundra',
        'type': 'Outdoor',
        'desc': ("|mTundra|n is a biome found in far northern regions. It is "
                 "sometimes swampy in summer, but hardens in cold months. Tundra "
                 "tends to have vegatation that is low to the ground. Animal "
                 "life is somewhat scarce. Tundra cannot be converted into "
                 "fields by human activity."),
        'vegetation_min': 0.05,
        'vegetation_max': 0.2,
        'climate': ['subartic', 'artic'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'swamp': {
        'name': 'Swamp',
        'type': 'Outdoor',
        'desc': ("|mSwamp|n is a biome found in temperate, subtropical, and "
                 "tropical regions. It is generally wet and heavily vegetated. "
                 "Swamps have a wide variety of animal and plant species. "
                 "Swamps can be converted into fields by human activity, but "
                 "require extensive draining and earthmoving."),
        'vegetation_min': 0.5,
        'vegetation_max': 0.95,
        'climate': ['temperate', 'subtropical', 'tropical'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'savannah': {
        'name': 'Savannah',
        'type': 'Outdoor',
        'desc': ("|mSavannah|n is a biome found in temperate, subtropical, and "
                 "tropical regions. Savannahs are generally dry and hot. "
                 "Savannahs have a wide variety of animal and plant species, but "
                 "are mostly grasslands with isolated trees and shrubs. "
                 "Savannahs can be converted into fields by human activity, but "
                 "require extensive irrigation in most cases."),
        'vegetation_min': 0.15,
        'vegetation_max': 0.35,
        'climate': ['subtropical', 'tropical'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'shore': {
        'name': 'Shore',
        'type': 'Outdoor',
        'desc': ("|mShoreh|n is a biome found next to significant bodies of "
                 "water (flowing or not). Shores can be rocky, sandy, heavily "
                 "vegetated, or some combo. Shores can be found in most climates. "
                 "Shores cannot be converted into fields by human activity."),
        'vegetation_min': 0.05,
        'vegetation_max': 0.85,
        'climate': ['tropical', 'subtropical', 'temperate', 'alpine', 'subartic', \
                    'artic', 'arid', 'semiarid'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'water': {
        'name': 'Water',
        'type': 'Outdoor',
        'desc': ("|mWaterh|n is a biome indicating a large body of water, "
                 "flowing or not. Water usually cannot be converted into fields "
                 "by human activity."),
        'vegetation_min': 0,
        'vegetation_max': 0.75,
        'climate': ['tropical', 'subtropical', 'temperate', 'alpine', 'subartic', \
                    'artic', 'arid', 'semiarid'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'fields': {
        'name': 'Fields',
        'type': 'Outdoor',
        'desc': ("|mFieldsh|n is a biome indicating a large amount of human "
                 "activity, curating and cultivating specific plant or animal "
                 "crops."),
        'vegetation_min': 0,
        'vegetation_max': 0.75,
        'climate': ['tropical', 'subtropical', 'temperate', 'alpine', 'subartic', \
                    'arid', 'semiarid'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    },
    'city': {
        'name': 'City',
        'type': 'Outdoor',
        'desc': ("|mCityh|n is a biome indicating a large amount of human "
                 "activity, usually with extensive built objects in it."),
        'vegetation_min': 0,
        'vegetation_max': 0.5,
        'climate': ['tropical', 'subtropical', 'temperate', 'alpine', 'subartic', \
                    'arid', 'semiarid', 'artic'],
        'biome_ratio': 0, # this should total to 1 across all biomes assocated to the room
        'extra': {}
    }
}


def apply_biomes(room):
    """
    Initializes a room with the full list of biomes.
    The biomes will have to be edited later on the individual rooms.
    """
    room.biomes.clear()
    for biome, data in _BIOME_DATA.items():
        room.biomes.add(
            key=biome,
            type='static',
            base=data['biome_ratio'],
            mod=0,
            name=data['name'],
            extra=data['extra']
        )


class BIOME(object):
    """Represents a Talent's display attributes for use in help files
    Args:
        name (str): display name for talent
        desc (str): description of talent
        climate (str): list of allowed climates
    """
    def __init__(self, name, desc, base):
        self.name = name
        self.desc = desc
        self.climate = climate
