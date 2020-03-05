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

    def test_grid_penalties(self, setup_settlementprocessor: SettlementProcessor,
                                 setup_dataframe: DataFrame):
    
        sp = setup_settlementprocessor

        df = setup_dataframe
        
        actual=sp.grid_penalties(df)
        print(actual, type(actual))

        expected = Series([1.0892443601228534,1.1076348215198037,1.0737289748812726])
       
        print(expected)
            
        # check_less_precise ensures that it does not consider
        assert_series_equal(actual, expected, check_less_precise= False)
       