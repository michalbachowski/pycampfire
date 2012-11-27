#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
import unittest
import mox
import logging

# hack for loading modules
import _path
_path.fix()

# event modules
from event import Dispatcher, Event

##
# campfire api modules
#
from campfire.api import Api


class ApiTestCase(unittest.TestCase):
    
    def setUp(self):
        logging.basicConfig()
        self.log = logging.getLogger()
        self.mox = mox.Mox()
        self.listeners = self.mox.CreateMock(Dispatcher)

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_init_require_2_args(self):
        err = False
        try:
            Api()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_require_2_args_1(self):
        err = False
        try:
            Api(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_require_2_args_2(self):
        err = False
        try:
            Api(None, None)
        except TypeError:
            err = True
        except AttributeError:
            pass
        self.assertFalse(err)

    def test_init_allows_3_args(self):
        err = False
        try:
            Api(None, None, 10)
        except TypeError:
            err = True
        except AttributeError:
            pass
        self.assertFalse(err)

    def test_init_allows_3_args_1(self):
        err = False
        try:
            Api(None, None, None, None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_expects_log_to_be_logging_instance(self):
        err = False
        try:
            Api(None, None)
        except AttributeError:
            err = True
        self.assertTrue(err)

    def test_init_expects_cache_size_to_be_int(self):
        err = False
        try:
            Api(self.log, None, 'a')
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_expects_cache_size_to_be_positive(self):
        err = False
        try:
            Api(self.log, None, -1)
        except ValueError:
            err = True
        self.assertTrue(err)

    def test_init_cache_size_can_be_None(self):
        err = False
        try:
            Api(self.log, None, None)
        except:
            err = True
        self.assertFalse(err)

    def test_attach_poller_requires_3_args(self):
        a = Api(self.log, None)
        err = False
        try:
            a.attach_poller()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_attach_poller_requires_3_args_1(self):
        a = Api(self.log, None)
        err = False
        try:
            a.attach_poller(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_attach_poller_requires_3_args_2(self):
        a = Api(self.log, None)
        poller = 'abc'
        err = False
        try:
            a.attach_poller(None, poller)
        except TypeError:
            err = True
        self.assertFalse(err)
        self.assertTrue(poller in [c for (c, u) in a.pollers if  c == poller])

    def test_attach_poller_requires_3_args_3(self):
        a = Api(self.log, None)
        poller = 'abc'
        err = False
        try:
            a.attach_poller(None, poller, None)
        except TypeError:
            err = True
        self.assertFalse(err)
        self.assertTrue(poller in [c for (c, u) in a.pollers if  c == poller])

    def test_attach_does_not_check_callback_type(self):
        err = False
        a = Api(self.log, None)
        try:
            a.attach_poller(None, 'abc')
        except:
            err = True
        self.assertFalse(err)

    def test_poller_must_by_callable(self):
        # prepare
        a = Api(self.log, self.listeners)
        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        def side_effect(a, b):
            e.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect).AndReturn(e)
        # called when notifying pollers
        e2 = self.mox.CreateMock(Event)
        e2.processed = False
        e2.return_value = None
        def side_effect2(a, b):
            e2.return_value = b
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e2)
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        
        self.mox.ReplayAll()

        # test
        a.attach_poller(None, 'a')
        err = False
        try:
            a.recv('a', 'b', 'c')
        except TypeError:
            err = True

        # verify
        self.mox.VerifyAll()
        self.assertTrue(err)

    def test_poller_is_called_on_recv(self):
        # prepare
        a = Api(self.log, self.listeners)
        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        def side_effect(a, b):
            e.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect).AndReturn(e)
        # called when notifying pollers
        e2 = self.mox.CreateMock(Event)
        e2.processed = False
        e2.return_value = None
        def side_effect2(a, b):
            e2.return_value = b
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e2)
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        # called when sending response to poller
        p = self.mox.CreateMockAnything()
        p(mox.IsA(list))
        
        self.mox.ReplayAll()

        # test
        err = False
        a.attach_poller(None, p)
        try:
            a.recv('a', 'b', 'c')
        except TypeError:
            err = True

        # verify
        self.mox.VerifyAll()
        self.assertFalse(err)



if "__main__" == __name__:
    unittest.main()
