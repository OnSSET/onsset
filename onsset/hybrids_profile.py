import cProfile
import os
from hybrids_pv import *
import logging

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

def profile_hybrids(iterations):
    tier = 5
    ghi = 2200

    logging.info('First')
    path = os.path.join(r'C:\GitHub\OnSSET\Results\sl-2-pv.csv')
    ghi_curve, temp = read_environmental_data(path)
    for i in range(iterations):
        a = pv_diesel_hybrid(9000, ghi, ghi_curve, temp, tier, 2020, 2030, 0.78)

profile_hybrids(1)


cProfile.run('profile_hybrids(100)', sort='tottime')

