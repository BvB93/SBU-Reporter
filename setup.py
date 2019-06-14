#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# To update the package version number, edit sbu/__version__.py
version = {}
with open(os.path.join(here, 'sbu', '__version__.py')) as f:
    exec(f.read(), version)

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='SBU-Reporter',
    version=version['__version__'],
    description=(
        'Tools for collection, formating and reporting SBU usage on the SURFsara HPC clusters.'
    ),
    long_description=readme + '\n\n',
    author='Bas van Beek',
    author_email='b.f.van.beek@vu.nl',
    url='https://github.com/BvB93/sbu-reporter',
    packages=[
        'sbu',
        'sbu.data'
    ],
    package_dir={'sbu': 'sbu'},
    package_data={'sbu': ['data/*.yaml']},
    include_package_data=True,
    entry_points={'console_scripts': [
        'get_sbu=sbu.entry_points:main_sbu'
    ]},
    license="GNU General Public License v3 or later",
    zip_safe=False,
    keywords=[
        'python-3'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring'
        'License :: OSI Approved :: MIT Licence',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only'
    ],
    test_suite='tests',
    install_requires=[
        'pyyaml>=5.1',
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn'
    ],
    setup_requires=[
        'pytest-runner',
        'sphinx',
        'sphinx_rtd_theme',
        'recommonmark'
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pycodestyle'
    ],
    extras_require={
        'test': ['pytest', 'pytest-cov', 'pytest-mock', 'pycodestyle'],
        'doc': ['sphinx', 'sphinx_rtd_theme', 'sphinx_autodoc_typehints'],
    }
)
