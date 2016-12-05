#!/usr/bin/env python

from setuptools import setup

setup(name="availability",
      version="0.1",
      description="Collect cloud services availability data",
      url="https://github.com/seecloud/availability",
      author="<name>",
      author_email="<name>@mirantis.com",
      packages=["availability"],
      entry_points={
          "console_scripts": [
              "availability-watcher = availability.watcher:main",
              "availability-api = availability.main:main",
          ],
      })
