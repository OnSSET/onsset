onsset : Open Source Spatial Electrification Tool
=================================================

[![PyPI version](https://badge.fury.io/py/onsset.svg)](https://badge.fury.io/py/onsset)
[![Build Status](https://travis-ci.com/OnSSET/onsset.svg?branch=master)](https://travis-ci.com/OnSSET/onsset)
[![Coverage Status](https://coveralls.io/repos/github/OnSSET/onsset/badge.svg?branch=master)](https://coveralls.io/github/OnSSET/onsset?branch=master)
[![Documentation Status](https://readthedocs.org/projects/onsset/badge/?version=latest)](https://onsset.readthedocs.io/en/latest/?badge=latest)

# Scope

This repository contains the source code of the Open Source Spatial Electrification Tool
[OnSSET](https://www.linkedin.com/company/onsset-open-source-spatial-electrification-tool/).

OnSSET can be run using interactive Jupyter Notebooks. First, the input file with GIS data extracted for each settlement should be created using the codes in the [OnSSET_GIS_Extraction_notebook repository](https://github.com/OnSSET/OnSSET_GIS_Extraction_notebook).

Next, run the *Calibration.ipynb* to calibrate the start year information.

Finally, run the *OnSSET_Scenarios.ipynb*, or the *OnSSET_Scenarios_MultipleTimeSteps.ipynb* if you want to run the code in multiple time-steps.

## Installation

OnSSET is run using Python, most easily through Jupyter Notebook, but can also be run using another Python IDE.
It is recommended to install OnSSET using Anaconda. 

### Install with the yml-file

1. Download or clone the repository.

2. Open Anaconda prompt. Navigate to the folder where the OnSSET code is installed.

3. Install all the packages required in a new environment called "OnSSET" using: 

```
conda env create -n OnSSET -f onsset_env.yml
```
4. Activate the environment using:
```
conda activate OnSSET
```
5. Finally, to run OnSSET using Jupyter Notebook, run the following command:
```
jupyter notebook
```
   

## Contact
For more information regarding the tool, its functionality and implementation
please visit OnSSET on LinkedIn or go to the [OnSSET forum](https://www.linkedin.com/company/onsset-open-source-spatial-electrification-tool/](https://forum.u4ria.org/c/onsset/)).
