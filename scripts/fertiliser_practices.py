import numpy as np
import pandas as pd
from scripts import emission_factors_mot as ef
from scripts import translations as tl
from scripts import fertiliser_functions as ff
from scripts import rice_estimations as rice

ORGANIC_FERTILISER_TYPES = ['compost', 'manure', 'residue']


class fertiliser_management:
    """Get fertiliser emissions factors and properties for ghg.


                  Parameters
                  ----------

                  input_table : pandas data frame
                          Table

                  language : str



                  Attributes
                  ----------
                  n_ammount : list
                          List of nitrogen amount used

                   : str
           """

    def split_fertiliser_type(self):

        list_of_organicproducts = {}
        list_of_syntheticproducts = {}

        option_column = "fertiliser_eng"

        if self.language == "spanish":
            option_column = "fertiliser_sp"

        orgcount = 0
        syntcount = 0
        if pd.isnull(self.fertiliser_table.amount_kg_ha).sum() > 0:
            if self.fertiliser_table.shape[0] == 1:
                fertiliser_table = ff.assign_fertilizer_products(self.fertiliser_table)
            else:
                fertiliser_table = self.fertiliser_table.copy()
                fertiliser_table.loc[pd.isnull(fertiliser_table.amount_kg_ha).values, 'amount_kg_ha'] = 0

        else:
            fertiliser_table = self.fertiliser_table.copy()

        for ind in range(fertiliser_table.shape[0]):

            table_subset = fertiliser_table.iloc[ind]

            fert = table_subset.fertliser_product.lower()

            fert_emissions_factors = ef.fertilizers_factors.loc[
                ef.fertilizers_factors[option_column].str.lower() == fert]

            if np.logical_not(fert in
                              ef.fertilizers_factors[option_column].str.lower().values):
                fert = "another_fert"
                fert_type = ""
                fert_emissions_factors = ef.fertilizers_factors.loc[
                    ef.fertilizers_factors[option_column].str.lower() == fert]
            else:
                fert_type = fert_emissions_factors.type.values[0]

            # table_subset = fert_table_copy.loc[fert_table_copy.fertliser_product == fert]

            if pd.isnull(table_subset.amount_kg_ha):
                table_subset.amount_kg_ha = 0

            if fert_type in ORGANIC_FERTILISER_TYPES:

                of_type = ORGANIC_FERTILISER_TYPES[ORGANIC_FERTILISER_TYPES.index(
                    fert_type)]
                if pd.isnull(table_subset.years_using_the_fertlizer):
                    years = 10
                else:
                    years = int(table_subset.years_using_the_fertlizer)
                list_of_organicproducts[orgcount] = [table_subset.amount_kg_ha,  # amount
                                                     years,  # years
                                                     of_type,  # type
                                                     fert  # fertiliser
                                                     ]
                orgcount += 1

            else:
                list_of_syntheticproducts[syntcount] = [table_subset.amount_kg_ha,
                                                        table_subset.inhibitor,
                                                        table_subset.production_country,
                                                        fert]
                syntcount += 1


        self.organic_products = list_of_organicproducts
        self.synthetic_products = list_of_syntheticproducts

    def calculate_emission_by_inhibitors(self):

        organic_inhi_n2o = ff.calculate_inhibitor_release_multiple(self.organic_products,
                                                                   ef.fertilizers_factors,
                                                                   ef.inhibi_factors,
                                                                   'organic')

        synthetic_inhi_n2o = ff.calculate_inhibitor_release_multiple(self.synthetic_products,
                                                                     ef.fertilizers_factors,
                                                                     ef.inhibi_factors)

        organic_inhi_no = ff.calculate_inhibitor_release_multiple(self.organic_products,
                                                                  ef.fertilizers_factors,
                                                                  ef.inhibi_no_factors,
                                                                  'organic')
        synthetic_inhi_no = ff.calculate_inhibitor_release_multiple(self.synthetic_products,
                                                                    ef.fertilizers_factors,
                                                                    ef.inhibi_no_factors)

        return ([organic_inhi_n2o, synthetic_inhi_n2o,
                 organic_inhi_no, synthetic_inhi_no])

    def nh3_emissions_by_application(self):
        """ Calculate nh3 emission due to fertiliser application method"""

        application_method_fert = ff.calculate_multiple_fertiliser_emissions(self.synthetic_products,
                                                                             ef.fertilizers_factors,
                                                                             fun_name='application_method',
                                                                             col_name='fertiliser_sp')

        n_synthetic_applications = self.application_inN_synthetic

        application_method_nh3 = []
        for i in range(len(application_method_fert)):

            if n_synthetic_applications[i] != 0:

                application_method_nh3.append(
                    ef.method_appl_nh3_options.loc[
                        ef.method_appl_nh3_options.iloc[:, 0].str.lower() == application_method_fert[i].lower()
                        ].iloc[:, 1].values[0])
            else:
                application_method_nh3.append(0)

        return application_method_nh3

    def caco3_emissions_by_limestone_application(self):

        if self.language == "spanish":
            ref_limestonename = "cal"
            col_name = 'fertiliser_sp'
        else:
            ref_limestonename = "limestone"
            col_name = "fertiliser_eng"

        total_limestone_applied = []
        for fertiliser in self.synthetic_products:

            if fertiliser == ref_limestonename:
                total_limestone_applied.append(
                    ff.calculate_n_amount_applied(fertiliser, self.synthetic_products[fertiliser][0],
                                                  ef.fertilizers_factors, col_name, table_nutrient='CaCO3') *
                    ef.limestone_factor * 44 / 12)

        return total_limestone_applied

    def get_rice_fertiliser_factors(self, soilcstock):

        if len(self.organic_products) > 0:
            dataframe = pd.DataFrame.from_dict(self.organic_products).transpose()

            dataframe.columns = ["amount", "years", "type", "product_name"]
            groupedamountsum = dataframe.groupby("type").amount.sum()
            dataframe.years = dataframe.years.astype('int64')
            yearsavg = dataframe.groupby("type").years.median()
            orgfertfactors = []
            for type in groupedamountsum.index.values:

                amount = groupedamountsum.loc[groupedamountsum.index == type].values[0]
                years = yearsavg.loc[yearsavg.index == type].values[0]
                amount_tones = amount / 1000
                baseline_cropadd = rice.factors_by_organic_fertilisers(type)

                baseline_crop = (1 + baseline_cropadd['All crops_Intercept'].values[0] +
                                 baseline_cropadd['Rice_Omamount_factor'].values[0] * amount_tones +
                                 baseline_cropadd['Rices_duration_factor'].values[0] * 20)

                if years <= 20:
                    baseline_crop = (-1 * soilcstock * ((1 + (baseline_crop - 1) * 20) - 1)) * (44 / 12)
                else:
                    baseline_crop = 0
                orgfertfactors.append(baseline_crop)

            emission_factors = ff.calculate_multiple_fertiliser_emissions(self.organic_products, ef.fertilizers_factors,
                                                                          'rice_factors')

            org_splitted = [i / 20 for i in orgfertfactors]
        else:
            emission_factors = [0]
            org_splitted = [0]

        return [emission_factors,
                org_splitted]

    def emissions_by_urea_application(self):

        if self.language == "spanish":
            ref_1 = "urea"
            ref_2 = "solución de nitrato de amonio urea"
            col_name = 'fertiliser_sp'
        else:
            ref_1 = "urea"
            ref_2 = "urea ammonium nitrate solution"
            col_name = "fertiliser_eng"

        total_urea_applied = []
        for ind in self.synthetic_products:
            fertiliser = self.synthetic_products[ind][len(self.synthetic_products[ind])-1]

            if fertiliser.lower() == ref_1.lower():
                total_urea_applied.append(
                    self.synthetic_products[ind][0] *
                    ef.urea_factor * (44 / 12))
            elif fertiliser.lower() == ref_2.lower():
                total_urea_applied.append(
                    self.synthetic_products[ind][0] * (0.25 / 0.73) *
                    ef.urea_factor * (44 / 12))
            else:
                total_urea_applied.append(0)

        return total_urea_applied

    def __init__(self,
                 input_table,
                 language="spanish"):

        self.language = language
        self.fertiliser_table = input_table

        self.split_fertiliser_type()
        ####

        self._compost_total_amount = ff.get_organic_specific_amount(self.organic_products, "compost")
        self._manure_total_amount = ff.get_organic_specific_amount(self.organic_products, "manure")
        self._residue_total_amount = ff.get_organic_specific_amount(self.organic_products, "residue")

        self.em_fert_production_CO2eq_kg_ha = np.array(
            ff.calculate_multiple_fertiliser_emissions(self.synthetic_products,
                                                       ef.fertilizers_factors, language=self.language)).sum()

        self.application_inN_synthetic = ff.calculate_multiple_fertiliser_emissions(self.synthetic_products,
                                                                                    ef.fertilizers_factors,
                                                                                    'n_amount_applied')

        self.application_inN_organic = ff.calculate_multiple_fertiliser_emissions(self.organic_products,
                                                                                  ef.fertilizers_factors,
                                                                                  'n_amount_applied')

        self.total_n_application = np.array(self.application_inN_synthetic + self.application_inN_organic).sum()

        if self.total_n_application != 0:
            self.weigthedsum = (np.array(self.calculate_emission_by_inhibitors()[0] +
                                         self.calculate_emission_by_inhibitors()[1]).sum() / self.total_n_application)
            self.weigthedsum_no = (np.array(self.calculate_emission_by_inhibitors()[2] +
                                            self.calculate_emission_by_inhibitors()[
                                                3]).sum() / self.total_n_application)
        else:
            self.weigthedsum = 0
            self.weigthedsum_no = 0

        #### NH3
