import numpy as np
import pandas as pd
from scripts import emission_factors_mot as ef
from scripts import translations as tl


def calculate_indiremissions_fertiliser_production(fertiliser, ammount_kg_ha,
                                                   country, emission_factors,
                                                   column_name, language="spanish"):
    """Gauging the emissions due to production, considering the country
       in which the fertiliser was fabricated.
       Currently, there are three options, europe, china, and other
    """

    if language == "spanish":
        country = tl.prod_country_options[1][tl.prod_country_options[0].index(country.lower())]
    if country not in ['Europe', 'China', 'other']:
        country = 'other'
    else:
        country = country.capitalize()

    if fertiliser in emission_factors[column_name].str.lower().values:
        fert_emissions_factors = emission_factors.loc[emission_factors[column_name].str.lower() == fertiliser]

        emissions = ammount_kg_ha / fert_emissions_factors['Product'] * fert_emissions_factors[country]
    else:
        emissions = 0

    return emissions.values[0]


def calculate_n_amount_applied(fertiliser, amount_kg_ha,
                               emission_factors, column_name, table_nutrient='N'):
    """function that calculates the total amount of nitrogen given a single product"""

    if fertiliser in emission_factors[column_name].str.lower().values:

        fert_emissions_factors = emission_factors.loc[emission_factors[column_name].str.lower() == fertiliser]
        emissions = amount_kg_ha / fert_emissions_factors['Product'] * fert_emissions_factors[table_nutrient]

    else:
        emissions = 0
    return emissions.values[0]


def nh3_by_bouwman_reference(fert, emission_factors_table, col_name):
    """Estimating the NH3 volatilization emission for each fertiliser using Bouwman index"""

    nh3_value = emission_factors_table.loc[
        emission_factors_table[col_name].str.lower() == fert.lower()]["Bouwman's estimate for NH3+"].values[0]
    if np.isnan(nh3_value):
        nh3_value = 0

    return nh3_value


def application_method(fert, emission_factors_table, col_name):
    """Estimating the NH3 volatilization emission for each fertiliser using Bouwman index
    https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2000GB001389"""
    am = emission_factors_table.loc[emission_factors_table[col_name].str.lower() == fert.lower()]["application_mehod"].values[0]

    if am != am:
        am = 'broadcast'

    return am


def calculate_multiple_fertiliser_emissions(fertiliser_list,
                                            emission_factors_table,
                                            fun_name='emissions_production',
                                            col_name='fertiliser_sp',
                                            language="spanish"):
    """function that runs through a fertiliser list and applied different functions for each product.
        * calculate the N amount available (n_amount_applied)
        * get bowman index (bouwman_estimates)
        * calculate indirect emissions by production (emissions_production)
        * stimate indirect emissions by application method (application_method)
    """

    cummulative_products = []

    for ind in fertiliser_list:
        fert = fertiliser_list[ind][len(fertiliser_list[ind])-1]

        if fun_name == 'emissions_production':
            cummulative_products.append(
                calculate_indiremissions_fertiliser_production(fert,  # fertiliser
                                                               fertiliser_list[ind][0],  # amount
                                                               fertiliser_list[ind][2],  # country
                                                               emission_factors_table,
                                                               col_name, language))
        elif fun_name == 'n_amount_applied':

            cummulative_products.append(
                calculate_n_amount_applied(fert,  # fertiliser
                                           fertiliser_list[ind][0],  # amount
                                           emission_factors_table,
                                           col_name))

        elif fun_name == 'bouwman_index':
            cummulative_products.append(
                nh3_by_bouwman_reference(fert,  # fertiliser
                                         emission_factors_table,
                                         col_name))
        elif fun_name == 'application_method':
            cummulative_products.append(
                application_method(fert,  # fertiliser
                                   emission_factors_table,
                                   col_name))

        elif fun_name == 'rice_factors':
            cummulative_products.append(
                emissions_factors_by_rice(fert,  # fertiliser
                                          fertiliser_list[ind][0],  # amount
                                          emission_factors_table))

    return cummulative_products


def emissions_factors_by_rice(org_fert, fert_amount, fertiliser_factors, language="spanish"):
    """get emission factors by orgnaic applications in rice"""
    if language == "spanish":
        column_name = "fertiliser_sp"
    else:
        column_name = "fertiliser_eng"

    if org_fert.lower() in fertiliser_factors[column_name].str.lower().values:

        factor = fertiliser_factors.loc[fertiliser_factors[column_name].str.lower() ==
                                        org_fert.lower()]
        factor = factor["rice_emission_factor"].values[0]
    else:
        factor = 0
    return [factor, fert_amount/1000]


def induced_emissions_by_inhibitor(inhibitor, n_ammount, inhibitor_factors, column_pos=0):
    """get N2O/No inhibitor factors for each single product"""

    inhibi_n2oproduct = inhibitor_factors.loc[inhibitor_factors.iloc[:, column_pos].str.lower() ==
                                              inhibitor.lower()]

    return n_ammount * inhibi_n2oproduct['Upland'].values[0]


def calculate_inhibitor_release_multiple(listoffertilisers, fert_factors_table,
                                         inhibitor_factors_table, fert_type='synthetic'):
    """gget N2O/NO inhibitor factors for multiple products among
    which are synthetic and organic origin."""

    if fert_type == 'organic':
        inhibitors = ['No inhibitors' for i in range(len(listoffertilisers))]
    elif fert_type == 'synthetic':
        inhibitors = [listoffertilisers[i][1] for i in listoffertilisers]

    fert_n_ammounts = calculate_multiple_fertiliser_emissions(listoffertilisers,
                                                              fert_factors_table,
                                                              'n_amount_applied')

    inducedbyinhibi = []
    for i in range(len(listoffertilisers)):
        inducedbyinhibi.append(induced_emissions_by_inhibitor(inhibitors[i],
                                                              fert_n_ammounts[i],
                                                              inhibitor_factors_table))

    return inducedbyinhibi


def cumulative_socemissions_for_20years(years_usingtec, factor_20years, soil_c_stock):
    if years_usingtec < 20:
        Cumulative_considering_20_years_org_fert = (-1 * soil_c_stock * (factor_20years - 1)) * (44 / 12)
        annual_change_org_fert = Cumulative_considering_20_years_org_fert / 20
    else:
        Cumulative_considering_20_years_org_fert = 0
        annual_change_org_fert = 0

    return [annual_change_org_fert,
            Cumulative_considering_20_years_org_fert]


def cumulative_organic_fertilizer_for20years(org_fert_amount_kg_ha,
                                             soil_c_stock,
                                             org_fert_option='compost',
                                             years_adding_org_fert=20):
    # org_fert_option = ef.organic_fertilizer_options[org_fert_incorporated]
    org_fert_amount = org_fert_amount_kg_ha / 1000

    if org_fert_amount > 0:
        intercept = ef.factors_soc_change[org_fert_option][0]
        amount = ef.factors_soc_change[org_fert_option][1]
        duration = ef.factors_soc_change[org_fert_option][2]

        anual_factor = 1 + (intercept + amount * org_fert_amount + duration * 20)
    else:
        anual_factor = 1

    cum20years_factor = 1 + (anual_factor - 1) * 20

    return (cumulative_socemissions_for_20years(years_adding_org_fert, cum20years_factor, soil_c_stock))


def get_organic_specific_amount(organic_fert_dict,
                                org_ferttype="compost"):
    """calculate sum for a specific type of fertiliser"""

    fert_amount = []
    years_using_tec = []

    for i in organic_fert_dict.keys():
        if (organic_fert_dict[i][2] == org_ferttype):
            fert_amount.append(organic_fert_dict[i][0])
            years_using_tec.append(organic_fert_dict[i][1])

    return ([np.array(fert_amount).sum(),
             np.array(years_using_tec).mean()])


def assign_fertilizer_products(fertilisers, language= "spanish"):
    """ defining a new table for events that were reported with only N, P, K values"""

    newtable = pd.DataFrame.from_dict({'fertliser_product': [], 'amount_kg_ha': [],'inhibitor':[],'production_country': []})

    if language == "spanish":
        fertiliser_names = ['urea', 'super fosfato', 'cloruro de potasio']
    else:
        fertiliser_names = ['urea', 'super phosphate', 'muriate of potash / potassium Chloride']

    newtable.fertliser_product = fertiliser_names
    newtable.inhibitor = ['no inhibitors', 'no inhibitors', 'no inhibitors']
    newtable.amount_kg_ha = [fertilisers.N.values[0] , fertilisers.P.values[0], fertilisers.K.values[0]]

    newtable.production_country = fertilisers.production_country.shape[0]*fertilisers.production_country.values[0]


    return newtable




