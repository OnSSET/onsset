import os
import pandas as pd
import logging

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

SET_POP = 'Pop'
SET_POP_CALIB = 'PopStartYear'
SET_URBAN = 'IsUrban'
SPE_URBAN_FUTURE = 'UrbanRatioEndYear'

pop_dict = {'ao': 43230578,
            'bf': 26447328,
            'bi': 15286009,
            'bj': 15088412,
            'bw': 2683123,
            'cd': 116615769,
            'cf': 5905661,
            'cg': 7057834,
            'ci': 32149804,
            'cm': 31800060,
            'dj': 1086262,
            'er': 6460542,
            'et': 134141337,
            'ga': 2496926,
            'gh': 35903736,
            'gm': 2899449,
            'gn': 17005669,
            'gq': 1807626,
            'gw': 2403006,
            'ke': 64306541,
            'km': 1023087,
            'lr': 6257687,
            'ls': 2489396,
            'mg': 34207767,
            'ml': 26180409,
            'mr': 5871502,
            'mw': 25567123,
            'mz': 40988426,
            'na': 3108924,
            'ne': 33981604,
            'ng': 255535878,
            'rw': 15403358,
            'sd': 52911016,
            'sl': 9348303,
            'sn': 21340368,
            'so': 20847888,
            'ss': 16648367,
            'st': 258533,
            'sz': 1589844,
            'td': 20758348,
            'tg': 10123501,
            'tz': 80707587,
            'ug': 61605875,
            'za': 61689536,
            'zm': 23967676,
            'zw': 20628864}

countries = ['ao', 'bf', 'bi', 'bj', 'bw', 'cd', 'cf', 'cg', 'ci', 'cm', 'dj', 'er', 'et', 'ga', 'gh', 'gm', 'gn', 'gq',
             'gw', 'ke', 'km', 'lr', 'ls', 'mg', 'ml', 'mr', 'mw', 'mz', 'na', 'ne', 'ng', 'rw', 'sd', 'sl', 'sn', 'so',
             'ss', 'st', 'sz', 'td', 'tg', 'tz', 'ug', 'za', 'zm', 'zw']

def project_pop_and_urban(df, pop_future_high, urban_future):
    """
    This function projects population and urban/rural ratio for the different years of the analysis
    """
    start_year = 2018
    intermediate_year = 2025
    end_year = 2030
    
    project_life = end_year - start_year

    # Project future population, with separate growth rates for urban and rural
    pop_modelled = df[SET_POP_CALIB].sum()
    urban_pop = df.loc[df[SET_URBAN] == 2, SET_POP_CALIB].sum()
    urban_modelled = urban_pop / pop_modelled

    urban_growth_high = (urban_future * pop_future_high) / (urban_modelled * pop_modelled)
    rural_growth_high = ((1 - urban_future) * pop_future_high) / ((1 - urban_modelled) * pop_modelled)

    yearly_urban_growth_rate_high = urban_growth_high ** (1 / project_life)
    yearly_rural_growth_rate_high = rural_growth_high ** (1 / project_life)

    # RUN_PARAM: Define here the years for which results should be provided in the output file.
    years_of_analysis = [intermediate_year, end_year]

    for year in years_of_analysis:
        df[SET_POP + "{}".format(year) + 'Lowest'] = \
            df.apply(lambda row: row[SET_POP_CALIB] * (yearly_urban_growth_rate_high ** (year - start_year))
            if row[SET_URBAN] > 1
            else row[SET_POP_CALIB] * (yearly_rural_growth_rate_high ** (year - start_year)), axis=1)

    df[SET_POP + "{}".format(start_year)] = df.apply(lambda row: row[SET_POP_CALIB], axis=1)

for country in countries:
    logging.info(country)
    specs_path = os.path.join('C:/Users/asahl/Box Sync/Scenario_discovery/Specs_files', "{}-1-specs.xlsx".format(country))
    csv_path = os.path.join('C:/Users/asahl/Box Sync/EGI Energy Systems/06 Projects/2017-11 WB Electrification Platform/Paper/Andreas Paper files/{}_inputs'.format(country),'{}-1-country-inputs.csv'.format(country))
    csv_out = os.path.join('C:/Users/asahl/Box Sync/EGI Energy Systems/06 Projects/2017-11 WB Electrification Platform/Paper/Andreas Paper files/{}_inputs'.format(country), '{}-1-country-inputs_NEW.csv'.format(country))

    specs_data = pd.read_excel(specs_path, sheet_name='SpecsData')
    urban_future = specs_data.loc[0, SPE_URBAN_FUTURE]
    pop_future = pop_dict[country]

    df = pd.read_csv(csv_path)

    project_pop_and_urban(df, pop_future, urban_future)

    df.to_csv(csv_out, index=False)
