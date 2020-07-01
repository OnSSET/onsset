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

    @fixture
    def setup_dataframe(self) -> DataFrame:
        df = DataFrame(
            {'X_deg': [42.00045, 41.9767, 42.0131],
             'Y_deg': [10.9668, 10.97138, 10.97166],
             'TravelHours': [0, 10, 20]
            })
        return df

    def test_diesel_cost_columns(self, setup_settlementprocessor: SettlementProcessor,
                                 setup_dataframe: DataFrame):
        """

        The ``diesel_cost_columns`` method receives a pandas.Series of
        travel hours, indexed by Lat,Lon coordinates

        It returns a DataFrame indexed by Lat,Lon coordinates with
        one column for each diesel gen type

        Diesel cost is calculated using the following formulae:

        (diesel_price + 2 * diesel_price * diesel_truck_consumption *
                        traveltime) / diesel_truck_volume / LHV_DIESEL / efficiency

        For travel hours 0, result should be:

        (0.1 + 2*0.1 * 14 * 0) / 300 / 9.9445485 / 0.28 = 0.00011971143692206745

        10 hours:

        (0.1 + 2*0.1 * 14 * 10) / 300 / 9.9445485 / 0.28 = 0.03363891377510096

        20 hours:

        (0.1 + 2*0.1 * 14 * 20) / 300 / 9.9445485 / 0.28 = 0.06715811611327985
        """

        sp = setup_settlementprocessor

        df = setup_dataframe

        sa_diesel_cost = {'diesel_price': 0.10,
                          'efficiency': 0.28,
                          'diesel_truck_consumption': 14,
                          'diesel_truck_volume': 300}

        mg_diesel_cost = {'diesel_price': 0.1,
                          'efficiency': 0.33,
                          'diesel_truck_consumption': 33.7,
                          'diesel_truck_volume': 15000}
        year = 2015

        actual = sp.compute_diesel_cost(df, sa_diesel_cost, mg_diesel_cost, year)
        expected = DataFrame(
            {'X_deg': [42.00045, 41.9767, 42.0131],
             'Y_deg': [10.9668, 10.97138, 10.97166],
             'SADieselFuelCost2015': [0.035913431076620234,
                                      0.06943263341479913,
                                      0.10295183575297802],
             'MGDieselFuelCost2015': [0.03047200212561717,
                                      0.03184121075446157,
                                      0.03321041938330597]
             })

        assert_frame_equal(actual, expected)
