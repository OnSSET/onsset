#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 16:22:12 2020

@author: balderrama
"""
from onsset import Technology


def technology_creation(start_year, end_year, grid_price, specs_data, diesel_price, pv_capital_cost_adjust):
    
    technologies = []

    Technology.set_default_values(base_year=start_year,
                                      start_year=start_year,
                                      end_year=end_year,
                                      discount_rate=0.08)

    grid_calc = Technology(om_of_td_lines=0.02,
                               distribution_losses=float(specs_data.iloc[0]['GridLosses']),
                               connection_cost_per_hh=125,
                               base_to_peak_load_ratio=0.8,
                               capacity_factor=1,
                               tech_life=30,
                               grid_capacity_investment=float(specs_data.iloc[0]['GridCapacityInvestmentCost']),
                               grid_penalty_ratio=1,
                               grid_price=grid_price,
                               name = 'Grid',
                               code = 1)
    
    technologies.append(grid_calc)
    
    mg_hydro_calc = Technology(om_of_td_lines=0.02,
                                   distribution_losses=0.05,
                                   connection_cost_per_hh=100,
                                   base_to_peak_load_ratio=0.85,
                                   capacity_factor=0.5,
                                   tech_life=30,
                                   capital_cost={float("inf"): 3000},
                                   om_costs=0.03,
                                   mini_grid=True,
                                   name = 'MG_Hydro',
                                   code = 7)
    
    technologies.append(mg_hydro_calc)
    
    mg_wind_calc = Technology(om_of_td_lines=0.02,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=100,
                                  base_to_peak_load_ratio=0.85,
                                  capital_cost={float("inf"): 3750},
                                  om_costs=0.02,
                                  tech_life=20,
                                  mini_grid=True,
                                  name = 'MG_Wind',
                                  code = 6)
    
    technologies.append(mg_wind_calc)

    mg_pv_calc = Technology(om_of_td_lines=0.02,
                                distribution_losses=0.05,
                                connection_cost_per_hh=100,
                                base_to_peak_load_ratio=0.85,
                                tech_life=20,
                                om_costs=0.015,
                                capital_cost={float("inf"): 2950 * pv_capital_cost_adjust},
                                mini_grid=True,
                                name = 'MG_PV',
                                code = 5)

    technologies.append(mg_pv_calc)
    
    sa_pv_calc = Technology(base_to_peak_load_ratio=0.9,
                                tech_life=15,
                                om_costs=0.02,
                                capital_cost={float("inf"): 6950 * pv_capital_cost_adjust,
                                              1: 4470 * pv_capital_cost_adjust,
                                              0.100: 6380 * pv_capital_cost_adjust,
                                              0.050: 8780 * pv_capital_cost_adjust,
                                              0.020: 9620 * pv_capital_cost_adjust
                                              },
                                standalone=True,
                                name = 'SA_PV',
                                code = 3)
    
    technologies.append(sa_pv_calc)

    mg_diesel_calc = Technology(om_of_td_lines=0.02,
                                    distribution_losses=0.05,
                                    connection_cost_per_hh=100,
                                    base_to_peak_load_ratio=0.85,
                                    capacity_factor=0.7,
                                    tech_life=15,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 721},
                                    mini_grid=True,
                                    name = 'MG_Diesel',
                                    code = 4)
    
    technologies.append(mg_diesel_calc)

    sa_diesel_calc = Technology(base_to_peak_load_ratio=0.9,
                                    capacity_factor=0.5,
                                    tech_life=10,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 938},
                                    standalone=True,
                                    name = 'SA_Diesel',
                                    code = 2)
    
    technologies.append(sa_diesel_calc)

    sa_diesel_cost = {'diesel_price': diesel_price,
                          'efficiency': 0.28,
                          'diesel_truck_consumption': 14,
                          'diesel_truck_volume': 300}

    mg_diesel_cost = {'diesel_price': diesel_price,
                          'efficiency': 0.33,
                          'diesel_truck_consumption': 33.7,
                          'diesel_truck_volume': 15000}
    
    return technologies, sa_diesel_cost, mg_diesel_cost
    