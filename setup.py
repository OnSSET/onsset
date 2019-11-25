import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

long_description = """
Modified version of the Open Source Spatial Electrification Tool (OnSSET) to serve GEP objectives.
"""

setuptools.setup(
    name='onsset',
    version='2019.0',
    author='Andreas Sahlberg, Alexandros Korkovelos, Dimitrios Mentis, Christopher Arderne, Babak Khavari',
    author_email=' seap@desa.kth.se',
    description='OnSSET model',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/onsset/onsset',
    packages=['onsset'],
    install_requires=[
        'et-xmlfile>=1.0',
        'jdcal>=1.4',
        'numpy>=1.16',
        'openpyxl>=2.6',
        'pandas>=0.24',
        'python-dateutil>=2.8',
        'pytz==2019.1',
        'six>=1.12',
        'xlrd>=1.2',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)