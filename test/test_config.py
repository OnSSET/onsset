import os

from onsset.runner import read_scenario_data


def test_read_scenario_data():
    """Store the configuration data as a dictionary
    """

    path = os.path.join('test', 'test_data', 'config.csv')

    data = [
        ['Country', 'Benin'],
        ['CountryCode', 'bj'],
        ['StartYear', 2020],
        ['EndYEar', 2030],
        ['PopStartYear', 12123000],
        ['UrbanRatioStartYear', 0.484],
        ['PopEndYearHigh', 15672000],
        ['PopEndYearLow', 15672000],
        ['UrbanRatioEndYear', 0.541],
        ['NumPeoplePerHHRural', 3.6],
        ['NumPeoplePerHHUrban', 3.1],
        ['GridCapacityInvestmentCost', 1982],
        ['GridLosses', 0.143],
        ['DiscountRate', 0.08],
        ['BaseToPeak', 0.8],
        ['ExistingGridCostRatio', 0.1],
        ['MaxGridExtensionDist', 50],
        ['NewGridGenerationCapacityAnnualLimitMW', 70],
        ['ElecActual', 0.42],
        ['Rural_elec_ratio', 0.18],
        ['Urban_elec_ratio', 0.67],
        ['UrbanTargetTier', 5],
        ['RuralTargetTier', 4],
        ['5YearTarget', 0.71],
        ['GridConnectionsLimitThousands', 9999],
        ['GridGenerationCost', 0.16],
        ['PV_Cost_adjust', 1.25],
        ['DieselPrice', 9999],
        ['ProductiveDemand', 0],
        ['PrioritizationAlgorithm', 2],
        ['AutoIntensificationKM', 0]
        ]
    actual = read_scenario_data(path)
    expected = dict(data)

    assert actual == expected
