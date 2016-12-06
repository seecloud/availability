#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup


def find_subpackages(package):
    packages = []
    for subpackage in find_packages(package):
        packages.append("{0}.{1}".format(package, subpackage))
    return packages


setup(name="availability",
      version="0.1",
      description="Collect cloud services availability data",
      url="https://github.com/seecloud/availability",
      author="<name>",
      author_email="<name>@mirantis.com",
      packages=find_subpackages("availability"),
      platforms='any',
      license='Apache 2.0',
      entry_points={
          "console_scripts": [
              "availability-watcher = availability.watcher:main",
              "availability-api = availability.main:main",
          ],
      })
