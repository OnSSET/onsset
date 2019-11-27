onsset
=================================

[![PyPI version](https://badge.fury.io/py/gridfinder.svg)](https://test.pypi.org/project/gep-onsset/)
[![Build Status](https://travis-ci.com/OnSSET/onsset.svg?branch=master)](https://travis-ci.com/OnSSET/onsset)
[![Documentation Status](https://readthedocs.org/projects/onsset/badge/?version=latest)](https://onsset.readthedocs.io/en/latest/?badge=latest)

Documentation: https://onsset.readthedocs.io/en/latest/index.html#

# Scope

This repository contains the source code of the Open Source Spatial Electrification Tool ([OnSSET](http://www.onsset.org/)). The repository also includes sample test files available in ```.\test_data``` and sample output files available in ```.\sample_output```.

## Installation

**Requirements**

OnSSET requires Python > 3.5 with the following packages installed:
- et-xmlfile
- jdcal
- numpy
- openpyxl
- pandas
- python-dateutil
- pytz
- six
- xlrd


**Install with pip**

```
pip install onsset
```

**Install from GitHub**

Download or clone the repository and install the package in `develop` (editable) mode:

```
git clone https://github.com/onsset/onsset.git
cd gep-onsset
python setup.py develop
```

The use of GEP generator requires also installation of
- IPython
- jupyter
- matplotlib
- seaborn

## Contact
For more information regarding the tool, its functionality and implementation please visit https://www.onsset.org or contact the development team at seap@desa.kth.se.
