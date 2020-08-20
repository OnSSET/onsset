import cProfile
import os
from hybrids3 import *
import logging

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

def profile_hybrids():
    pv_no = 15
    diesel_no = 15
    tier = 5
    ghi = 2200

    logging.info('First')
    path = os.path.join('Supplementary_files', 'ninja_pv_7.0000_2.3000_uncorrected.csv')
    ghi_curve, temp = read_environmental_data(path)
    a1, b1, c1, d1, e1, f1 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Second')
    path = os.path.join('Supplementary_files', 'ninja_pv_8.0000_2.3000_uncorrected.csv')
    ghi_curve, temp = read_environmental_data(path)
    a2, b2, c2, d2, e2, f2 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Third')
    path = os.path.join('Supplementary_files', 'ninja_pv_9.0000_2.3000_uncorrected.csv')
    ghi_curve, temp = read_environmental_data(path)
    a3, b3, c3, d3, e3, f3 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Fourth')
    path = os.path.join('Supplementary_files', 'ninja_pv_10.0000_2.3000_uncorrected.csv')
    ghi_curve, temp = read_environmental_data(path)
    a4, b4, c4, d4, e4, f4 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Fifth')
    path = os.path.join('Supplementary_files', 'ninja_pv_11.0000_2.3000_uncorrected.csv')
    ghi_curve, temp = read_environmental_data(path)
    a5, b5, c5, d5, e5, f5 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Sixth')
    path = os.path.join('Supplementary_files', 'South_Africa.csv')
    ghi_curve, temp = read_environmental_data(path)
    a6, b6, c6, d6, e6, f6 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Seventh')
    path = os.path.join('Supplementary_files', 'Angola.csv')
    ghi_curve, temp = read_environmental_data(path)
    a7, b7, c7, d7, e7, f7 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

    logging.info('Eigth')
    path = os.path.join('Supplementary_files', 'CAF.csv')
    ghi_curve, temp = read_environmental_data(path)
    a8, b8, c8, d8, e8, f8 = pv_diesel_hybrid(100, ghi, ghi_curve, temp, tier, 2020, 2030, pv_no, diesel_no)

cProfile.run('profile_hybrids()', sort='tottime')

