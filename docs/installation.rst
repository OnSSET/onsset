Software installation
=====================

Requirements
************



**Python - Anaconda package**

OnSSET is written in python, an open source programming language used widely in many applications.
Python is a necessary requirement for the OnSSET tool to work.
Programming in python usually relies on the usage of pre-defined functions
that can be found in the so called modules.
In order to work with OnSSET, certain modules need to be installed/updated.
The easiest way to do so is by installing Anaconda, a package that contains a wide range of
Python packages in one bundle.
Anaconda includes many of the Python packages required to run OnSSET successfully.

**Jupyter notebook (via Anaconda)**

Jupyter notebook is a console-based, interactive computing approach providing a web-based application suitable for capturing the whole computation process: developing, documenting, and executing code, as well as communicating the results. OnSSET is most easily run using Jupyter Notebook, although users that need to run many scenarios can do so using an IDE instead.

**GitHub**

GitHub is a web-based Git repository hosting service. It provides access control and several collaboration features such as bug tracking, feature requests, task management, and wikis for every project. OnSSET is an open source tool therefore the code behind it is open and freely accessible to any user through GitHub. A GitHub account is not required to download the code, but will allow you to propose changes, modifications and upgrades to the existing code. Access the repository on `Github <https://github.com/OnSSET>`_.

Software installation and setup
*******************************

1. Download **Anaconda** `here <https://www.continuum.io/downloads>`_ and install.

* Please make sure that you download the version that is compatible with your operating system
  (Windows/MacOS/Linux - In case you run Windows open the *Windows Control Panel*,
  go to *System and Security  System* and check e.g. Windows 32-bit or 64-bit).
* Following the installation process make sure that you click on the option “Add Python X.X to PATH”.
  Also by choosing to customize the installation, you can specify the directory of your
  preference (suggest something convenient e.g. C:/Python3/..).

* After the installation you can use the Anaconda command line (search for “Anaconda Prompt”)
  to run python. It should work by simply writing “python” and pressing enter,
  since the path has already been included in the system variables.
  In case this doesn’t work, you can either navigate to the specified directory and write “python” there,
  or add the directory to the PATH by editing the
  `environment variables <https://www.computerhope.com/issues/ch000549.htm>`_.

3. Download the OnSSET code from **GitHub** `here <https://github.com/onsset/OnSSET>`_.


4. Open Anaconda prompt. Navigate to the folder where the OnSSET code is installed.

5. Install all the packages required in a new environment called "OnSSET" using:

```
conda env create -n OnSSET -f onsset_env.yml
```

6. Activate the environment using:

```
conda activate OnSSET
```

7. Finally, to run OnSSET using Jupyter Notebook, run the following command which will open Jupyter Notebook using the browser as an interface:

```
jupyter notebook
```

**Python Interfaces - Integrated Development Environment (IDEs)**

**PyCharm**

Integrated Development Environments are used in order to ease the programming process when multiple or long scripts are required. There are plenty of IDEs developed for Python. KTH dESA has been using PyCharm as the standard IDE to run OnSSET.


**QGIS**

OnSSET is a spatial electrification tool and as such highly relies on the usage of
Geographic Information Systems (GIS). While OnSSET itself is run entirely using Python/Jupyter Notebook, a GIS software
can be useful to examine geospatial input data and to visualize and analyze the results.
While there are no specific requirements, training material and descriptions are typically based on QGIS, which is freely available

.. note:: In order to assure that the QGIS section of OnSSET functions correctly make sure to download the lastest long-term release of QGIS (version 3.40 as of 2025)

Download QGIS for free from the official `QGIS website <https://qgis.org/download/>`_.

Additional Info
***************
