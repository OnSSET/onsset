"""
The onsset package contains the following modules:

 - onsset.py : main functions of the model
 - runner.py : runner is used to calibrate inputs and specify scenario runs
"""

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

from .onsset import *
