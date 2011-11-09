#!/usr/bin/env python
#
# Copyright Oscar Benjamin 2011 under new BSD license

import os.path
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension('sode.cysode', [os.path.join('sode', 'cysode.pyx')])]

setup(
    name = 'sode',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
)
