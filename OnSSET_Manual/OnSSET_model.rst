OnSSET Model
=============

OnSSET determines the least-cost electrification strategy in a region based on minimizing the Levelized Cost of Electricity generation (LCOE). The study area is divided into a mesh of square grid cells, then four parameters determine the LCOE per location assuming
full electrification by 2030:

1)  Target level and quality of energy access, i.e., the amount of electricity that already electrified and yet to
    be electrified households will be provided with, measured in kWh/person/year.

2)  Population density, measured in people/km^2.

3)  Local grid connection characteristics including the distance from the nearest grid (km) and the
    average national cost of grid supplied electricity ($/kWh).

4)  Local renewable energy resource availability and diesel costs.

Electricity demand
**********************

OnSSET finds the least-cost electrification strategy based on the residential electricity demand. At first the cells
that are likely to already be electrified by the national grid are identified, whereas the remaining cells are considered
unelectrified. This is based on geospatial data as described in the following section to match the official statistics
for the electrified population.

Once the electrified and non-electrified population has been spatially identified, we incorporate the expected
population growth rates per region to estimate the total population in the eng year of the analysis (e.g. 2030). This is one of the two parameters we need to know to quantify and locate the future electricity demand. The second parameter is the target level of
electricity access; the modelling adopts the consumption levels defined as electricity access tiers by the Global
Tracking Framework (2015).
These tiers indicate electricity consumption levels starting from 22 kWh/hh/year, enough
electricity only enough for task lightning, charge a phone or power a radio (Tier 1), up to approx. 2195 kWh/hh/year,
allowing for enough electricity to run several heavy or continuous appliances like refrigerator, washing machine, oven etc.
(Tier 5). The model currently allows the user to specify different target tiers for urban rural population.
The combination of the population and assumed electrification consumption levels allows estimations regarding the future
electricity demand per location by 2030.


Electrification options
*****************************

Over the last few decades, access to electricity has been established by connecting households and businesses to the national
interconnected electricity central grid. However, technological innovation in renewable energy sources and concerns
about social inclusion have added a handful of technologies to feasibly generate electricity in a decentralized
manner resorting to mini-grids or standalone alternatives. Seven configurations
of energy technologies are considered in each cell by OnSSET. These have be divided into the three aforementioned
categories; grid-extension, mini-grids and standalone systems.

**Grid extension:**
Central grids can offer low generating costs. However, grid extension might not be economically or socially
feasible if the purpose is to meet a relatively small electricity demand or for remotely located areas.

**Mini-grids (Wind Turbines, Solar PVs, Mini/Small Hydro, Diesel gensets):**
Mini grids usually provide electricity from small power plants with generating capacity of few MW.
They tap locally available energy resources such as solar, hydro, wind, or can use commonly available fuels such as diesel.
Overall, they can provide affordable electricity to rural and remote areas with low-medium electricity consumption habits.
Cost-wise, if based on renewable sources, they usually have moderate to high upfront investment costs but
small operational monetary costs and no fuel costs. On the other hand, diesel generator sets (gensets) are a mature
technology with low upfront investment cost but subjected to operational costs depending on diesel pump price and
transport costs fluctuations.

**SA (Solar PVs, Diesel gensets):**
As mini grids, these systems are usually based on local energy resources but the difference is that these can produce
only few kWh per day, suitable to cover the electricity demand of a single household or a small business, but no more.
Stand-alone systems do not require a T&D network nor construction investments. The capital cost of these systems is
not high and depends mainly on size. Batteries, allowing for electricity when dark, may increase the upfront cost for PV systems.


Brief description of the electrification algorithm
****************************************************************
The electrification algorithm procedure is based on two separate, yet complementary processes. On the one hand, a GIS
analysis is required to obtain a settlement table referencing each settlement’s position –i.e., its x and y coordinates
– and information related to demand, resource, availability, infrastructure and economic activities. Night-time light
datasets are used in combination with population density and distribution, the transmission and the road network in
order to identify the presently electrified populations. The initial electrification status is listed as either 1
(electrified) or 0 (non-electrified).

The algorithm calculates the cost of generating electricity at each cell for different electrification configurations
based on the local specificities and cost related parameters. Depending on the electricity demand, transmission and distribution
network requirements, energy resource availability etc. the LCOE for each of the seven technology configurations is
calculated in each cell. The LCOE of a specific technology option represents the final cost of electricity required for
the overall system to break even over the project lifetime.

.. note::

    The LCOE calculations for the mini-grid and standalone electrification options reflect the total system costs while
    the LCOE for the grid option is the sum of the average LCOE of the national grid plus the marginal LCOE of
    transmitting and distributing electricity from the national grid to the demand location.

Once the LCOEs for all the off-grid technology configurations have been calculated the grid extension algorithm is
executed. For each cell electrified by the national grid the algorithm iterates through all
non-electrified cells to test if the conditions for their connection to the electrified cell are fulfilled.
These conditions include:

a) lower cost of generating, transmitting and distributing electricity as compared to the off-grid
technologies and

b) not causing the total additional MV grid length to exceed 50 km if it is connected. 

If these conditions are verified, the settlement status is set to electrified (by the national grid). At the same time, the algorithm
stores the length of the additional MV lines that have been built thus far by the model to connect this new settlement.
This is required to ensure all newly electrified cells comply with the 50 km limit for the length of MV lines. Further,
this is also used to consider cost increases for each additional MV extension, due to the requirement to strengthen the
previously built grid line. This process is repeated with the newly electrified cells until no additional cells are being
electrified, and thus until all settlements to which the grid can be economically extended are reached. Settlements that
are not connected to the grid will get access to electricity through mini grid or stand-alone systems. This decision is
based on a cost comparison process where the off-grid technology which can meet the electricity demand at the lowest LCOE
selected for each cell.

Penalty cost assignment to electricity grid expansion processess
*****************************************************************

The expansion of the transmission network to areas lacking access is a capital intensive process. The investment costs
are influenced by several factors such as the capacity, the type and the length of the lines as well as by the topology
of the subjected area. In this analysis, a number of geospatial factors that affect the investment costs of the
transmission network are identified and considered in order to assign an incremental capital cost in locations that
indicate specific topological features. More particularly, investment cost is influenced by elevation, the road network,
land cover type, slope gradient and distance from substations.


Renewable energy resource potentials
************************************

Wind energy potential and capacity factors
------------------------------------------

GIS wind speed data is used to calculate the capacity factor. The latter is defined as the ratio of the yearly expected
wind energy production to the energy production if the wind turbine were to operate at its rated power throughout the
year. The capacity factor reflects the potential wind power at a given site and it can be used for comparing different
sites before the installation of wind power plants.

Solar energy potential
----------------------

Solar data that provides insights about the global horizontal irradiation (GHI - kWh/m^2/time). The LCOE of stand-alone
solar PVs is calculated based on the radiation and the system costs. The LCOE of mini-grids solar PVs is calculated based
on the above parameters and the population density of settlements.
