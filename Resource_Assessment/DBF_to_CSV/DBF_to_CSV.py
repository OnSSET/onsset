# This piece of code converts a dbf file into a simple csv file. It runs with python 3.5>= and requires the following modules to be installed
# simpledbf is installed through conda using: conda install -c rnelsonchem simpledbf or via pip install using: pip install simpledbf

import pandas as pd
import numpy as np
import logging
import time
from simpledbf import Dbf5

start_time = time.time()

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

logging.info('Converting the dbf into a dataframe')
dbf = Dbf5("Madagascar_10kmSettlements.dbf")
df = dbf.to_dataframe()

logging.info("Exporting dataframe to the csv")
df.to_csv("{c}.csv".format(c="Madagascar_10kmSettlements"))

print("It took {time:0.2f} min to run".format(time = (time.time() - start_time)/60))
