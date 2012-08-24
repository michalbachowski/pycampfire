#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
import unittest
import mox

# hack for loading modules
import _path
_path.fix()

##
# campfire api modules
#
from campfire import api


class ApiTestCase(unittest.TestCase):
    pass

if "__main__" == __name__:
    unittest.main()
