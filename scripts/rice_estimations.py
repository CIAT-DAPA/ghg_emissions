from scripts import emission_factors_mot as ef
from scripts import translations as tl
import numpy as np


def get_nh4_by_pH_content(pH_content):
    """ get NH4 by pH in Rice"""

    if pH_content % 1 == 0:
        pH_content = float(pH_content) + 0.01
    else:
        pH_content = float(pH_content)

    if float(pH_content) <= 4.5:
        ph_attribute = 'less than 4.5'
    elif float(pH_content) >= 8.0:
        ph_attribute = 'more than 8.0'

    else:
        a = np.round(pH_content)
        b = np.ceil(pH_content) - 0.5
        if a > b:
            ph_attribute = "{}-{}".format(b, a)
        else:
            ph_attribute = "{}-{}".format(a, b)

    if ph_attribute!="nan-nan":
        pH_nh4_content = ef.rice_factors.loc[ef.rice_factors.iloc[:, 0] == ph_attribute].iloc[:, 1].values[0]
    else:
        pH_nh4_content = 0
    return [pH_nh4_content]

def mitigation_by_cropadding(cover_input,climate_input):

    covercropfilter = ef.rice_covercrop_factors.Change.str.lower() == cover_input.lower()
    climatefilter = ef.rice_covercrop_factors.Climate.str.lower() == climate_input.lower()
    if climatefilter.sum() == 0:
        cl_eng_input = tl.world_climate_bouwman[1][tl.world_climate_bouwman[0].index(climate_input)]
        climatefilter = ef.rice_covercrop_factors.Climate.str.lower() == cl_eng_input.lower()

    filter_conditions = climatefilter & covercropfilter
    if (np.array(filter_conditions).sum() != 0):
        factor_change_20years = ef.rice_covercrop_factors.Factor.loc[filter_conditions].values[0]
    else:
        factor_change_20years = 1

    return factor_change_20years

def mitigation_by_tillage(tillage_input):
    """ get NH4 by pH in Rice"""

    to_tillagefilter = ef.rice_soilm_factors.iloc[:,2].str.lower() == tillage_input.lower()
    defaulttillage = ef.rice_soilm_factors.iloc[:,1].str.lower() == 'conventional tillage'

    filter_conditions = defaulttillage & to_tillagefilter
    factor_change_20years = 1
    if (np.array(filter_conditions).sum() != 0):
        factor_change_20years = ef.rice_soilm_factors.iloc[:,3].loc[
            filter_conditions].values[0]

    return (factor_change_20years)


def pre_water_regime_factor(pwclass, language):
    if language == "spanish":
        pwater_options = [i.lower() for i in tl.rice_prewater_regime_options[0]]
    else:
        pwater_options = [i.lower() for i in tl.rice_prewater_regime_options[1]]

    pwclass_enginput = "unknown"

    if pwclass.lower() in pwater_options:
        pwclass_enginput = tl.rice_prewater_regime_options[1][pwater_options.index(pwclass.lower())]

    pw_factor = ef.rice_factors.loc[ef.rice_factors.iloc[:, 3].str.lower() == pwclass_enginput].iloc[:, 4].values[0]

    return ([pw_factor,
             pwclass_enginput])


def water_regime_factor(wclass, language):
    if language == "spanish":
        water_options = [i.lower() for i in tl.rice_water_regime_options[0]]
    else:
        water_options = [i.lower() for i in tl.rice_water_regime_options[1]]

    wclass_enginput = "unknown"

    if wclass.lower() in water_options:
        wclass_enginput = tl.rice_water_regime_options[1][water_options.index(wclass.lower())]

    w_factor = ef.rice_factors.loc[ef.rice_factors.iloc[:, 6].str.lower() == wclass_enginput.lower()].iloc[:, 7].values[0]

    return ([w_factor,
             wclass_enginput])

def sp_climate_factor(cl_input, language):
    if language == "spanish":
        climate_options = [i.lower() for i in tl.specific_climate_rice_options[0]]
    else:
        climate_options = [i.lower() for i in tl.specific_climate_rice_options[1]]

    climate_enginput = "unknown"
    if cl_input.lower() in climate_options:
        climate_enginput = tl.specific_climate_rice_options[1][climate_options.index(cl_input.lower())]

    cl_factor = ef.rice_factors.loc[
                        ef.rice_factors.iloc[:, 9].str.lower() == climate_enginput.lower()].iloc[:, 10].values[0]


    return (cl_factor)

def factors_by_organic_fertilisers(organic_ferttype):

    subset = ef.rice_ofert_factors.loc[
        ef.rice_ofert_factors.Treatment.str.lower() == organic_ferttype.lower()]

    return subset

