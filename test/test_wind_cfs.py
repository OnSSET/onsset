import os

from onsset import SettlementProcessor

from pandas import DataFrame, Series
from pandas.testing import assert_frame_equal, assert_series_equal
from pytest import fixture, raises, approx


class TestCalcWind:

    @fixture
    def setup_settlementprocessor(self) -> SettlementProcessor:
        csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
        settlementprocessor = SettlementProcessor(csv_path)

        return settlementprocessor

    def positive_wind_speed(self, setup_settlementprocessor):
        """

        Parameters
        ----------
        setup_settlementprocessor

        Returns
        -------

        """
        sp = setup_settlementprocessor
        wind_vel = 5.08063

        actual = sp.get_wind_cf(wind_vel)

        print(actual)

        expected = 0.08181981

        print(expected)
        assert actual == approx(expected)

    def test_calc_wind_cfs_zero(self, setup_settlementprocessor):
        """

        Parameters
        ----------
        setup_settlementprocessor

        Returns
        -------

        """
        sp = setup_settlementprocessor
        wind_vel = 0

        actual = sp.get_wind_cf(wind_vel)

        print(actual)

        expected = 0

        print(expected)
        assert actual == expected

    def test_calc_wind_cfs_negative(self, setup_settlementprocessor):
        """

        Parameters
        ----------
        setup_settlementprocessor

        Returns
        -------

        """
        sp = setup_settlementprocessor
        wind_vel = -1

        with raises(ValueError):
            sp.get_wind_cf(wind_vel)
