#!/usr/bin/env python

import os.path
from distutils.core import setup

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'TracDocs',
    version = '0.3.1',
    description="A Trac plugin for RCS-backed documentation",
    long_description = read('README.md'),
    author = "John Benediktsson",
    author_email = 'mrjbq7@gmail.com',
    url = "http://github.com/trac-hacks/tracdocs",
    download_url = "http://github.com/trac-hacks/tracdocs/zipball/master#egg=TracDocs-0.3",
    packages=['tracdocs'],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Framework :: Trac",
        "License :: OSI Approved :: BSD License",
    ],
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
    },
    dependency_links = ['http://github.com/trac-hacks/tracdocs/zipball/master#egg=TracDocs-0.3']
)

