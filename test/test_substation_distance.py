import os

from onsset import SettlementProcessor

from pandas import DataFrame,Series
from pandas.testing import  assert_series_equal
from pytest import fixture


class TestSettlementProcessor:

    @fixture
    def setup_settlementprocessor(self) -> SettlementProcessor:

        csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
        settlementprocessor = SettlementProcessor(csv_path)

        return settlementprocessor
   
    def test_classify_substation_distance(self, setup_settlementprocessor):

        sp = setup_settlementprocessor
        df = DataFrame({'Substation':[-1,0,11.954,14.282,10.472]})

        actual = sp.classify_substation_distance(df['Substation'])    
        print (actual)
        
        expected =Series(['NaN','NaN',1,1,1], name='Substation').astype(float)

        print (expected)
        assert_series_equal(actual, expected)