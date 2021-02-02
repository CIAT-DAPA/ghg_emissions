###
## spanish | english
climate_options = [[
    'templado continental',
    'templado seco',
    'templado oceanico',
    'húmedo subtropical',
    'seco subtropical',
    'tropico húmedo',
    'tropico seco'
], ['temperate continental',
    'temperate dry',
    'temperate oceanic',
    'subtropical moist',
    'subtropical dry',
    'tropical moist',
    'tropical dry'
    ]]

soil_type = [[
    'suelo ligero (arenoso), bajo en mo',
    'suelo medio',
    'suelo pesado (arcilloso), alto en mo'
], [
    'Light soil (e.g. sandy), low SOC',
    'Medium soil',
    'Heavy soil (e.g. clay), high SOC'
]]

###
soil_texture = [[
    "media",
    "gruesa",
    "fina"
], ["medium",
    "coarse",
    "fine"
    ]]

### INFERENCIA POR SUELO

tillage_options = [[
    'cero labranza',
    'labranza convencional',
    'labranza reducida'
], ['no tillage',
    'conventional tillage',
    'reduced tillage'
    ]]

cover_crop_options = [[
    'cobertura vegetal',
    'sin cobertura vegetal'
], [
    'start adding',
    'no change'
]]

### land use change

luc_options = [[
    'bosque a pastura',
    'bosque a arable',
    'pastura a arable',
    'arable a pastura',
    'bosque a cacao'
], [
    'forest to grassland',
    'forest to arable',
    'grassland to arable',
    'arable to grassland',
    'forest to cocoa'
]]

### producer country

prod_country_options = [[
    'europa',
    'china',
    'otro'
], [
    'Europe',
    'China',
    'other'
]]

###### rice

rice_water_regime_options = [[
    "inundación continua",
    "inundación",
    "drenaje multiple",
    "drenaje simple",
    "secano, temporada húmeda",
    "secano, temporada seca",
    "desconocido"
], [
    "Continuous flooding",
    "Deepwater",
    "Multiple drainage",
    "Single drainage",
    "Rainfed, wet season",
    "Rainfed, dry season",
    "Unknown"
]]

##pre-water regime

rice_prewater_regime_options = [[
    "inundado",
    "drenaje largo",
    "drenaje corto",
    "dos drenajes",
    "desconocido"
], [
    "flooded",
    "long drainage",
    "short drainage",
    "two drainage",
    "unknown"
]]

specific_climate_rice_options = [[
    "trópicos calido arido y sermi arido",
    "trópicos cálido subhúmedo",
    "trópico húmedo cálido",
    "subtrópico cálido arido y semiarido con lluvias en verano",
    "subtrópico cálido subhumedo con lluvias en verano",
    "subtrópico cálido/frio subhúmedo con lluvias en verano"
],
    [
        "warm arid and semi arid tropics",
        "warm subhumid tropics",
        "warm humid tropics",
        "warm arid and semiarid subtropics with summer rainfall",
        "warm humid subtropcis with summer rainfall",
        "warm/cool humid subtropics with summer rainfall"
    ]]

###
world_climate_bouwman = [[
    "temperate continental",
    "temperate oceanic",
    "subtropical moist",
    "subtropical dry",
    "tropical moist",
    "tropical dry"
], [
    "temperate dry",
    "temperate moist",
    "temperate moist",
    "temperate dry",
    "tropical moist",
    "tropical dry"
]]

world_climate_sayre = {
    'temperate dry': [[6, 8],
                      ["Cool Temperate Dry", "Warm Temperate Dry"]],
    'subtropical moist': [[13],
                          ["Sub Tropical Moist"]],
    'subtropical dry': [[14],
                        ["Sub Tropical Dry"]],
    'tropical moist': [[18],
                       ["Tropical Moist"]],
    'tropical dry': [[16],
                     ["Tropical Dry"]]

    # 1: "Polar Moist", 2:"Polar Dry", 3:"Boreal Moist", 4:"Boreal Dry",
    # 5:"Cool Temperate Moist", 6:"Cool Temperate Dry", 7:"Warm Temperate Moist",
    # 8:"Warm Temperate Dry", 9:"Cool Temperate Desert",
    # 10:"Warm Temperate Desert", 11:"Boreal Desert", 12:"Polar Desert",
    # 13:"Sub Tropical Moist", 14:"Sub Tropical Dry", 15:"Sub Tropical Desert",
    # 16:"Tropical Dry", 17:"Tropical Desert", 18:"Tropical Moist"
}

world_climate_koppen = {
    'temperate continental': [[18, 26, 19, 27, 22, 23, 6],
                              ["Dfa", "Dwa", "Dfb", "Dwb", "Dsa", "Dsb", "BSk"]],
    'temperate oceanic': [[10, 11, 16, 17],
                          ["Cfb", "Cfc", "Cwb", "Cwc"]]
    #'other': [[1, 2, 3, 4, 5, 7, 8, 9, 12, 13, 14, 15, 20, 21, 24, 25, 28, 29, 30, 31, 32]]
}
