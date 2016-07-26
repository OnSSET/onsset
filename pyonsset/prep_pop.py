import pandas as pd
import os

def run(settlements, specs):
    settlements_csv = os.path.join('Tables', settlements)
    country_specs_xlsx = os.path.join('Tables', specs)

    df = pd.read_csv(settlements_csv)
    country_specs = pd.read_excel(country_specs_xlsx, index_col = 0)

    countries = country_specs.index.values.tolist()

    for c in countries:
        # Calibrate actual population
        pop_tot = float(country_specs.loc[c, 'Pop2015TotActual'])
        pop_sum = df.loc[df.Country == c, 'Pop'].sum()
        pop_ratio = pop_tot/pop_sum

        df.loc[df.Country == c, 'Pop2015Act'] = df.loc[df.Country == c].apply(lambda row:
                                                                           row['Pop'] * pop_ratio
                                                                           , axis=1)

        # Urban split, calibrate to actual value
        count = 0
        target = country_specs.loc[c, 'UrbanRatio']
        cutoff = country_specs.loc[c, 'UrbanCutOff']
        prev_vals = []

        while True:
            df.loc[df.Country == c, 'IsUrban'] = df.loc[df.Country == c].apply(lambda row:
                                                                  1
                                                                  if row['Pop2015Act'] > cutoff
                                                                  else 0
                                                                  , axis=1)

            pop_urb = df.ix[df.Country == c][df.loc[df.Country == c]['IsUrban'] == 1]['Pop2015Act'].sum()
            calculated = pop_urb / pop_tot

            print("{}\t\turban: {}\t\tcutoff: {}".format(c, calculated, cutoff))

            if calculated == 0: calculated = 0.05
            elif calculated == 1: calculated = 0.999

            if abs(calculated - target) < 0.005:
                print('satisfied')
                break
            else: cutoff = sorted([0.005, cutoff - cutoff * 2 *(target-calculated)/target, 10000.0])[1]

            if cutoff in prev_vals:
                print('repeating myself')
                break
            else: prev_vals.append(cutoff)

            if count >= 30:
                print('got to 30')
                break

            count += 1

        country_specs.loc[c, 'UrbanCutOff'] = cutoff
        country_specs.loc[c, 'UrbanRatioModelled'] = calculated

        print("{} done urban split".format(c))

        # Project 2030 population
        urban_growth = country_specs.loc[c, 'UrbanGrowth']
        rural_growth = country_specs.loc[c, 'RuralGrowth']

        df.loc[df.Country == c, 'Pop2030'] = df.loc[df.Country == c].apply(lambda row:
                                                                           row['Pop2015Act'] * urban_growth
                                                                           if row['IsUrban'] == 1
                                                                           else row['Pop2015Act'] * rural_growth
                                                                           , axis=1)


    df.to_csv(settlements_csv,index=False)
    country_specs.to_excel(country_specs_xlsx)