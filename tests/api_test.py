#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
import unittest
import mox
import logging
from functools import partial

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

    def test_detach_poller_requires_2_args(self):
        a = Api(self.log, None)
        err = False
        try:
            a.detach_poller()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_detach_poller_requires_2_args_1(self):
        a = Api(self.log, None)
        poller = 'abc'
        err = False
        try:
            a.detach_poller(poller)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_detach_poller_checks_object_id(self):
        a = Api(self.log, None)
        poller = 'abc'
        a.attach_poller(None, poller)
        a.detach_poller('abc')
        self.assertFalse(poller in [c for (c, u) in a.pollers if  c == poller])

    def test_detach_poller_checks_object_id_1(self):
        a = Api(self.log, None)
        class Poller(object):
            def poller(msg):
                pass
        poller1 = Poller().poller
        poller2 = Poller().poller
        a.attach_poller(None, poller1)
        a.detach_poller(poller2)
        self.assertTrue(poller1 in [c for (c, u) in a.pollers if  c == poller1])

    def test_detach_poller_checks_object_id_2(self):
        a = Api(self.log, None)
        class Poller(object):
            def poller(msg):
                pass
        poller1 = Poller().poller
        poller2 = Poller().poller
        a.attach_poller(None, poller1)
        a.attach_poller(None, poller2)
        a.detach_poller(poller2)
        self.assertTrue(poller1 in [c for (c, u) in a.pollers if  c == poller1])
        self.assertFalse(poller2 in [c for (c, u) in a.pollers \
            if  c == poller2])

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

    def test_run(self):
        # prepare
        a = Api(self.log, self.listeners)
        pollers = []

        def side_effect1(e, a, b):
            b['tmp'] = a['user']
            e.return_value = b

        def side_effect(e, a, b):
            e.return_value = b

        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when notifying pollers
        for i in xrange(1, 3):
            e2 = self.mox.CreateMock(Event)
            e2.processed = False
            e2.return_value = None
    
            self.listeners.filter(mox.IsA(Event), mox.IsA(dict)\
                ).WithSideEffects(partial(side_effect1, e2)).AndReturn(e2)
            self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
            
            # called when sending response to poller
            p = self.mox.CreateMockAnything()
            p([{'tmp': i, 'data': {'message': 'a', 'args': 'c', 'from': None}, \
                'id': mox.IsA(str)}])
            a.attach_poller(i, p)

        self.mox.ReplayAll()

        # test
        a.recv('a', 'b', 'c')

        # verify
        self.mox.VerifyAll()
    
    def test_init_sends_chat_init_event(self):
        # prepare
        out = {'route': None}
        def side_effect(e):
            out['route'] = e.name

        # called when initializing object
        self.listeners.notify(mox.IsA(Event)).WithSideEffects(side_effect)

        self.mox.ReplayAll()

        # test
        a = Api(self.log, self.listeners)
        a.init()

        # verify
        self.mox.VerifyAll()
        self.assertEqual('chat.init', out['route'])

    def test_shutdown_sends_event_and_closes_connections(self):
        # prepare
        a = Api(self.log, self.listeners)
        
        out = {'route': None}
        def side_effect(e):
            out['route'] = e.name

        self.listeners.notify(mox.IsA(Event)).WithSideEffects(side_effect)
        
        # called when shutting down pollers
        for i in xrange(1, 3):
            p = self.mox.CreateMockAnything()
            p(mox.IsA(list))
            a.attach_poller(i, p)

        self.mox.ReplayAll()

        # test
        a.shutdown()

        # verify
        self.mox.VerifyAll()
        self.assertEqual('chat.shutdown', out['route'])

if "__main__" == __name__:
    unittest.main()
