import pandas as pd
import numpy as np
import os
from scripts import general_functions as gf

pc_CO2 = 1
pc_CH4 = 34  ## IPCC 2013 5th Assessement Report WG1
pc_N2O = 265
pc_N2O_MOT = 298

N_to_N2O = 44 / 28

### FERTILISERS MANAGEMENT

limestone_factor = 0.12
urea_factor = 0.2

### factors
fertilizers_table = pd.read_excel(r'emission_factors/fertilizers_factors.xlsx')

fertilizers_factors = gf.subsetpandas_byvalues(fertilizers_table,
                                               'Factors for fertilizers',
                                               'Factors for inhibitors and Polymer-coated fertilizer', 1, addinitrow=3)

### RICE FACTORS

rice_table = pd.read_excel(r'emission_factors/rice_factors.xlsx')

rice_factors = gf.subsetpandas_byvalues(rice_table,
                                               'Empirical method factors',
                                               'IPCC  method factors', 1, addinitrow=1,)

rice_soilm_factors = gf.subsetpandas_byvalues(rice_table,
                                               'Management change_Rice based system' ,
                                               'Management change_Cover cropping', 1, addinitrow=1)

rice_covercrop_factors = gf.subsetpandas_byvalues(rice_table,
                                               'Management change_Cover cropping' ,
                                               'Factors - SOC change/baseline', 1, addinitrow=1)

rice_ofert_factors = gf.subsetpandas_byvalues(rice_table,
                                               'Factors - SOC change/baseline' ,
                                               'end_table', 1, addinitrow=2,delendrow = 0)


## INHIBITORS


inhibi_factors = gf.subsetpandas_byvalues(fertilizers_table,
                                          'Factors for N2O emission change with N inhibitor',
                                          'Factors for NO emission change with N inhibitor', 1, addinitrow=0)

inhibi_no_factors = gf.subsetpandas_byvalues(fertilizers_table,
                                             'Factors for NO emission change with N inhibitor',
                                             'end_table', 1, addinitrow=0)

### INDIRECT EMISSIONS BY FERTLISERS
inducedfertiliser_table = pd.read_excel(r'emission_factors/N2O_and NO_model_factors.xlsx')
inducedfertiliser_factors = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                                     'Stehfest and Bouwman 2006',
                                                     'Factors for NH3 model', 1, addinitrow=1)

nh3_factors_table = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                             'Factors for NH3 model',
                                             'Method of N application', 1, addinitrow=2, delendrow=-5)

method_appl_nh3_options = gf.subsetpandas_byvalues(nh3_factors_table,
                                                   'Method of N application',
                                                   'Method of N application', 0, addinitrow=-1, delendrow=-5)

constantN2O = inducedfertiliser_factors.loc[inducedfertiliser_factors.Variables == 'constant']['N2O'].values[0]
constantNO = inducedfertiliser_factors.loc[inducedfertiliser_factors.Variables == 'constant']['NO'].values[0]

N_application_rate_constant = inducedfertiliser_factors.loc[inducedfertiliser_factors.Variables ==
                                                            'N application rate per kg N ha-1']['N2O'].values[0]

NO_application_rate_constant = inducedfertiliser_factors.loc[inducedfertiliser_factors.Variables ==
                                                             'N application rate per kg N ha-1']['NO'].values[0]

### SOIL MANAGEMENT

### SOIL PROPERTIES

soil_ef_table = pd.read_excel(r'emission_factors/soil_factors.xlsx')
soil_properties = gf.subsetpandas_byvalues(soil_ef_table, 'soil properties', 'end_table', 1)

n2o_soc_options = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                           'SOC content (%)',
                                           'soil N content (%)', 1, addinitrow=-1)

n_soc_options = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                         'soil N content (%)',
                                         'Soil pH', 1, addinitrow=-1)

pH_n2o_options = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                          'Soil pH',
                                          'Soil texture', 1, addinitrow=-1)

pH_nh3_options = gf.subsetpandas_byvalues(nh3_factors_table,
                                          'Soil pH',
                                          'Climate', 0, addinitrow=-3)

texture_n2o_options = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                               'Soil texture',
                                               'Climate', 1, addinitrow=-1)

climate_options_table = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                                 'Climate',
                                                 'Crop type', 1, addinitrow=-1)

cropbouwman_n2o_options_table = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                                 'Crop type',
                                                 'Length of experiment', 1, addinitrow=-1)

climate_nh3_options = gf.subsetpandas_byvalues(nh3_factors_table,
                                               'Climate',
                                               'Crop type', 0, addinitrow=-3)

crop_factors_file = pd.read_excel(r'emission_factors/crop_factors.xlsx')
crop_factors = gf.subsetpandas_byvalues(crop_factors_file, "Factors for crops",
                                        "Factors for calculating residue amount", 1, 1, 4)

crop_nh3_options = gf.subsetpandas_byvalues(nh3_factors_table,
                                            'Crop type',
                                            'CEC', 0, addinitrow=-3)

lengthexperimet_factors = {
    'Per year (>300 days)': [1.991, 2.544],
    'Per year (<300 days)': [0, 0]
}

### TILLAGE FACTORS

tillage_factors = gf.subsetpandas_byvalues(soil_ef_table,
                                           "Tillage change_All (except rice)",
                                           "Input practice change_All (except rice)", 1)

### COVER CROP FACTORS

cover_cropping_factors = gf.subsetpandas_byvalues(soil_ef_table,
                                                  "Management change_Cover cropping",
                                                  "soil properties", 1)

### organic fertliser tecnologies soc

factors_soc_change = {
    'compost': [0, 0.00036, -0.00004, 0, 0.00049936, -0.00001762],
    'manure': [0, 0.00036, -0.00004, 0, 0.00049936, -0.00001762],
    'residue': [0, 0.00131, 0, 0, 0.00131, 0]
}

########### LUC
luc_table = pd.read_excel(r'emission_factors/luc_factors.xlsx')
luc_factors = gf.subsetpandas_byvalues(luc_table,
                                       'land use change (LUC)',
                                       'end_table',
                                       1)

luc_options = {
    'forest to grassland': [1],
    'forest to arable': [2],
    'grassland to arable': [4],
    'arable to grassland': [6],
    'forest to cocoa': [8]
}

######## burning residues

burned_CH4factor = 2.7
burned_N2Ofactor = 0.07

ramount_factors_file = pd.read_excel(r'emission_factors/crop_factors.xlsx')
ramount_factors = gf.subsetpandas_byvalues(ramount_factors_file,
                                           "Factors for calculating residue amount",
                                           "end_table", 1, addinitrow=3)

######## cec

cec_table = pd.read_excel(r'emission_factors/cec_factors.xlsx')
cec_factors = gf.subsetpandas_byvalues(cec_table,
                                       'Factors for CEC',
                                       'Factors for Limestone and Urea', 1, addinitrow=2)

cec_nh3_options = gf.subsetpandas_byvalues(nh3_factors_table,
                                           'CEC',
                                           'Method of N application', 0, addinitrow=-1, delendrow=1)

#### volatilization


volatilizationfactors = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                                 'Factor for N volatilization and leaching',
                                                 'end_table', 5, addinitrow=0)

#### LEACHING

leachingfactors = gf.subsetpandas_byvalues(inducedfertiliser_table,
                                          'N leaching',
                                            'end_table',3, addinitrow= 1)
