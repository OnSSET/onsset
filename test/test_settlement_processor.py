import os

from onsset import SettlementProcessor
from pandas import DataFrame
from pandas.testing import assert_frame_equal
from pytest import fixture


class TestSettlementProcessor:

    @fixture
    def setup_settlementprocessor(self) -> SettlementProcessor:

        csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
        settlementprocessor = SettlementProcessor(csv_path)

        return settlementprocessor

    def test_diesel_cost_columns(self, setup_settlementprocessor: SettlementProcessor):

        sp = setup_settlementprocessor

        sp.df = DataFrame(
            {'X_DEG': [42.00045, 41.9767, 42.0131],
             'Y_DEG': [10.9668, 10.97138, 10.97166],
             'TravelHours': [4.03333, 4.08333, 3.61667]
             })

        sa_diesel_cost = {'diesel_price': 0.10,
                          'efficiency': 0.28,
                          'diesel_truck_consumption': 14,
                          'diesel_truck_volume': 300}

        mg_diesel_cost = {'diesel_price': 0.1,
                          'efficiency': 0.33,
                          'diesel_truck_consumption': 33.7,
                          'diesel_truck_volume': 15000}
        year = 2015

        # Run the method
        actual = sp.diesel_cost_columns(sa_diesel_cost, mg_diesel_cost, year)
        expected = DataFrame(
            {'X_DEG': [42.00045, 41.9767, 42.0131],
             'Y_DEG': [10.9668, 10.97138, 10.97166],
             'SADieselFuelCost': [0, 0, 0],
             'MGDieselFuelCost': [0, 0, 0]
             })
        assert_frame_equal(actual, expected)
