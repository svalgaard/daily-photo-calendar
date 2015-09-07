#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

from setuptools import setup
import codecs
import re
import os

#
# Get version number from __init__py
#
init = os.path.join(os.path.dirname(__file__) or '.', 'dpc', '__init__.py')
init = codecs.open(init, 'r', 'utf-8').read()
VERSION = re.search("__version__ = '([^']+)'", init).group(1)

setup(name='dpc',
      version=VERSION,
      description='Daily photo calendar',
      url='https://github.com/svalgaard/daily-photo-calendar',
      author='Jens Svalgaard Kohrt',
      author_email='python@svalgaard.net',
      license='MIT',
      packages=['dpc'],
      zip_safe=True,
      requires=["Pillow"],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: End Users/Desktop',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License',
          
      ])
