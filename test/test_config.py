import os

from onsset.runner import read_scenario_data


def test_read_scenario_data():
    """Store the configuration data as a dictionary
    """

    path = os.path.join('test', 'test_data', 'config.csv')

    data = [
        ['Country', 'Djibouti'],
        ['CountryCode', 'dj'],
        ['StartYear', 2018],
        ['EndYear', 2030],
        ['PopStartYear', 971000],
        ['UrbanRatioStartYear', 0.778],
        ['PopEndYearHigh', 1179150],
        ['PopEndYearLow', 1132710],
        ['UrbanRatioEndYear', 0.8],
        ['NumPeoplePerHHRural', 7.7],
        ['NumPeoplePerHHUrban', 6.5],
        ['GridCapacityInvestmentCost', 4426],
        ['GridLosses', 0.083],
        ['BaseToPeak', 0.8],
        ['ExistingGridCostRatio', 0.1],
        ['MaxGridExtensionDist', 50],
        ['NewGridGenerationCapacityAnnualLimitMW', 19],
        ['ElecActual', 0.6],
        ['Rural_elec_ratio', 0.26],
        ['Urban_elec_ratio', 0.7],
        ]
    actual = read_scenario_data(path)
    expected = dict(data)

    assert actual == expected
