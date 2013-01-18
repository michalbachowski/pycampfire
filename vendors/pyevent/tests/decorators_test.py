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
from event import synchronous, asynchronous


class DecoratorsTestCase(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
    
    def tearDown(self):
        self.mox.UnsetStubs()
    
    @synchronous
    def sync_notify(self, event):
        return True

    @asynchronous
    def async_notify(self, event, callback):
        callback(True)

    def test_synchronous_notify(self):
        self.assertTrue(self.sync_notify('foo'))

    def test_asynchronous_notify_requires_callback(self):
        err = False
        try:
            self.async_notify('foo')
        except RuntimeError:
            err = True
        self.assertTrue(err)

    def test_asynchronous_call_requires_callback_to_be_given_as_named_arg(self):
        def callback(val):
            pass
        err = False
        try:
            self.async_notify('foo', callback)
        except RuntimeError:
            err = True
        self.assertTrue(err)

    def test_asynchronous_notify_calls_callback(self):
        # prepare callback
        callback = self.mox.CreateMockAnything()
        callback(True)

        self.mox.ReplayAll()
        
        self.async_notify('foo', callback=callback)
        
        self.mox.VerifyAll()
    
    @synchronous
    def sync_filter(self, event, val):
        return val

    @asynchronous
    def async_filter(self, event, val, callback):
        callback(val)

    def test_synchronous_filter(self):
        self.assertEquals('bar', self.sync_filter('foo', 'bar'))

    def test_asynchronous_filter_requires_callback(self):
        err = False
        try:
            self.async_filter('foo', 'bar')
        except RuntimeError:
            err = True
        self.assertTrue(err)

    def test_asynchronous_filter_calls_callback(self):
        # prepare callback
        callback = self.mox.CreateMockAnything()
        callback('bar')

        self.mox.ReplayAll()
        
        self.async_filter('foo', 'bar', callback=callback)
        
        self.mox.VerifyAll()


if "__main__" == __name__:
    unittest.main()
