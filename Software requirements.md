#ONSSET Software requirements

##ArcGIS
**ONSSET** is a spatial electrification tool and as such relies highly on the usage of Geographic Information Systems (GIS). 
A GIS environment is therefore necessary for two main reasons:
a)	Extract trivial characteristics for the electrification analysis from GIS layers and combine them all together in a format easy to
read by the python code (a csv file with all the attributes per population point). 
b)	Visualize the final results in maps.
In the current stage, **ONSSET** relies on ArcGIS however, any alternative GIS environment can be used (e.g. QGIS or GRASS).

##Python - Anaconda package
**ONSSET** is written in python, an open source programming language used widely in many applications. Python is a necessary requirement 
for **ONSSET**. 
Programming in python relies usually on the usage of pre-defined functions that can be found in the so called modules.
In order to work with **ONSSET**, certain modules need to be installed/updated. The easiest way to do so is by installing Anaconda, 
a package that contains various useful modules. Anaconda can be downloaded for free from [here] 
(https://www.continuum.io/anaconda-overview). 
Please make sure that you download the version that is compatible with your operating system (e.g. Windows 32-bit).
After the installation you can use the Anaconda command line to run python. Anaconda includes all the modules required to run **ONSSET**. 

###Python Interfaces
1.	**Integrated Development Environment (IDEs)**
Integrated Development Environment programs are used in order to ease the programming process when multiple or long scripts are required.
There are plenty IDEs developed for Python (you can find a few [here]
(http://noeticforce.com/best-python-ide-for-programmers-windows-and-mac)). 
KTH dESA uses PyCharm as the standard IDE to run **ONSSET**. 
It can be downloaded [here] (https://www.jetbrains.com/pycharm/).

2.	**Jupyter notebook**
Jupyter notebook is a console-based, interactive computing approach providing a web-based application suitable for capturing the whole 
computation process: developing, documenting, and executing code, as well as communicating the results. 
Jupyter notebook is used for the online onset interface, recommended for small analyses and exploring code and results.

##GitHub
GitHub is a web-based Git repository hosting service. It provides access control and several collaboration features such as bug tracking,
feature requests, task management, and wikis for every project. **ONSSET** is an open source tool therefore the code behind it is open and
freely accessible to any user. The code behind **ONSSET** tool is called “**PyOnSSET**” and is available in KTH dESA’s [Github space] 
(https://github.com/KTH-dESA/PyOnSSET). A GitHub account will allow you to propose changes, modifications and upgrades to the existing
code.

###Additional Info
Basic navigating commands for DOS (cmd) can be found [here](https://community.sophos.com/kb/en-us/13195).

###Problems with running python/Anaconda
Before installing Python or Anaconda, please identify the version that is suitable for your operating system 
(e.g. _Python 3.5.2_ for Windows etc.). Following the installation process make sure that you click on the option
“_Add Python X.X to PATH_”. Also by choosing to customize the installation, you can specify the directory of your preference
(suggest something convenient e.g. _C:/Python35/.._). 

You can test if python is installed correctly through the command line for Windows. It should work by simply writing python and pressing
"Enter" since the path has already been included in the system variables. In case this doesn’t work you can either navigate to the specified directory
and write python there or _add the directory to the path_ by editing the “environment variables”.  
In case you want to install/update certain modules with Anaconda, you have (at least) three options.
1. Use Anaconda
On the command line of Anaconda you can type conda install <package name> and the installation/update will go through automatically.

Problems with Anacoda rights while updating can be found [here]
(http://stackoverflow.com/questions/37766873/anaconda-on-ubuntu-error-in-permission-to-update-using-conda-command)

2. Use Pip
Pip is the easiest way to install/update packages. Using the command line, navigate to your python directory 
(e.g. _C:\...Python35\scripts_) and then type pip and enter. This will show you all the possible choices you have within pip.
In order to update pip itself you can just type: _pip install --upgrade pip_

![upgrade pip](/resources/pip1.png "upgrade pip")

 
In order to install any additional module required you can type:
Examples: _pip install scipy_, _pip install matplotlib_

![install new module](/resources/pip2.png "install new module")
 
You can find more in [here] (https://www.youtube.com/watch?v=FKwicZF7xNE).

3. Manual installation
In case pip doesn’t work, you can install the required modules manually. More information can be found [here] (https://www.youtube.com/watch?v=jnpC_Ib_lbc). 
Python extension packages in wheel file formats can be found [here] (http://www.lfd.uci.edu/~gohlke/pythonlibs/).

