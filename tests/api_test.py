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
        # called when initializing object
        self.listeners.notify(mox.IsA(Event))
        self.api = Api(self.log, self.listeners)

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
        err = False
        self.api.init()
        try:
            self.api.attach_poller()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_attach_poller_requires_3_args_1(self):
        err = False
        self.api.init()
        try:
            self.api.attach_poller(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_attach_poller_requires_3_args_2(self):
        poller = 'abc'
        err = False
        self.api.init()
        try:
            self.api.attach_poller(None, poller)
        except TypeError:
            err = True
        self.assertFalse(err)
        self.assertTrue(poller in [c for (c, u) in self.api.pollers \
            if  c == poller])

    def test_attach_poller_requires_3_args_3(self):
        poller = 'abc'
        err = False
        self.api.init()
        try:
            self.api.attach_poller(None, poller, None)
        except TypeError:
            err = True
        self.assertFalse(err)
        self.assertTrue(poller in [c for (c, u) in self.api.pollers \
            if  c == poller])

    def test_attach_does_not_check_callback_type(self):
        err = False
        self.api.init()
        try:
            self.api.attach_poller(None, 'abc')
        except:
            err = True
        self.assertFalse(err)

    def test_poller_must_by_callable(self):
        # prepare
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
        self.api.init()

        # test
        self.api.attach_poller(None, 'a')
        err = False
        try:
            self.api.recv('a', 'b', 'c')
        except TypeError:
            err = True

        # verify
        self.mox.VerifyAll()
        self.assertTrue(err)

    def test_detach_poller_requires_2_args(self):
        err = False
        try:
            self.api.detach_poller()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_detach_poller_requires_2_args_1(self):
        poller = 'abc'
        err = False
        self.api.init()
        try:
            self.api.detach_poller(poller)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_detach_poller_checks_object_id(self):
        poller = 'abc'
        self.api.init()
        self.api.attach_poller(None, poller)
        self.api.detach_poller('abc')
        self.assertFalse(poller in [c for (c, u) in self.api.pollers \
            if  c == poller])

    def test_detach_poller_checks_object_id_1(self):
        class Poller(object):
            def poller(msg):
                pass
        poller1 = Poller().poller
        poller2 = Poller().poller
        self.api.init()
        self.api.attach_poller(None, poller1)
        self.api.detach_poller(poller2)
        self.assertTrue(poller1 in [c for (c, u) in self.api.pollers \
            if  c == poller1])

    def test_detach_poller_checks_object_id_2(self):
        class Poller(object):
            def poller(msg):
                pass
        poller1 = Poller().poller
        poller2 = Poller().poller
        self.api.init()
        self.api.attach_poller(None, poller1)
        self.api.attach_poller(None, poller2)
        self.api.detach_poller(poller2)
        self.assertTrue(poller1 in [c for (c, u) in self.api.pollers \
            if  c == poller1])
        self.assertFalse(poller2 in [c for (c, u) in self.api.pollers \
            if  c == poller2])

    def test_poller_is_called_on_recv(self):
        # prepare
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
        self.api.init()

        # test
        err = False
        self.api.attach_poller(None, p)
        try:
            self.api.recv('a', 'b', 'c')
        except TypeError:
            err = True

        # verify
        self.mox.VerifyAll()
        self.assertFalse(err)

    def test_run(self):
        # prepare
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

        # called when attaching and notifying pollers
        for i in xrange(0, 2):
            e2 = self.mox.CreateMock(Event)
            e2.processed = False
            e2.return_value = None
        
            # called when sending response to poller
            self.listeners.filter(mox.IsA(Event), mox.IsA(dict)\
                ).WithSideEffects(partial(side_effect1, e2)).AndReturn(e2)
            self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
            
            p = self.mox.CreateMockAnything()
            p([{'tmp': i, 'data': {'message': 'a', 'args': 'c', 'from': None}, \
                'id': mox.IsA(str)}])
            pollers.append(p)

        self.mox.ReplayAll()
        
        self.api.init()
        for (i, p) in enumerate(pollers):
            self.api.attach_poller(i, p)

        # test
        self.api.recv('a', 'b', 'c')

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
        self.api.init()

        # test
        a = Api(self.log, self.listeners)
        a.init()

        # verify
        self.mox.VerifyAll()
        self.assertEqual('chat.init', out['route'])

    def test_shutdown_sends_event_and_closes_connections(self):
        # prepare
        pollers = []
        out = {'route': None}
        def side_effect(e):
            out['route'] = e.name

        self.listeners.notify(mox.IsA(Event)).WithSideEffects(side_effect)
        
        # called when shutting down pollers
        for i in xrange(0, 2):
            p = self.mox.CreateMockAnything()
            p(mox.IsA(list))
            pollers.append(p)

        self.mox.ReplayAll()
        self.api.init()
        
        for (i, p) in enumerate(pollers):
            self.api.attach_poller(i, p)

        # test
        self.api.shutdown()

        # verify
        self.mox.VerifyAll()
        self.assertEqual('chat.shutdown', out['route'])

if "__main__" == __name__:
    unittest.main()
