#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

from setuptools import setup
import codecs
import re
import os


def rread(fn):
    lfn = os.path.join(os.path.dirname(__file__) or '.', fn)
    return codecs.open(lfn, 'r', 'utf-8').read()

#
# Get version number from __init__py
#
init = rread('dpc/__init__.py')
VERSION = re.search("__version__ = '([^']+)'", init).group(1)

setup(name='dpc',
      version=VERSION,
      description='Daily photo calendar',
      long_description=rread('README.rst'),
      url='https://github.com/svalgaard/daily-photo-calendar',
      author='Jens Svalgaard Kohrt',
      author_email='python@svalgaard.net',
      license='MIT',
      packages=['dpc'],
      zip_safe=False,
      requires=['Pillow'],
      scripts=['dpc-single'],
      keywords='photos calendar',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: End Users/Desktop',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'License :: OSI Approved :: MIT License',
      ])
