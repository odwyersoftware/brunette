#!/usr/bin/env python
# -*- coding: utf-8 -*

import os
from codecs import open

from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

with open('requirements-dev.txt') as f:
    dev_install_requires = [
        l
        for l in f.read().splitlines()
        if not (l.startswith('-r') or l.startswith('#'))
    ]

with open('README.md', 'r', encoding='utf-8') as rm_file:
    readme = rm_file.read()

with open('HISTORY.md', 'r', encoding='utf-8') as hist_file:
    history = hist_file.read()

setup(
    name='brunette',
    version='0.2.1',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    description='Google/Excel Sheets API Python.',
    author="O'Dwyer Software",
    author_email='hello@odwyer.software',
    url='https://github.com/ODwyerSoftware/brunette',
    license='Apache 2.0',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    extras_require={'dev': dev_install_requires},
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ],
    entry_points={'console_scripts': ['brunette = brunette.brunette:main',]},
)
