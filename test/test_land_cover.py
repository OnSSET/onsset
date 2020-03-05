import os

from onsset import SettlementProcessor

from pandas import DataFrame,Series
from pandas.testing import assert_frame_equal, assert_series_equal
from pytest import fixture


class TestSettlementProcessor:

    @fixture
    def setup_settlementprocessor(self) -> SettlementProcessor:

        csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
        settlementprocessor = SettlementProcessor(csv_path)

        return settlementprocessor
   
    def test_classify_land_cover(self,setup_settlementprocessor):
        sp = setup_settlementprocessor
        df = DataFrame({'LandCover':list(range(17))})

        actual = sp.classify_land_cover(df['LandCover'])

        print (actual)

        expected =Series([1,3,4,3,4,3,2,5,2,5,5,1,3,3,5,3,5], name='LandCover')

        print (expected)
        assert_series_equal(actual, expected)
       