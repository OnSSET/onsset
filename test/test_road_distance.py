import os
from pandas import DataFrame,Series,cut
from pandas.testing import assert_frame_equal, assert_series_equal
from pytest import fixture


# class TestSettlementProcessor:

#     @fixture
#     def setup_settlementprocessor(self) -> SettlementProcessor:

#         csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
#         settlementprocessor = SettlementProcessor(csv_path)

#         return settlementprocessor

@fixture
def setup_dataframe() -> DataFrame:
    df = DataFrame({'RoadDist':[0,11.954,14.282,10.472]})
    return df
   
def test_road_distance(setup_dataframe):

    #  sp = setup_settlementprocessor
    df = setup_dataframe
       
    #define bins as -inf to 5, 5 to 10, 10 to 25, 25 to 50, 50 to inf
    road_distance_bins = [0,5,10,25,50,float("inf")]
    #define classifiers
    road_distance_labels = [5,4,3,2,1]


    actual = cut(df['RoadDist'], road_distance_bins,
                            labels=road_distance_labels, include_lowest=True).astype(float)
        
    print (actual)
    
    expected =Series([5,3,3,3], name='RoadDist').astype(float)

    print (expected)
    assert_series_equal(actual, expected)
                    
