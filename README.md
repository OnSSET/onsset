gep_onsset
=================================

[![PyPI version](https://badge.fury.io/py/gridfinder.svg)](https://test.pypi.org/project/gep-onsset/)  [![Build Status](https://travis-ci.org/global-electrification-platform/gep-onsset.svg?branch=master)](https://travis-ci.org/global-electrification-platform/gep-onsset) [![Documentation Status](https://readthedocs.org/projects/gep-onsset/badge/?version=latest)](https://gep-onsset.readthedocs.io/en/latest/?badge=latest)

Documentation: https://gep-onsset.readthedocs.io/en/latest/index.html#

# Scope

This repository contains the source code of the Open Source Spatial Electrification Tool ([OnSSET](http://www.onsset.org/)) as used to inform [electrification investment outlooks](http://gep-explorer.surge.sh/) for the Global Electrification Platform. The repository also includes sample test files available in ```.\test_data``` and sample output files available in ```.\sample_output```. More information on how to replicate, run and interprate results are available in [user's guide.](https://gep-onsset.readthedocs.io/en/latest/index.html#)

## Installation

**Requirements**

gons_test requires Python >= 3.5 with the following packages installed:
- et-xmlfile>=1.0
- jdcal>=1.4
- numpy>=1.16
- openpyxl>=2.6
- pandas>=0.24
- python-dateutil>=2.8
- pytz==2019.1
- six>=1.12
- xlrd>=1.2


**Install with pip**

```
python -m pip install -i https://test.pypi.org/simple/ gep-onsset
```

**Install from GitHub**

Download or clone the repository and install the required packages (preferably in a virtual environment):

```
git clone https://github.com/global-electrification-platform/gep-onsset.git
cd gep-onsset
pip install -r requirements.txt
```

The use of GEP generator requires also installation of 
- IPython
- jupyter
