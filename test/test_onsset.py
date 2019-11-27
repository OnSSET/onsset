from onsset.onsset import Technology


def test_calcuate_capital_investment():

    technology = Technology(10, 0.2, capital_cost=0.32)

    installed_capacity = 1
    conflict_sa_pen = {1: 42}
    conf_status = 1
    system_size = 0.02

    actual = technology.calcuate_capital_investment(installed_capacity, conflict_sa_pen, conf_status, system_size)
    expected = 13.44
    assert actual == expected


def test_hv_mv_ratio_property():

    technology = Technology(10, 0.2, capital_cost=0.32)

    actual = technology.hv_mv_ratio
    expected = 42
    assert actual == expected
