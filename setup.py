import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

long_description = """
Modified version of the Open Source Spatial Electrification Tool (OnSSET) to serve GEP objectives.
"""

setuptools.setup(
    name='gep_onsset',
    version='2019.0',
    author='KTH dESA',
    author_email=' seap@desa.kth.se',
    description='OnSSET model for GEP',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/global-electrification-platform/gep-onsset',
    packages=['gep_onsset'],
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
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
)