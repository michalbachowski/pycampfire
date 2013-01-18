#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
from functools import partial
import unittest
import mox

# hack for loading modules
import _path
_path.fix()

##
# event modules
#
from event import Event, Dispatcher, Listener


class DispatcherAsyncTestCase(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.event = self.mox.CreateMock(Event)
    
    def tearDown(self):
        self.mox.UnsetStubs()

    def test_notify_when_callback_is_present_calls_it_on_finish(self):
        # prepare dispatcher
        def cb(event, callback):
            callback()
        d = Dispatcher()

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event), mox.IsA(partial)).WithSideEffects(cb)
        listener.foo(mox.IsA(Event), mox.IsA(partial)).WithSideEffects(cb)
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.foo)])
        
        # prepare callback
        callback = self.mox.CreateMockAnything()
        callback(self.event)

        # register
        self.mox.ReplayAll()
        listener.register(d)

        # prepare event
        self.event.name = 'foo'

        # test
        d.notify(self.event, callback)

        # verify
        self.mox.VerifyAll()

    def test_notify_until_when_callback_is_present_calls_it_on_finish(self):
        def cb(event, callback, ret=False):
            callback(ret)
        # prepare dispatcher
        d = Dispatcher()

        # prepare event
        self.event.name = 'foo'
        self.event.mark_processed()

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event), mox.IsA(partial)).WithSideEffects(cb)
        listener.bar(mox.IsA(Event), mox.IsA(partial)).WithSideEffects(\
            partial(cb, ret=True))
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        
        # prepare callback
        callback = self.mox.CreateMockAnything()
        callback(self.event)
       
        # start test
        self.mox.ReplayAll()
        listener.register(d)

        # test
        d.notify_until(self.event, callback)

        # verify
        self.mox.VerifyAll()

    def test_filter_until_when_callback_is_present_calls_it_on_finish(self):
        def cb(event, value, callback):
            callback(value)
        # prepare dispatcher
        d = Dispatcher()

        # prepare event
        self.event.name = 'foo'

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event), 1, mox.IsA(partial)).WithSideEffects(cb)
        listener.bar(mox.IsA(Event), 1, mox.IsA(partial)).WithSideEffects(cb)
        listener.foo(mox.IsA(Event), 1, mox.IsA(partial)).WithSideEffects(cb)
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        
        # prepare callback
        callback = self.mox.CreateMockAnything()
        callback(self.event)

        # test
        self.mox.ReplayAll()
        listener.register(d)

        # test
        d.filter(self.event, 1, callback)

        # verify
        self.mox.VerifyAll()
        self.assertEquals(self.event.return_value, 1)


if "__main__" == __name__:
    unittest.main()
