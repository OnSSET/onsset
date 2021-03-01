from os import path

import setuptools

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

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
        'notebook',
        'seaborn',
        'scipy',
        'matplotlib',
        'keplergl',
        'tk',
        'geopandas'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
