#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python standard library
#
import unittest

# hack for loading modules
import _path
_path.fix()

##
# event modules
#
from event import Event


class EventTestCase(unittest.TestCase):

    def test_init_requires_2_arguments(self):
        err = False
        try:
            e = Event()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_requires_2_arguments_1(self):
        err = False
        try:
            e = Event(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_init_requires_2_arguments_2(self):
        err = False
        try:
            e = Event(None, None)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_init_allows_to_pass_3_arguments(self):
        err = False
        try:
            e = Event(None, None, {})
        except TypeError:
            err = True
        self.assertFalse(err)
        
    def test_init_does_not_check_input_arguments(self):
        err = False
        try:
            e = Event(None, None, None)
        except:
            err = True
        self.assertFalse(err)
        
    def test_init_state(self):
        e = Event('a', 'b')
        self.assertEqual('a', e.subject)
        self.assertEqual('b', e.name)
        self.assertEqual({}, e.parameters)
        self.assertIsNone(e.return_value)
        self.assertFalse(e.processed)

        e = Event('a', 'b', {'a': 1})
        self.assertEqual({'a': 1}, e.parameters)

    def test_mark_processed_changes_state_of_object(self):
        e = Event(None, None)
        self.assertFalse(e.processed)
        e.mark_processed()
        self.assertTrue(e.processed)

    def test_processed_is_read_only_property(self):
        e = Event(None, None)
        err = False
        try:
            e.processed = True
        except AttributeError:
            err = True
        self.assertTrue(err)

    def test_parametrs_can_be_accessed_throught_event_instance(self):
        e = Event(None, None, {'a': 1})

        self.assertEqual(1, e['a'])
        self.assertTrue('a' in e)
        # event is read-only
        err = False
        try:
            e['b'] = 2
        except RuntimeError:
            err = True
        self.assertTrue(err)
        err = False
        try:
            del e['a']
        except RuntimeError:
            err = True
        self.assertTrue(err)


if "__main__" == __name__:
    unittest.main()
