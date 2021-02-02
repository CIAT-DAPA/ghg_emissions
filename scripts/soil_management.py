import numpy as np
import os
import pandas as pd
from scripts import emission_factors_mot as ef
from scripts import translations as tl
from scripts import soilgrid_functions as sgf
from scripts import general_functions as gf
from scripts import fertiliser_practices as fp
from scripts import rice_estimations as rice


# SOILGRID_ORGANIC_CARBON_STOCK_PATH = "soilgrids/ocs_0_30cm_mean_southamerica.tif"
# SOILGRID_ORGANIC_CARBON_PATH = "soilgrids/soc_0_5cm_mean_southamerica.tif"
# SOILGRID_BULKDENSITY_PATH = "soilgrids/bdod_0_5cm_mean_southamerica.tif"
# SOILGRID_PH_PATH = "soilgrids/phh2o_0_5cm_mean_southamerica.tif"
# SOILGRID_NITROGEN_PATH = "soilgrids/nitrogen_0_5cm_mean_southamerica.tif"


class soil_management_emissions:
    """Get soil emissions factors and properties for gauging ghg.


               Parameters
               ----------

               input_table : pandas data frame
                       Table

               soil_emissions table : str



               Attributes
               ----------
               soil_properties : list
                       List of soil properties that contain following values texture, soc, n content, pH and bulk density

               soil_emissions table : str
        """

    def get_soil_properties(self):
        """get soil properties from the input, there are two alternatives, one that the
        values are inferred regarding the soil type, or that the table contains the values individually"""

        if np.logical_not(pd.isnull(self.soil_inputs.soil.values[0])):
            option_column = "eng_options"
            soil_type_options = tl.soil_type[1]
            if self.language == "spanish":
                option_column = "sp_options"
                soil_type_options = tl.soil_type[0]

            tipo_suelo = self.soil_inputs.soil.values[0]

            if tipo_suelo.lower() in [i.lower() for i in soil_type_options]:
                self.soil_texture = ef.soil_properties.loc[
                    ef.soil_properties[option_column].str.lower() == tipo_suelo].values[0][2]
                self.soil_organic_c = ef.soil_properties.loc[
                    ef.soil_properties[option_column].str.lower() == tipo_suelo].values[0][3]
                self.n_content = ef.soil_properties.loc[
                    ef.soil_properties[option_column].str.lower() == tipo_suelo].values[0][4]
                self.pH_content = ef.soil_properties.loc[
                    ef.soil_properties[option_column].str.lower() == tipo_suelo].values[0][5]
                self.soil_bulk_density = ef.soil_properties.loc[
                    ef.soil_properties[option_column].str.lower() == tipo_suelo].values[0][6]
        else:
            self.soil_organic_c = self.soil_inputs.soil_organic_content.values[0]
            self.n_content = self.soil_inputs.soil_n_content.values[0]
            self.pH_content = self.soil_inputs.soil_pH.values[0]
            self.soil_bulk_density = self.soil_inputs.bulk_density.values[0]
            self.soil_texture = self.soil_inputs.soil_texture.values[0]

            if self.language == "spanish":
                soil_text_options = [i.lower() for i in tl.soil_texture[0]]
                if self.soil_texture in soil_text_options:
                    self.soil_texture = tl.soil_texture[1][soil_text_options.index(self.soil_texture.lower())]
                else:
                    self.soil_texture = "medium"

            self.soil_organic_c = self.soil_inputs.soil_organic_content.values[0]

    def get_n2o_soil_organic_content(self):
        """ get N2O soil content due to soil organic"""
        attribute_temp = 'more than 3.0'
        if float(self.soil_organic_c) < 1.0:
            attribute_temp = 'less than 1.0'
        elif (float(self.soil_organic_c) >= 1.0) and (float(self.soil_organic_c) < 3.0):
            attribute_temp = '1.0-3.0'

        soc_n2o_content = ef.n2o_soc_options.loc[ef.n2o_soc_options.iloc[:, 1] == attribute_temp].iloc[:, 2].values[0]
        return soc_n2o_content

    def get_no_by_n_content(self):
        """ get No soil content due to soil organic"""

        attribute_temp = 'more than 0.2'
        if float(self.n_content) < 0.05:
            attribute_temp = 'less than 0.05'
        elif (float(self.n_content) >= 0.05) and (float(self.n_content) < 0.2):
            attribute_temp = '0.05-0.2'

        n_no_content = ef.n_soc_options.loc[ef.n_soc_options.iloc[:, 1] == attribute_temp].iloc[:, 3].values[0]
        return n_no_content

    def get_n2o_nh3_by_pH_content(self):
        """ get NH3 and N2O soil content due by pH"""

        ph_attribute = 'more than 8.5'
        if float(self.pH_content) < 5.5:
            ph_attribute = 'less than 5.5'
        elif (float(self.pH_content) >= 5.5) and (float(self.pH_content) < 7.3):
            ph_attribute = '5.5-7.3'
        elif (float(self.pH_content) >= 7.3) and (float(self.pH_content) < 8.5):
            ph_attribute = '7.3-8.5'

        pH_n2o_content = ef.pH_n2o_options.loc[ef.pH_n2o_options.iloc[:, 1] == ph_attribute].iloc[:, 2].values[0]
        pH_nh3_content = ef.pH_nh3_options.loc[ef.pH_nh3_options.iloc[:, 0] == ph_attribute].iloc[:, 1].values[0]

        return ([pH_n2o_content, pH_nh3_content, ph_attribute])

    def rice_factors(self):
        """ rice factors"""
        years_tillage_tech = self.soil_inputs.time_using_tillage_system.values[0]
        years_cropcover_tech = self.soil_inputs.time_using_crop_cover.values[0]

        rice_pH_factor = rice.get_nh4_by_pH_content(self.pH_content)
        pw_class_input = self.soil_inputs.pre_water_regime.values[0]
        w_class_input = self.soil_inputs.water_regime.values[0]
        cl_sp_input = self.soil_inputs.specific_climate_for_rice.values[0]
        if pd.notnull(pw_class_input):
            prew_factor = rice.pre_water_regime_factor(pw_class_input, self.language)
            wr_factor = rice.water_regime_factor(w_class_input, self.language)
            cl_factor = rice.sp_climate_factor(cl_sp_input, self.language)
        else:
            prew_factor = [0]
            wr_factor = [0]
            cl_factor = 0

        ### tillage
        if years_tillage_tech <= 20:
            till_factor20 = rice.mitigation_by_tillage(self._til_eng_input)
            till_factor20 = (-1 * self.soil_c_stock * (till_factor20 - 1)) * (44 / 12)
            till_factor = [till_factor20 / 20, till_factor20]
        else:
            till_factor = [0, 0]
        ### adding crop cover
        if years_tillage_tech <= 20:
            cropadd_factor20 = rice.mitigation_by_cropadding(self._cc_eng_input, self._cl_eng_input)
            cropadd_factor20 = (-1 * self.soil_c_stock * (cropadd_factor20 - 1)) * (44 / 12)
            cropadd_factor = [cropadd_factor20 / 20, cropadd_factor20]
        else:
            cropadd_factor = [0, 0]

        return ([rice_pH_factor, prew_factor, wr_factor, cl_factor, till_factor, cropadd_factor])

    def get_n2o_by_texture(self):
        """ get N2O soil content by texture"""

        texture_n2o_content = \
            ef.texture_n2o_options.loc[ef.texture_n2o_options.iloc[:, 1] == self.soil_texture.capitalize()].iloc[:,
            2].values[
                0]
        return (texture_n2o_content)

    def get_n2o_no_by_climate(self):

        climate_n2o_content = \
            ef.climate_options_table.loc[ef.climate_options_table.iloc[:, 1] == self._cl_eng_input.capitalize()
                                         ].iloc[:, 2].values[0]
        climate_no_content = \
            ef.climate_options_table.loc[ef.climate_options_table.iloc[:, 1] == self._cl_eng_input.capitalize()
                                         ].iloc[:, 3].values[0]

        climate_nh3_content = \
            ef.climate_nh3_options.loc[ef.climate_nh3_options.iloc[:, 0] == self._cl_eng_input.capitalize()
                                       ].iloc[:, 1].values[0]

        return [climate_n2o_content, climate_no_content,
                climate_nh3_content]

    def get_nh3_n2o_by_crop(self):

        crop = self.soil_inputs.crop.values[0]

        if self.language == "spanish":
            col_name = "crop_spanish"
        else:
            col_name = "Crop"

        # major_class = ef.crop_factors['Major class'].loc[ef.crop_factors[col_name] == crop].values[0]

        if crop.lower() in ef.crop_factors[col_name].str.lower().values:
            bouwman_equi = ef.crop_factors["Bouwman's equivalent"].loc[
                ef.crop_factors[col_name].str.lower().values == crop.lower()].values[0]
        else:
            bouwman_equi = ef.crop_factors["Bouwman's equivalent"].loc[
                ef.crop_factors["crop_spanish"].str.lower().values == 'otro'].values[0]

        pos_list = list(ef.crop_nh3_options.iloc[:, 0].str.lower().values).index(bouwman_equi.lower())
        crop_nh3_content = ef.crop_nh3_options.iloc[pos_list].values[1]

        pos_list = list(ef.cropbouwman_n2o_options_table.iloc[:, 1].str.lower().values).index(bouwman_equi.lower())
        crop_n2o_content = ef.cropbouwman_n2o_options_table.iloc[pos_list].values[2]

        ### crop n content
        crop_ncontent = \
            ef.crop_factors["N content"].loc[ef.crop_factors[col_name].str.lower().values == crop.lower()].values[0]
        ## crop Moisture content (%)
        crop_harvestmoist = ef.crop_factors["Moisture content (%)"].loc[
            ef.crop_factors[col_name].str.lower().values == crop.lower()].values[0]
        return ([crop_nh3_content, crop_n2o_content, crop_ncontent, crop_harvestmoist])

    def get_n2o_no_by_experiment_length(self):
        """ by default less than 300 days to do change regarding the crop extension"""

        lengthexpriment_n2ocontent = ef.lengthexperimet_factors['Per year (<300 days)'][0]
        lengthexpriment_nocontent = ef.lengthexperimet_factors['Per year (<300 days)'][0]

        return [lengthexpriment_n2ocontent, lengthexpriment_nocontent]

    def estimate_soil_cec(self):

        # pH
        ph_attribute = self.get_n2o_nh3_by_pH_content()[2]
        ph_valueforcec = ef.cec_factors.loc[ef.cec_factors.iloc[:, 1] == ph_attribute].iloc[:, 2].values[0]

        texture_factorforcec = \
            ef.cec_factors.loc[ef.cec_factors.iloc[:, 1] == self.soil_texture.capitalize()].iloc[:, 2].values[0]
        if self.soil_bulk_density != 0:
            estimated_soil_cec = ((-59 + 51 * ph_valueforcec) * self.soil_c_stock / 3000000 / self.soil_bulk_density +
                                  (30 + 4.4 * ph_valueforcec) * texture_factorforcec)
        else:
            estimated_soil_cec = ((-59 + 51 * ph_valueforcec) * self.soil_c_stock / 3000000 / 1 +
                                  (30 + 4.4 * ph_valueforcec) * texture_factorforcec)

        cec_attribute = 'more than 32'
        if float(estimated_soil_cec) < 16:
            cec_attribute = 'less than 16'
        elif (float(estimated_soil_cec) >= 16) and (float(estimated_soil_cec) < 24):
            cec_attribute = '16-24'
        elif (float(estimated_soil_cec) >= 24) and (float(estimated_soil_cec) < 32):
            cec_attribute = '24-32'

        cec_nh3 = ef.cec_nh3_options.loc[ef.cec_nh3_options.iloc[:, 0] == cec_attribute].iloc[:, 1].values[0]

        return [estimated_soil_cec, cec_nh3, cec_attribute]

    def tillage_technology(self):
        """Gauging the soil organic content change due to tillage practices.
        Currently, there are three different types of practices
            'cero labranza' | 'no tillage',
            'labranza convencional'| 'conventional tillage',
            'labranza reducida' | 'reduced tillage'
        The number of years in which the practices have been implemented must be provided, ,
        otherwise, a 10 years value will be assignated by default"""

        ## getting input parameter

        tillage_input = self.soil_inputs.tillage_input.values[0]
        if pd.isnull(tillage_input):
            tillage_input = "na"

        #climate_input = self.soil_inputs.climate.values[0]

        years_tillage_tech = self.soil_inputs.time_using_tillage_system.values[0]

        if np.isnan(years_tillage_tech):
            years_tillage_tech = 10

        if self.language == "spanish":
            climate_options = [i.lower() for i in tl.climate_options[0]]
            tillage_options = [i.lower() for i in tl.tillage_options[0]]
        else:
            tillage_options = [i.lower() for i in tl.tillage_options[1]]
            climate_options = [i.lower() for i in tl.climate_options[1]]

        # if (climate_input.lower() in climate_options):
        # self._cl_eng_input = tl.climate_options[1][climate_options.index(climate_input.lower())]

        if tillage_input.lower() in tillage_options:

            til_eng_input = tl.tillage_options[1][tillage_options.index(tillage_input.lower())]
            self._til_eng_input = til_eng_input
            to_tillagefilter = ef.tillage_factors.To_till.str.lower() == til_eng_input.lower()
            defaulttillage = ef.tillage_factors.From_till.str.lower() == 'conventional tillage'
            print("Climate Classification: {}".format(self._cl_eng_input))
            climatefilter = ef.tillage_factors.Climate.str.lower() == self._cl_eng_input.lower()

            if climatefilter.sum() == 0:
                cl_eng_input = tl.world_climate_bouwman[1][tl.world_climate_bouwman[0].index(self._cl_eng_input)]
                climatefilter = ef.tillage_factors.Climate.str.lower() == cl_eng_input.lower()

            filter_conditions = climatefilter & defaulttillage & to_tillagefilter
            if (np.array(filter_conditions).sum() != 0):
                factor_change_20years = ef.tillage_factors.Factor.loc[
                    climatefilter & defaulttillage & to_tillagefilter].values[0]
            else:
                factor_change_20years = 1
            self.tillage_soc_change = cumulative_socemissions_for_20years(years_tillage_tech,
                                                                          factor_change_20years,
                                                                          self.soil_c_stock)
        else:
            self.tillage_soc_change = [0]

    def burning_residues(self):
        """Gauging the emissions by burning residues"""
        burninginput = self.soil_inputs.residues_input.values[0]

        crop = self.soil_inputs.crop.values[0]

        if self.language == "spanish":
            col_name = "crop_spanish"
        else:
            col_name = "Crop"

        slope_above_ground = ef.ramount_factors.loc[ef.ramount_factors[col_name].str.lower() == crop][
            'Slope_above ground residue'].values[0]
        drymatter_factor = ef.ramount_factors.loc[ef.ramount_factors[col_name].str.lower() == crop][
            'DRY(Dry matter fraction of harvested product)'].values[0]
        intercept_factor = ef.ramount_factors.loc[ef.ramount_factors[col_name].str.lower() == crop][
            'Intercept_above ground residue'].values[0]
        ratiobelowground_residue = ef.ramount_factors.loc[ef.ramount_factors[col_name].str.lower() == crop][
            'Ratio of belowground to aboveground residue'].values[0]

        above_residues = self.crop_yield_kg_ha / 1000 * slope_above_ground * drymatter_factor + intercept_factor
        belowground_residue = above_residues * ratiobelowground_residue
        total_biomas = belowground_residue + above_residues

        if ((burninginput == "quema") | (burninginput == "burning")):
            burningCH4_emissions_kg = above_residues * (ef.burned_CH4factor / 1000) * 1000
            burningN2O_emissions_kg = above_residues * (ef.burned_N2Ofactor / 1000) * 1000

        else:
            burningCH4_emissions_kg = 0
            burningN2O_emissions_kg = 0

        burning_CH4emissions_kg_CO2eq = burningCH4_emissions_kg * ef.pc_CH4
        burning_N2Oemissions_kg_CO2eq = burningN2O_emissions_kg * ef.pc_N2O_MOT
        total_burning_kg_CO2eq = burning_N2Oemissions_kg_CO2eq + burning_CH4emissions_kg_CO2eq

        return (total_burning_kg_CO2eq)

    def emmissions_by_luc(self):
        """Gauging the emissions by luc"""
        luc_input = self.soil_inputs.luc.values[0]
        luc_time = self.soil_inputs.luc_time.values[0]

        if np.isnan(luc_time):
            years_tillage_tech = 10

        if self.language == "spanish":
            luc_options = [i.lower() for i in tl.luc_options[0]]
            #climate_options = [i.lower() for i in tl.climate_options[0]]
        else:
            luc_options = [i.lower() for i in tl.luc_options[1]]
            #climate_options = [i.lower() for i in tl.climate_options[1]]

        if np.logical_not(pd.isnull(luc_input)):

            if luc_input.lower() in luc_options:
                luc_eng_input = tl.luc_options[1][luc_options.index(luc_input.lower())]

                changefilter = ef.luc_factors['change-nr'] == ef.luc_options[luc_eng_input][0]
                climatefilter = ef.luc_factors.Climate.str.lower() == self._cl_eng_input.lower()
                filter_conditions = climatefilter & changefilter

                if np.array(filter_conditions).sum() != 0:
                    luc_factor = ef.luc_factors.factor.loc[filter_conditions].values[0]
                else:
                    cl_eng_input = tl.world_climate_bouwman[1][tl.world_climate_bouwman[0].index(self._cl_eng_input)]

                    changefilter = ef.luc_factors['change-nr'] == ef.luc_options[luc_eng_input][0]
                    climatefilter = ef.luc_factors.Climate.str.lower() == cl_eng_input.lower()
                    filter_conditions = climatefilter & changefilter
                    luc_factor = ef.luc_factors.factor.loc[filter_conditions].values[0]

                self.luc_effect_on_soil = cumulative_socemissions_for_20years(luc_time, luc_factor, self.soil_c_stock)
        else:
            self.luc_effect_on_soil = 0

    def cover_crop_added(self):
        """Gauging the soil organic content change due to Temporary vegetative cover between
        agricultural crops. Currently, there are two options crop vegetative:
        The number of years in which the practices have been implemented must be provided, ,
        otherwise, a 10 years value will be assignated by default"""

        ## getting input parameter
        crop_input = self.soil_inputs.crop_cover.values[0]
        if pd.isnull(crop_input):
            crop_input = "nan"
        #climate_input = self.soil_inputs.climate.values[0]
        years_cropcover_tech = self.soil_inputs.time_using_crop_cover.values[0]

        if np.isnan(years_cropcover_tech):
            years_cropcover_tech = 10

        if self.language == "spanish":
            #climate_options = [i.lower() for i in tl.climate_options[0]]
            cover_crop_options = [i.lower() for i in tl.cover_crop_options[0]]
        else:
            #climate_options = [i.lower() for i in tl.climate_options[1]]
            cover_crop_options = [i.lower() for i in tl.cover_crop_options[1]]

        if crop_input.lower() in cover_crop_options:

            cc_eng_input = tl.cover_crop_options[1][cover_crop_options.index(crop_input.lower())]
            self._cc_eng_input = cc_eng_input
            #cl_eng_input = tl.climate_options[1][climate_options.index(self._cl_eng_input.lower())]

            covercropfilter = ef.cover_cropping_factors.Change.str.lower() == cc_eng_input.lower()
            climatefilter = ef.cover_cropping_factors.Climate.str.lower() == self._cl_eng_input.lower()

            if climatefilter.sum() == 0:
                cl_eng_input = tl.world_climate_bouwman[1][tl.world_climate_bouwman[0].index(self._cl_eng_input)]
                climatefilter = ef.cover_cropping_factors.Climate.str.lower() == cl_eng_input.lower()

            filter_conditions = climatefilter & covercropfilter
            if np.array(filter_conditions).sum() != 0:
                factor_change_20years = ef.cover_cropping_factors.Factor.loc[filter_conditions].values[0]
            else:
                factor_change_20years = 1

            self.cover_crop_soc_change = cumulative_socemissions_for_20years(years_cropcover_tech,
                                                                             factor_change_20years,
                                                                             self.soil_c_stock)
        else:
            self.cover_crop_soc_change = [0]

    def crop_duration(self):
        """Calculate crop duration using as a reference the sowing and
        harvesting dates"""

        s_date = self.soil_inputs.sowing_date.values[0]
        h_date = self.soil_inputs.harvest_date.values[0]

        return [s_date, h_date]

    def __init__(self,
                 input_table,
                 language="spanish"):

        self._til_eng_input = np.nan
        self._cc_eng_input = np.nan

        self.language = language
        self.soil_inputs = input_table

        self.crop_yield_kg_ha = self.soil_inputs.crop_yield_kg_ha.values[0]
        self._longitude = self.soil_inputs.longitude.values[0]
        self._latitude = self.soil_inputs.latitude.values[0]

        ### get climate intput from coordinates
        self._cl_eng_input = 'temperate continental'

        if (np.logical_not(pd.isnull(self._longitude)) and
                np.logical_not(pd.isnull(self._latitude))):
            climate_classification = get_climate_fromlayers(self._longitude,
                                                            self._latitude)
            self._cl_eng_input = mot_climate_classification(climate_classification)

        self.get_soil_properties()  ##.

        ## calculating soil carbon stock
        if np.logical_not(np.isnan(self.soil_organic_c)) and np.logical_not(np.isnan(self.soil_bulk_density)):
            self.soil_c_stock = 10000 * 0.3 * self.soil_organic_c * self.soil_bulk_density / 100 * 1000
        else:
            [self.soil_c_stock, self.soil_bulk_density,
             self.n_content, self.pH_content, self.soil_organic_c] = self.fill_with_gridsoilvalues()

        self.tillage_technology()
        self.cover_crop_added()  ## cover crop
        self.emmissions_by_luc()

        self._soil_cec = self.estimate_soil_cec()[0]

    def fill_with_gridsoilvalues(self):

        soil_organic_stock = 0
        soil_organic_content = 0
        soil_bulk_density = 0
        n_content = 0
        pH_content = 0

        if np.logical_not(pd.isnull(self._longitude) or
                          pd.isnull(self._latitude)):

            soil_organic_stock = sgf.get_soilgridpixelvalue("Soil organic carbon stock",
                                                            self._longitude, self._latitude) * 1000

            soil_bulk_density = sgf.get_soilgridpixelvalue("Bulk density",
                                                           self._longitude, self._latitude) / 100

            if pd.isnull(self.n_content):
                n_content = sgf.get_soilgridpixelvalue("Nitrogen",
                                                       self._longitude, self._latitude) / 1000
            else:
                n_content = self.n_content

            if pd.isnull(self.pH_content):
                pH_content = sgf.get_soilgridpixelvalue("pH water",
                                                        self._longitude, self._latitude) / 10
            else:
                pH_content = self.pH_content

            soil_organic_content = sgf.get_soilgridpixelvalue("Organic carbon density",
                                                              self._longitude, self._latitude) / 100

        print(
            "Soil properties were drawn from soilgrid\n bulk_density:{} n_content: {} pH_content: {}, soil_organic_content:{}".format(
                soil_bulk_density,
                n_content, pH_content,
                soil_organic_content))
        return [soil_organic_stock, soil_bulk_density,
                n_content, pH_content, soil_organic_content]


def get_climate_fromlayers(longitude, latitude):
    """ get climate classification from layers
    :param longitude: wgs 84 longitude
    :param latitude: wgs 84 latitude
    :return: str list: koppen classification and climateregion classification
    """
    koppen_path = "climate_classification/world_climate_class_koppen.tif"
    koppen_value = sgf.getCoordinatePixel(koppen_path, longitude, latitude)

    if len(koppen_value[0]) > 0:
        koppen_value = koppen_value[0][0][0]
    else:
        koppen_value = 0

    climateregion_path = "climate_classification/world_climate_regions_Sayre.tif"
    cliregion_value = sgf.getCoordinatePixel(climateregion_path, longitude, latitude)

    if len(cliregion_value[0]) > 0:
        cliregion_value = cliregion_value[0][0][0]
    else:
        cliregion_value = 0

    return [koppen_value, cliregion_value]


def cumulative_socemissions_for_20years(years_usingtec, factor_20years, soil_c_stock):
    """Function that calculates the soc changes for 20 years
    :param years_usingtec:
    :param factor_20years:
    :param soil_c_stock:
    :return:
    """

    if years_usingtec < 20:
        if factor_20years == 1:
            Cumulative_considering_20_years = 0
        else:
            Cumulative_considering_20_years = (-1 * soil_c_stock * (factor_20years - 1)) * (44 / 12)
        annual_change = Cumulative_considering_20_years / 20
    else:
        Cumulative_considering_20_years = 0
        annual_change = 0

    return [annual_change,
            Cumulative_considering_20_years]


def mot_climate_classification(cl_classification):
    """

    :param cl_classification:
    :return:
    """
    koppenclimate = np.nan
    sayreclimate = np.nan

    koppen = cl_classification[0]
    sayre = cl_classification[1]

    for i in tl.world_climate_koppen.keys():
        if koppen in tl.world_climate_koppen[i][0]:
            koppenclimate = i

    if np.logical_not(pd.isnull(koppenclimate)):
        cl_eng_class = koppenclimate

    else:
        for i in tl.world_climate_sayre.keys():
            if sayre in tl.world_climate_sayre[i][0]:
                sayreclimate = i

        cl_eng_class = sayreclimate

    if pd.isnull(cl_eng_class):
        cl_eng_class = "temperate continental"
    return cl_eng_class
