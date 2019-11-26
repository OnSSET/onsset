import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

long_description = """
Modified version of the Open Source Spatial Electrification Tool (OnSSET) to serve GEP objectives.
"""

setuptools.setup(
    name='onsset',
    author='Andreas Sahlberg, Alexandros Korkovelos, Dimitrios Mentis, Christopher Arderne, Babak Khavari',
    author_email=' seap@desa.kth.se',
    description='OnSSET model',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/onsset/onsset',
    packages=['onsset'],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=[
        'et-xmlfile',
        'jdcal',
        'numpy',
        'openpyxl',
        'pandas',
        'python-dateutil',
        'pytz',
        'six',
        'xlrd',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)