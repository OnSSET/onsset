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
                                      discount_rate=0.12)

    grid_calc = Technology(om_of_td_lines=0.02,
                               distribution_losses=float(specs_data.iloc[0]['GridLosses']),
                               connection_cost_per_hh=125,
                               base_to_peak_load_ratio=float(specs_data.iloc[0]['BaseToPeak']),
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
                                   connection_cost_per_hh=125,
                                   base_to_peak_load_ratio=1,
                                   capacity_factor=0.5,
                                   tech_life=30,
                                   capital_cost={float("inf"): 5000},
                                   om_costs=0.02,
                                   mini_grid=True,
                                   name = 'MG_Hydro1',
                                   code = 7)
    
    technologies.append(mg_hydro_calc)

    mg_hydro_calc1 = Technology(om_of_td_lines=0.04,
                                   distribution_losses=0.03,
                                   connection_cost_per_hh=25,
                                   base_to_peak_load_ratio=1,
                                   capacity_factor=0.6,
                                   tech_life=30,
                                   capital_cost={float("inf"): 2000},
                                   om_costs=0.01,
                                   mini_grid=True,
                                   name = 'MG_Hydro2',
                                   code = 7)
    
    technologies.append(mg_hydro_calc1)


   
    mg_wind_calc = Technology(om_of_td_lines=0.02,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=125,
                                  base_to_peak_load_ratio=0.75,
                                  capital_cost={float("inf"): 2500},
                                  om_costs=0.02,
                                  tech_life=20,
                                  mini_grid=True,
                                  name = 'MG_Wind1',
                                  code = 6)
    
    technologies.append(mg_wind_calc)

    mg_wind_calc1 = Technology(om_of_td_lines = 0.02,
                                  distribution_losses = 0.05,
                                  connection_cost_per_hh = 225,
                                  base_to_peak_load_ratio = 0.55,
                                  capital_cost={float("inf"): 2000},
                                  om_costs=0.01,
                                  tech_life=15,
                                  mini_grid=True,
                                  name = 'MG_Wind2',
                                  code = 6)
    
    technologies.append(mg_wind_calc1)



    mg_pv_calc = Technology(om_of_td_lines=0.03,
                                distribution_losses=0.05,
                                connection_cost_per_hh=125,
                                base_to_peak_load_ratio=0.9,
                                tech_life=20,
                                om_costs=0.02,
                                capital_cost={float("inf"): 3500},
                                mini_grid=True,
                                name = 'MG_PV1',
                                code = 5)

    technologies.append(mg_pv_calc)
    
    mg_pv_calc1 = Technology(om_of_td_lines = 0.01,
                                distribution_losses = 0.03,
                                connection_cost_per_hh = 225,
                                base_to_peak_load_ratio = 0.5,
                                tech_life = 20,
                                om_costs = 0.01,
                                capital_cost = {float("inf"): 3000},
                                mini_grid = True,
                                name = 'MG_PV2',
                                code = 5)

    technologies.append(mg_pv_calc1)    
    
    
    sa_pv_calc = Technology(base_to_peak_load_ratio = 0.9,
                                tech_life = 15,
                                om_costs = 0.02,
                                capital_cost={float("inf"): 5070 * pv_capital_cost_adjust,
                                              0.200: 5780 * pv_capital_cost_adjust,
                                              0.100: 7660 * pv_capital_cost_adjust,
                                              0.050: 11050 * pv_capital_cost_adjust,
                                              0.020: 20000 * pv_capital_cost_adjust
                                              },
                                standalone=True,
                                name = 'SA_PV1',
                                code = 3)
    
    technologies.append(sa_pv_calc)

    sa_pv_calc1 = Technology(base_to_peak_load_ratio=0.8,
                                tech_life=20,
                                om_costs=0.01,
                                capital_cost={float("inf"): 6070 * pv_capital_cost_adjust,
                                              0.200: 8780 * pv_capital_cost_adjust,
                                              0.100: 10660 * pv_capital_cost_adjust,
                                              0.050: 12050 * pv_capital_cost_adjust,
                                              0.020: 15000 * pv_capital_cost_adjust
                                              },
                                standalone=True,
                                name = 'SA_PV2',
                                code = 3)
    
    technologies.append(sa_pv_calc1)

    mg_diesel_calc = Technology(om_of_td_lines=0.02,
                                    distribution_losses=0.05,
                                    connection_cost_per_hh=125,
                                    base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.7,
                                    tech_life=15,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 1000},
                                    mini_grid=True,
                                    name = 'MG_Diesel1',
                                    code = 4)
    
    technologies.append(mg_diesel_calc)

    mg_diesel_calc1 = Technology(om_of_td_lines=0.03,
                                    distribution_losses=0.07,
                                    connection_cost_per_hh=100,
                                    base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.8,
                                    tech_life=20,
                                    om_costs=0.08,
                                    capital_cost={float("inf"): 1500},
                                    mini_grid=True,
                                    name = 'MG_Diesel2',
                                    code = 4)
    
    technologies.append(mg_diesel_calc1)

    sa_diesel_calc = Technology(base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.5,
                                    tech_life=10,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 938},
                                    standalone=True,
                                    name = 'SA_Diesel1',
                                    code = 2)
    
    technologies.append(sa_diesel_calc)

    sa_diesel_calc1 = Technology(base_to_peak_load_ratio=0.8,
                                    capacity_factor=0.6,
                                    tech_life=20,
                                    om_costs=0.05,
                                    capital_cost={float("inf"): 1200},
                                    standalone=True,
                                    name = 'SA_Diesel2',
                                    code = 2)
    
    technologies.append(sa_diesel_calc1)

    
    
    transportation_cost = []
    
    transportation_cost.append({'diesel_price': diesel_price,
                                'fuel_price': diesel_price,
                                'tech_name': 'MG_Diesel1',
                                'efficiency': 0.33,
                                'fuel_LHV': 9.9445485,
                                'diesel_truck_consumption': 33.7,
                                'diesel_truck_volume': 15000})
        
    transportation_cost.append({'diesel_price': diesel_price,
                                'fuel_price': diesel_price,
                                'tech_name': 'MG_Diesel2',
                                'efficiency': 0.33,
                                'fuel_LHV': 9.9445485,
                                'diesel_truck_consumption': 33.7,
                                'diesel_truck_volume': 15000})
    
    transportation_cost.append({'diesel_price': diesel_price,
                                'fuel_price': diesel_price,
                                'tech_name' : 'SA_Diesel1',
                                'efficiency': 0.28,
                                'fuel_LHV': 9.9445485,
                                'diesel_truck_consumption': 14,
                                'diesel_truck_volume': 300})
    
    transportation_cost.append({'diesel_price': diesel_price,
                                'fuel_price': diesel_price,
                                'tech_name' : 'SA_Diesel2',
                                'efficiency': 0.28,
                                'fuel_LHV': 9.9445485,
                                'diesel_truck_consumption': 14,
                                'diesel_truck_volume': 300})    
        
    
    return technologies, transportation_cost
    