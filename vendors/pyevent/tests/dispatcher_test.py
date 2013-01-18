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
from event import Event, Dispatcher, Listener


class DispatcherTestCase(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.event = self.mox.CreateMock(Event)
    
    def tearDown(self):
        self.mox.UnsetStubs()

    def test_init_does_not_take_any_arguments(self):
        err = False
        try:
            Dispatcher()
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_attach_requires_2_arguments(self):
        err = False
        e = Dispatcher()
        try:
            e.attach()
        except TypeError:
            err = True
        self.assertTrue(err)
    
    def test_attach_requires_2_arguments_1(self):
        err = False
        e = Dispatcher()
        try:
            e.attach(None)
        except TypeError:
            err = True
        self.assertTrue(err)
    
    def test_attach_accepts_3_arguments_1(self):
        err = False
        e = Dispatcher()
        try:
            e.attach(None, None, None)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_attach_maintains_priority_based_order(self):
        d = Dispatcher()
        d.attach('test', 'b', 20)
        d.attach('test', 'a', 10)
        d.attach('test', 'c', 20)

        l = d.get_listeners('test')
        self.assertEqual('a', l.next())
        self.assertEqual('b', l.next())
        self.assertEqual('c', l.next())

    def test_get_listeners_always_returns_iterator(self):
        d = Dispatcher()
        d.attach('test', 'b')
        self.assertEqual(1, sum([1 for i in d.get_listeners('test')]))
        self.assertEqual(0, sum([1 for i in d.get_listeners('unknown')]))

    def test_has_listeners_returns_integer(self):
        d = Dispatcher()
        d.attach('test', 'b')
        self.assertTrue(d.has_listeners('test'))
        self.assertFalse(d.has_listeners('unknown'))

    def test_notify_expects_event_as_first_argument(self):
        err = False
        try:
            Dispatcher().notify('a')
        except AttributeError:
            err = True
        self.assertTrue(err)

    def test_notify_notifies_all_listeners(self):
        # prepare dispatcher
        d = Dispatcher()

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event))
        listener.foo(mox.IsA(Event))
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.foo)])
        self.mox.ReplayAll()
        listener.register(d)

        # prepare event
        self.event.name = 'foo'

        # test
        d.notify(self.event)

        # verify
        self.mox.VerifyAll()

    def test_notify_until_expects_event_as_first_argument(self):
        err = False
        try:
            Dispatcher().notify_until('a')
        except AttributeError:
            err = True
        self.assertTrue(err)

    def test_notify_until_notifies_listeners_until_one_returns_true(self):
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
        listener.foo(mox.IsA(Event))
        listener.bar(mox.IsA(Event)).AndReturn('a')
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        self.mox.ReplayAll()
        listener.register(d)

        # test
        d.notify_until(self.event)

        # verify
        self.mox.VerifyAll()

    def test_notify_until_notifies_all_listeners_is_none_returned_true(self):
        # prepare dispatcher
        d = Dispatcher()

        # prepare event
        self.event.name = 'foo'

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event))
        listener.bar(mox.IsA(Event))
        listener.foo(mox.IsA(Event))
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        self.mox.ReplayAll()
        listener.register(d)

        # test
        d.notify_until(self.event)

        # verify
        self.mox.VerifyAll()

    def test_filter_expects_2_arguments(self):
        err = False
        try:
            Dispatcher().filter()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_filter_expects_2_arguments_1(self):
        err = False
        try:
            Dispatcher().filter(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_filter_expects_event_as_first_argument(self):
        err = False
        try:
            Dispatcher().filter('a', 1)
        except AttributeError:
            err = True
        self.assertTrue(err)

    def test_filter_notifies_all_listeners(self):
        # prepare dispatcher
        d = Dispatcher()

        # prepare event
        self.event.name = 'foo'

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event), 1).AndReturn(1)
        listener.bar(mox.IsA(Event), 1).AndReturn(1)
        listener.foo(mox.IsA(Event), 1).AndReturn(1)
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        self.mox.ReplayAll()
        listener.register(d)

        # test
        d.filter(self.event, 1)

        # verify
        self.mox.VerifyAll()

    def test_filter_passes_received_value_to_following_listeners(self):
        # prepare dispatcher
        d = Dispatcher()

        # prepare event
        self.event.name = 'foo'

        # prepare listener
        listener = Listener()
        self.mox.StubOutWithMock(listener, 'mapping')
        listener.foo = self.mox.CreateMockAnything()
        listener.bar = self.mox.CreateMockAnything()
        listener.foo(mox.IsA(Event), 1).AndReturn(2)
        listener.bar(mox.IsA(Event), 2).AndReturn(3)
        listener.foo(mox.IsA(Event), 3).AndReturn(4)
        listener.mapping().AndReturn([('foo', listener.foo),\
            ('foo', listener.bar),\
            ('foo', listener.foo)])
        self.mox.ReplayAll()
        listener.register(d)

        # test
        o = d.filter(self.event, 1)

        # verify
        self.mox.VerifyAll()
        self.assertEqual(4, o.return_value)


if "__main__" == __name__:
    unittest.main()
