#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python packaging."""
import os

from setuptools import setup


def read_relative_file(filename):
    """Returns contents of the given file, which path is supposed relative
    to this module."""
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read().strip()


NAME = 'macman'
DESCRIPTION = "Manage multiple VMs from one place."
README = read_relative_file('README')
VERSION = read_relative_file('VERSION')
KEYWORDS = ['VirtualBox', 'Vagrant']
PACKAGES = [NAME]
REQUIRES = ['setuptools']
ENTRY_POINTS = {
    'console_scripts': [
        'macman = %s:main' % NAME,
    ]
}


if __name__ == '__main__':  # Don't run setup() when we import this module.
    setup(name=NAME,
          version=VERSION,
          description=DESCRIPTION,
          long_description=README,
          classifiers=['License :: OSI Approved :: BSD License',
                       'Development Status :: 3 - Alpha',
                       'Programming Language :: Python :: 2.7'],
          keywords=' '.join(KEYWORDS),
          author='Benoît Bryon',
          author_email='benoit@marmelune.net',
          url='https://github.com/novagile/macman',
          license='BSD',
          packages=PACKAGES,
          include_package_data=True,
          zip_safe=False,
          install_requires=REQUIRES,
          entry_points=ENTRY_POINTS)
