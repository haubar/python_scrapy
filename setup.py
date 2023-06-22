# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '3.2',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = carpost.settings']},
)
