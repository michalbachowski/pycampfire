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
# event modules
#
from event import Dispatcher, Listener


class ListenerTestCase(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.dispatcher = self.mox.CreateMock(Dispatcher)
    
    def tearDown(self):
        self.mox.UnsetStubs()

    def test_register_uses_mapping(self):
        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.mapping().AndReturn([('foo', None, 2)])

        # prepare dispatcher
        self.dispatcher.attach('foo', None, 2)
        self.mox.ReplayAll()

        # test
        listener.register(self.dispatcher)

        # verify
        self.mox.VerifyAll()


if "__main__" == __name__:
    unittest.main()
