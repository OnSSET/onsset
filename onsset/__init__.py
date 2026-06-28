"""
The onsset package contains the following modules:

 - onsset.py : main functions of the model
 - runner.py : runner is used to calibrate inputs and specify scenario runs
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("onsset")
except PackageNotFoundError:
    pass

from .onsset import *
