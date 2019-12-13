import os

from onsset import SettlementProcessor

from pandas import DataFrame , Series
from pandas.testing import assert_frame_equal , assert_series_equal
from pytest import fixture

"GRIDPENALTY"
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
             'RoadDist':[11.954,14.282,10.472],
             'SubstationDist':[77.972,80.351,76.497],
             'LandCover':[2,16,5],
             'Elevation':[4,5,-3],
             'Slope':[0.75,1.498,0.73],

            })
        return df

    def test_grid_penalties_helper(self, setup_settlementprocessor: SettlementProcessor,
                                 setup_dataframe: DataFrame):
    
    #     """

    #     The ``diesel_cost_columns`` method receives a pandas.Series of
    #     travel hours, indexed by Lat,Lon coordinates

    #     It returns a DataFrame indexed by Lat,Lon coordinates with
    #     one column for each diesel gen type

    #     Diesel cost is calculated using the following formulae:

    #     (diesel_price + 2 * diesel_price * diesel_truck_consumption *
    #                     traveltime) / diesel_truck_volume / LHV_DIESEL / efficiency

    #     For travel hours 0, result should be:

    #     (0.1 + 2*0.1 * 14 * 0) / 300 / 9.9445485 / 0.28 = 0.00011971143692206745

    #     10 hours:

    #     (0.1 + 2*0.1 * 14 * 10) / 300 / 9.9445485 / 0.28 = 0.03363891377510096

    #     20 hours:

    #     (0.1 + 2*0.1 * 14 * 20) / 300 / 9.9445485 / 0.28 = 0.06715811611327985
    #     """

        sp = setup_settlementprocessor

        df = setup_dataframe
       

        
        actual=sp.grid_penalties_helper(df)
        print(actual, type(actual))

        # expected = Series(
        #     {'X_deg': [42.00045, 41.9767, 42.0131],
        #      'Y_deg': [10.9668, 10.97138, 10.97166],
        #      'RoadDist':[11.954,14.282,10.472],
        #      'SubstationDist':[77.972,80.351,76.497],
        #      'LandCover':[2,16,5],
        #      'Elevation':[4,5,-3],
        #      'Slope':[0.75,1.498,0.73],
        #      'GridPenalty':[1.0892443601228534,1.1076348215198037,1.0737289748812726]
        #     })
        expected = Series([1.0892443601228534,1.1076348215198037,1.0737289748812726])
       
        print(expected)
            
        # check_less_precise ensures that it does not consider
        assert_series_equal(actual, expected, check_less_precise= False)
       