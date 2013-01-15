#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
import time
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
from campfire.api import Api, ChatReinitializationForbiddenError, \
    UninitializedChatError, AuthError


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

    def test_attach_poller_doest_not_attach_poller_when_any_messages_are_found(self):
        # prepare
        pollers = []
        
        def side_effect2(a, b):
            e1.return_value = b
        
        def side_effect1(e, a, b):
            b['tmp'] = a['user']
            e.return_value = b

        def side_effect(e, a, b):
            e.return_value = b

        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when preparing response to request
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e1)

        # called when attaching and notifying pollers
        for i in xrange(0, 2):
            e2 = self.mox.CreateMock(Event)
            e2.processed = False
            e2.return_value = None
        
            # called when sending response to poller
            self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
            self.listeners.filter(mox.IsA(Event), mox.IsA(dict)\
                ).WithSideEffects(partial(side_effect1, e2)).AndReturn(e2)
            
            p = self.mox.CreateMockAnything()
            p([{'tmp': i, 'text': 'a', 'args': 'c', 'date': mox.IsA(int), \
                'from': 'b', 'id': mox.IsA(str)}])
            pollers.append(p)

        self.mox.ReplayAll()
        
        self.api.init()

        # test
        self.api.recv('a', 'b', 'c')

        for (i, p) in enumerate(pollers):
            self.api.attach_poller(i, p)

        # verify
        self.mox.VerifyAll()

    def test_poller_will_not_receive_messages_that_should_not_be_returned(self):
        def side_effect2(a, b):
            e1.return_value = b

        def side_effect1(e, a, b):
            e.return_value = b

        def side_effect(e, a, b):
            e.return_value = b

        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when attaching and notifying pollers
        e2 = self.mox.CreateMock(Event)
        e2.processed = True
        e2.return_value = None
    
        # called when sending response to poller
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).AndReturn(e2)
        
        p = self.mox.CreateMockAnything()
        i = 'usr'

        # called when preparing response to request
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e1)

        self.mox.ReplayAll()
        
        self.api.init()

        # test
        self.api.recv('a', 'b', 'c')
        self.api.attach_poller(i, p)
        
        # verify
        self.mox.VerifyAll()
    
    def test_poller_will_not_receive_messages_that_are_too_old(self):
        def side_effect2(a, b):
            e1.return_value = b

        def side_effect1(e, a, b):
            e.return_value = b

        def side_effect(e, a, b):
            b['date'] = time.time() - 365 * 24 * 60 * 60 # year ago
            e.return_value = b

        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when attaching and notifying pollers
        e2 = self.mox.CreateMock(Event)
        e2.processed = True
        e2.return_value = None
    
        # called when sending response to poller
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).AndReturn(e2)
        
        p = self.mox.CreateMockAnything()
        i = 'usr'

        self.mox.ReplayAll()
        
        self.api.init()

        # test
        self.api.recv('a', 'b', 'c')
        self.api.attach_poller(i, p)
        
        # verify
        self.mox.VerifyAll()

    def test_attach_poller_attaches_poller_when_cursor_indicates_last_message(self):
        # prepare
        pollers = []
        msgs = []
        
        def side_effect3(m):
            msgs.extend(m)
        
        def side_effect2(a, b):
            e1.return_value = b

        def side_effect1(e, a, b):
            b['tmp'] = a['user']
            e.return_value = b

        def side_effect(e, a, b):
            e.return_value = b

        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when attaching and notifying pollers
        e2 = self.mox.CreateMock(Event)
        e2.processed = False
        e2.return_value = None
    
        # called when sending response to poller
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)\
            ).WithSideEffects(partial(side_effect1, e2)).AndReturn(e2)
        
        p = self.mox.CreateMockAnything()
        i = 'usr'
        p([{'tmp': i, 'text': 'a', 'args': 'c', 'date': mox.IsA(int), \
            'from': 'b', 'id': mox.IsA(str)}]).WithSideEffects(side_effect3)
        pollers.append(p)

        p1 = self.mox.CreateMockAnything()

        # called when preparing response to request
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e1)

        self.mox.ReplayAll()
        
        self.api.init()
        self.api.attach_poller(i, p)

        # test
        self.api.recv('a', 'b', 'c')
        
        self.api.attach_poller('usr', p1, msgs[0]['id'])

        # verify
        self.mox.VerifyAll()

    def test_attach_poller_does_not_check_callback_type(self):
        err = False
        self.api.init()
        try:
            self.api.attach_poller(None, 'abc')
        except:
            err = True
        self.assertFalse(err)
    
    def test_attach_poller_raises_exception_when_chat_is_not_initialized(self):
        err = False
        try:
            self.api.attach_poller(None, None, None)
        except UninitializedChatError:
            err = True
        self.assertTrue(err)

    def test_poller_must_by_callable(self):
        # prepare
        # called when message is received
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
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
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e2)
        
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
    
    def test_detach_poller_raises_exception_when_chat_is_not_initialized(self):
        err = False
        try:
            self.api.detach_poller(None)
        except UninitializedChatError:
            err = True
        self.assertTrue(err)
    
    def test_recv_raises_exception_when_chat_is_not_initialized(self):
        err = False
        try:
            self.api.recv(None, None, None)
        except UninitializedChatError:
            err = True
        self.assertTrue(err)

    def test_poller_is_called_on_recv(self):
        # prepare
        # called when message is received (recv())
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        def side_effect(a, b):
            e.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect).AndReturn(e)
        # called when notifying pollers (filter output)
        e2 = self.mox.CreateMock(Event)
        e2.processed = False
        e2.return_value = None
        def side_effect2(a, b):
            e2.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e2)
        # called when sending response to poller
        p = self.mox.CreateMockAnything()
        p(mox.IsA(list))
        # called before sending response to poller
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        def side_effect1(a, b):
            e1.return_value = b
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect1).AndReturn(e1)
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
    
    def test_recv_raises_exception_when_auth_chat_event_was_not_processed(self):
        e = self.mox.CreateMock(Event)
        e.processed = False
        e.return_value = None
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.mox.ReplayAll()

        self.api.init()
        try:
            self.api.recv(None, None, None)
        except AuthError:
            err = True
        
        self.mox.VerifyAll()
        self.assertTrue(err)
    
    def test_when_event_read_prevent_is_processed_message_will_be_ignored(self):
        # prepare
        # called when message is received (recv())
        e = self.mox.CreateMock(Event)
        e.processed = True
        e.return_value = None
        e.__getitem__('response').AndReturn({})
        def side_effect(a, b):
            e.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect).AndReturn(e)
        # called when notifying pollers (filter output)
        e2 = self.mox.CreateMock(Event)
        e2.processed = True
        e2.return_value = None
        def side_effect2(a, b):
            e2.return_value = b
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
        # called before sending response to sender (_prepare_response())
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        def side_effect1(a, b):
            e1.return_value = b
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect1).AndReturn(e1)
        self.mox.ReplayAll()
        self.api.init()

        # test
        err = False
        self.api.attach_poller(None, lambda f: f)
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
        e.__getitem__('response').AndReturn({})
        self.listeners.notify_until(mox.IsA(Event)).AndReturn(e)
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            partial(side_effect, e)).AndReturn(e)

        # called when attaching and notifying pollers
        for i in xrange(0, 2):
            e2 = self.mox.CreateMock(Event)
            e2.processed = False
            e2.return_value = None
        
            # called when sending response to poller
            self.listeners.notify_until(mox.IsA(Event)).AndReturn(e2)
            self.listeners.filter(mox.IsA(Event), mox.IsA(dict)\
                ).WithSideEffects(partial(side_effect1, e2)).AndReturn(e2)
            
            p = self.mox.CreateMockAnything()
            p([{'tmp': i, 'text': 'a', 'args': 'c', 'date': mox.IsA(int), \
                'from': 'b', 'id': mox.IsA(str)}])
            pollers.append(p)
        # called when preparing response to request
        e1 = self.mox.CreateMock(Event)
        e1.processed = True
        e1.return_value = None
        def side_effect2(a, b):
            e1.return_value = b
        self.listeners.filter(mox.IsA(Event), mox.IsA(dict)).WithSideEffects(\
            side_effect2).AndReturn(e1)

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

    def test_init_prevents_reinitialization(self):
        err = False
        self.api.init()
        try:
            self.api.init()
        except ChatReinitializationForbiddenError:
            err = True
        self.assertTrue(err)

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
    
    def test_shutdown_raises_exception_when_chat_is_not_initialized(self):
        err = False
        try:
            self.api.shutdown()
        except UninitializedChatError:
            err = True
        self.assertTrue(err)


if "__main__" == __name__:
    unittest.main()
