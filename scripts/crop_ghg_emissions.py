import numpy as np
import pandas as pd
import math

from scripts import soil_management as sme
from scripts import fertiliser_practices as fp

from scripts import emission_factors_mot as ef
from scripts import translations as tl
from scripts import fertiliser_practices as fp
from scripts import fertiliser_functions as ff
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


class ghg_emissions:
    """Get soil emissions factors and properties for gauging ghg.


                   Parameters
                   ----------

                   input_list_files : list
                           Table

                   soil_emissions table : str



                   Attributes
                   ----------
                   soil_properties : list
                           List of soil properties that contain following values texture, soc, n content, pH and bulk density

                   soil_emissions table : str
            """

    def calculate_emissions_for_a_single_event(self, event_id):
        """Gauge ghg emissions for a single event"""
        print("calculating emissions for {}".format(event_id))
        subset_generalinfo = self._general_info.loc[self._general_info['id_event'] == event_id]
        subset_input_fertilisers_table = self._input_fertilisers_table.loc[
            self._input_fertilisers_table['id_event'] == event_id]

        fertiliser_data = fp.fertiliser_management(subset_input_fertilisers_table)

        soil_emissions = sme.soil_management_emissions(subset_generalinfo)

        ###

        compost_soc_change = ff.cumulative_organic_fertilizer_for20years(
            fertiliser_data._compost_total_amount[0],
            soil_emissions.soil_c_stock,
            'compost',
            fertiliser_data._compost_total_amount[1])

        manure_soc_change = ff.cumulative_organic_fertilizer_for20years(
            fertiliser_data._manure_total_amount[0],
            soil_emissions.soil_c_stock,
            'manure',
            fertiliser_data._manure_total_amount[1])

        residue_soc_change = ff.cumulative_organic_fertilizer_for20years(
            fertiliser_data._residue_total_amount[0],
            soil_emissions.soil_c_stock,
            'residue',
            fertiliser_data._residue_total_amount[1])

        ####SOIL MANAGEMENT

        soil_management_soc_CO2eq_kg_ha = np.array(
            [soil_emissions.tillage_soc_change[0],
             soil_emissions.cover_crop_soc_change[0],
             compost_soc_change[0],
             manure_soc_change[0],
             residue_soc_change[0]]).min()

        #### FERTILISERS PRODUCTION
        fertiliser_production_CO2eq_kg_ha = fertiliser_data.em_fert_production_CO2eq_kg_ha
        #### LUC
        luc_kg_co2 = soil_emissions.luc_effect_on_soil
        ### BURNING
        total_burning_kg_CO2eq = soil_emissions.burning_residues()
        ### BACKGROUND NH3 NO AND N2O EMISSIONS
        total_N2O_total_flux_kgCO2ha = calculate_n2o_ghg_from_soil_fertilizers(soil_emissions, fertiliser_data)
        total_NO_total_flux_kgCO2ha = calculate_no_ghg_from_soil_fertilizers(soil_emissions, fertiliser_data)
        total_NH3_total_flux_kgCO2ha = emissions_by_volatilization(soil_emissions, fertiliser_data)
        total_N_leaching_kgCO2ha = emissions_by_leaching(soil_emissions, fertiliser_data)

        fertiliser_induced_field_emissions_co2 = (np.array(
            fertiliser_data.emissions_by_urea_application()).sum() +
                                                  np.array(
                                                      fertiliser_data.caco3_emissions_by_limestone_application()).sum())

        #### SOIL MINING
        soil_mining_ghg_emission_kg_co2 = calculate_co2eq_by_soilmining(soil_emissions, fertiliser_data)

        fertiliser_induced_field_emissions_n2o = np.array([
            total_N2O_total_flux_kgCO2ha,
            total_NO_total_flux_kgCO2ha,
            total_NH3_total_flux_kgCO2ha,
            total_N_leaching_kgCO2ha
        ]).sum()

        ### LUC

        if np.array(luc_kg_co2).size > 1:
            luc_kg_co2_year = luc_kg_co2[0]
        else:
            luc_kg_co2_year = luc_kg_co2

        retults = pd.DataFrame({
            'id_event': [event_id],
            'municipality': subset_generalinfo.municipality.values[0],
            'Fertiliser production': [np.round(fertiliser_production_CO2eq_kg_ha, 2)],
            'Fertlises induced field emissions': [np.round(fertiliser_induced_field_emissions_n2o +
                                                           fertiliser_induced_field_emissions_co2, 2)],
            'Soil Management': [np.round(soil_management_soc_CO2eq_kg_ha, 2)],
            'Soil Mining': soil_mining_ghg_emission_kg_co2,
            'Land Use Change effect on soil': [luc_kg_co2_year],
            'Burning residues': [total_burning_kg_CO2eq],

        })

        total_emissions = np.array([np.round(fertiliser_production_CO2eq_kg_ha, 2),
                                    np.round(fertiliser_induced_field_emissions_n2o +
                                             fertiliser_induced_field_emissions_co2, 2),
                                    np.round(soil_management_soc_CO2eq_kg_ha, 2),
                                    luc_kg_co2_year,
                                    total_burning_kg_CO2eq]).sum()

        fertiliser_data.caco3_emissions_by_limestone_application()

        #### RICE
        crop = soil_emissions.soil_inputs.crop.values[0].lower()

        if crop == "rice" or crop == "arroz":
            rice_emissions, rice_soilmanagement = ghg_from_rice(soil_emissions, fertiliser_data)
            retults['Methane from rice'] = rice_emissions
            total_emissions -= retults['Soil Management'].values[0]
            retults['Soil Management'] = rice_soilmanagement
            total_emissions += rice_soilmanagement

        ## table | total emissions | Nitrogen applied
        return [retults, total_emissions,
                np.array(fertiliser_data.application_inN_synthetic).sum(),
                soil_emissions.crop_yield_kg_ha]

    def multiple_events(self):
        """Gauge ghg emissions for multiple events"""
        table_summary = []
        total_n_amount = []
        crop_yield = []
        for id_event in self.id_list:
            summary_ghg_emissions = self.calculate_emissions_for_a_single_event(id_event)
            if summary_ghg_emissions[0].shape[1] == 7:
                summary_ghg_emissions[0]['Methane from rice'] = np.nan

            table_summary.append(summary_ghg_emissions[0])
            total_n_amount.append(summary_ghg_emissions[2])
            crop_yield.append(summary_ghg_emissions[3])

        return [pd.concat(table_summary), total_n_amount, crop_yield]

    def __init__(self,
                 input_general_path,
                 input_fert_file_path,
                 id_event=np.nan,
                 id_column_name='id_event'):

        self._general_info = pd.read_excel(input_general_path)
        ##removing nan from the id list
        self.id_list = [i for i in self._general_info[id_column_name] if np.logical_not(pd.isnull(i))]
        self._input_fertilisers_table = pd.read_excel(input_fert_file_path)

        self.emissions_summary = np.nan
        if np.logical_not(pd.isnull(id_event)):
            if id_event in self.id_list:
                summary_ghg_emissions = self.calculate_emissions_for_a_single_event(id_event)
                self.emissions_summary = summary_ghg_emissions[0]
                summary_single_event = self.emissions_summary.drop(['id_event', 'municipality'], axis=1).copy()
                self.total_ghg = summary_single_event.iloc[0].values.sum()
                self._N_total_amount = summary_ghg_emissions[2]
                self._N_total_amount = summary_ghg_emissions[3]

        else:
            ghg_emissions_perevent = self.multiple_events()
            self.emissions_summary = ghg_emissions_perevent[0]
            self._N_total_amount = ghg_emissions_perevent[1]
            self._yield = ghg_emissions_perevent[2]

        #####



def calculate_co2eq_by_soilmining(general_info, fertiliser_info):
    baseline_namount = np.array(fertiliser_info.application_inN_synthetic).sum() + np.array(
        fertiliser_info.application_inN_organic).sum()
    n_content_harvested = general_info.get_nh3_n2o_by_crop()[2]
    moisture_content_harvested = general_info.get_nh3_n2o_by_crop()[3]

    cropyield = general_info.crop_yield_kg_ha
    cropyielddry = general_info.crop_yield_kg_ha - (
            general_info.crop_yield_kg_ha * (moisture_content_harvested / 100))
    n_removal_inharvest = cropyielddry * (n_content_harvested / 100)

    current_nue = (n_removal_inharvest / baseline_namount) * 100

    balance_n_rate = n_removal_inharvest / 0.85

    if baseline_namount < balance_n_rate:
        additional_fert = balance_n_rate - baseline_namount
    else:
        additional_fert = 0
    return (additional_fert * 8)


def ghg_from_rice(soil_emissions, fertiliser_data):
    intercept = 0.363
    soc = 0.3371
    rice_soil_management = soil_emissions.rice_factors()
    rice_fertiliserfactors = fertiliser_data.get_rice_fertiliser_factors(soil_emissions.soil_c_stock)

    pH_value = rice_soil_management[0][0]
    pw_value = rice_soil_management[1][0]
    w_value = rice_soil_management[2][0]
    cl_value = rice_soil_management[3]

    rice_fert_factors = rice_fertiliserfactors[0]
    if len(rice_fert_factors) > 1:
        fert_flux = np.array([i[0] * math.log(1 + i[1]) for i in rice_fert_factors]).sum()
    else:
        fert_flux = np.array([0 * math.log(1 + 0)]).sum()

    if pd.isnull(soil_emissions.soil_organic_c):
        soil_organic_c = 0
    else:
        soil_organic_c = soil_emissions.soil_organic_c

    if soil_organic_c != 0:
        ch4emission_lnflux = (intercept + soc * math.log(soil_organic_c) +
                              pH_value + pw_value + w_value + cl_value + fert_flux)
    else:
        ch4emission_lnflux = (intercept +
                              pH_value + pw_value + w_value + cl_value + fert_flux)

    ch4emission_flux = math.exp(ch4emission_lnflux)

    ch4_kg_ch4_ha_day = (ch4emission_flux * 10000 * 24) / (1000 * 1000)

    sdate = soil_emissions.crop_duration()[0]
    hdate = soil_emissions.crop_duration()[1]
    if (np.issubdtype(sdate, np.datetime64) and
            np.issubdtype(hdate, np.datetime64)):
        dif_dates = soil_emissions.crop_duration()[1] - soil_emissions.crop_duration()[0]
        days = dif_dates.astype('timedelta64[D]') / np.timedelta64(1, 'D')

    else:
        print("no dates detected, crop date assumed as 120")
        days = 120

    ch4_kg_ch4_ha = ch4_kg_ch4_ha_day * days * ef.pc_CH4
    ###soil management

    rice_tillfactor = rice_soil_management[4]
    rice_cropaddfactor = rice_soil_management[5]
    org_fert_mit = rice_fertiliserfactors[1]

    rice_smanagement = np.array(org_fert_mit + [rice_tillfactor[0]] + [rice_cropaddfactor[0]]).min()

    return [ch4_kg_ch4_ha, rice_smanagement]


def calculate_n2o_ghg_from_soil_fertilizers(soil_emissions, fertiliser_data):
    backgrounds_log_n2o = np.array([ef.constantN2O, soil_emissions.get_n2o_soil_organic_content(),
                                    soil_emissions.get_n2o_nh3_by_pH_content()[0],
                                    soil_emissions.get_n2o_by_texture(),
                                    soil_emissions.get_n2o_no_by_climate()[0],
                                    soil_emissions.get_nh3_n2o_by_crop()[1],
                                    soil_emissions.get_n2o_no_by_experiment_length()[0]
                                    ])

    background_n2o_emissions = math.exp(backgrounds_log_n2o.sum())

    n_equivalent_emissions = np.array(
        [ef.N_application_rate_constant * i for i in
         fertiliser_data.application_inN_synthetic + fertiliser_data.application_inN_organic]).sum()

    fertiliserinducedemission_n2o = ((math.exp(
        backgrounds_log_n2o.sum() + n_equivalent_emissions) - background_n2o_emissions) *
                                     fertiliser_data.weigthedsum)

    total_n2o_total_flux = fertiliserinducedemission_n2o + background_n2o_emissions

    total_n2o_total_flux_kgN2Oha = total_n2o_total_flux * ef.N_to_N2O

    return total_n2o_total_flux_kgN2Oha * ef.pc_N2O_MOT


def calculate_no_ghg_from_soil_fertilizers(soil_emissions, fertiliser_data):
    backgroundemission_log_no = np.array([soil_emissions.get_no_by_n_content(),
                                          ef.constantNO,
                                          soil_emissions.get_n2o_no_by_climate()[1],
                                          soil_emissions.get_n2o_no_by_experiment_length()[1]])

    background_no_emissions = math.exp(backgroundemission_log_no.sum()) * 0.01

    no_equivalent_emissions = np.array(
        [ef.NO_application_rate_constant * i for i in
         fertiliser_data.application_inN_synthetic + fertiliser_data.application_inN_organic]).sum()

    fertiliserinducedemission_no = ((math.exp(
        backgroundemission_log_no.sum() + no_equivalent_emissions) * 0.01 - background_no_emissions) *
                                    fertiliser_data.weigthedsum_no)

    total_NO_total_flux = fertiliserinducedemission_no + background_no_emissions

    total_NO_total_flux_kgN2Oha = total_NO_total_flux * ef.N_to_N2O

    return total_NO_total_flux_kgN2Oha * ef.pc_N2O_MOT


def emissions_by_volatilization(soil_emissions, fertiliser_data):
    bowman_nh3 = ff.calculate_multiple_fertiliser_emissions(fertiliser_data.synthetic_products,
                                                            ef.fertilizers_factors,
                                                            fun_name='bouwman_index',
                                                            col_name='fertiliser_sp')

    coefficients_per_product = []

    for bowman, application, nammount in zip(bowman_nh3, fertiliser_data.nh3_emissions_by_application(),
                                             fertiliser_data.application_inN_synthetic):
        pH_nh3_content = soil_emissions.get_n2o_nh3_by_pH_content()[1]
        climate_nh3_content = soil_emissions.get_n2o_no_by_climate()[2]
        crop_nh3_content = soil_emissions.get_nh3_n2o_by_crop()[0]
        cec_nh3 = soil_emissions.estimate_soil_cec()[1]

        coeff_nh3 = np.sum([pH_nh3_content, climate_nh3_content, crop_nh3_content, cec_nh3, bowman, application])
        coefficients_per_product.append(math.exp(coeff_nh3) * nammount)

    volatilizationfactor = ef.volatilizationfactors.loc[
        ef.volatilizationfactors.iloc[:, 4] == "Volatilization"].iloc[0, 5]

    nh3_volatilization_kgnha = np.array(coefficients_per_product).sum() * volatilizationfactor
    nh3_volatilization_kgN2Oha = nh3_volatilization_kgnha * ef.N_to_N2O

    return nh3_volatilization_kgN2Oha * ef.pc_N2O_MOT


def emissions_by_leaching(soil_emissions, fertiliser_data):
    filter_conditions = (ef.leachingfactors.iloc[:, 1] ==
                         soil_emissions._cl_eng_input.capitalize())

    if np.array(filter_conditions).sum() != 0:
        leachingfactorclimate = ef.leachingfactors.loc[ef.leachingfactors.iloc[:, 1] ==
                                                       soil_emissions._cl_eng_input.capitalize()].iloc[0, 2]
    else:
        leachingfactorclimate = 0

    leachingfactor = ef.leachingfactors.loc[ef.leachingfactors.iloc[:, 4] == "Leaching"].iloc[0, 5]

    n_leaching_kgnha = np.sum(
        fertiliser_data.application_inN_synthetic) * leachingfactor * leachingfactorclimate
    n_leaching_kgN2Oha = n_leaching_kgnha * ef.N_to_N2O

    return n_leaching_kgN2Oha * ef.pc_N2O_MOT


