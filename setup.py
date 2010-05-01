#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'TracDocs'
VERSION = '0.3'

setup(
    name=PACKAGE, version=VERSION,
    description="A plugin for RCS-backed documentation",
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
        'tracdocs': [
            'htdocs/*.css',
            'htdocs/*.js',
            'templates/*.html'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'tracdocs.web_ui = tracdocs.web_ui',
        ]
    }
)

