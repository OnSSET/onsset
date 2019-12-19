import os

from onsset import SettlementProcessor

from pandas import DataFrame,Series,cut
from pandas.testing import assert_frame_equal, assert_series_equal
from pytest import fixture


class TestSettlementProcessor:

    @fixture
    def setup_settlementprocessor(self) -> SettlementProcessor:

        csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
        settlementprocessor = SettlementProcessor(csv_path)

        return settlementprocessor
   
    def test_classify_road_distance(self, setup_settlementprocessor):

        sp = setup_settlementprocessor
        df = DataFrame({'RoadDist':[0,11.954,14.282,10.472]})

        actual = sp.classify_road_distance(df['RoadDist'])    
        print (actual)
        
        expected =Series([5,3,3,3], name='RoadDist').astype(float)

        print (expected)
        assert_series_equal(actual, expected)
                        
