#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='flask-appconfig',
    version='0.8',
    description=('Configures Flask applications in a canonical way. Also auto-'
                 'configures Heroku. Aims to standardize configuration.'),
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/flask-appconfig',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['flask', 'six'],
    entry_points={
        'console_scripts': [
            'flaskdev = flask_appconfig.cmd:main_flaskdev',
        ],
    }
)
