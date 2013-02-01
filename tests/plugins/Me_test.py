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

##
# campfire modules
#
from campfire.plugins import Me


class MeTestCase(unittest.TestCase):
    
    def setUp(self):
        logging.basicConfig()
        self.log = logging.getLogger()
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_init_does_not_require_any_arg(self):
        err = False
        try:
            Me()
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_mapping_returns_list(self):
        self.assertEqual(type(Me()._mapping()), type(list()))

    def test_plugin_registers_handler_to_one_event(self):
        self.assertEqual(1, len(Me()._mapping()))

    def test_on_new_message_requires_2_args_1(self):
        err = False
        try:
            Me().on_new_message()
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_on_new_message_requires_2_args_2(self):
        err = False
        try:
            Me().on_new_message(None)
        except TypeError:
            err = True
        self.assertTrue(err)

    def test_on_new_message_requires_2_args_3(self):
        err = False
        try:
            Me().on_new_message(None, None)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_on_new_message_accepts_callback_arg(self):
        err = False
        try:
            Me().on_new_message(None, None, callback=None)
        except TypeError:
            err = True
        self.assertFalse(err)

    def test_on_new_message_expects_data_to_contain_text_field(self):
        err = False
        try:
            Me().on_new_message(None, {})
        except KeyError:
            err = True
        self.assertTrue(err)

    def test_on_new_message_skips_execution_if_data_is_null(self):
        self.assertIsNone(Me().on_new_message(None, None))

    def test_on_new_message_adds_me_key_to_data(self):
        self.assertTrue('me' in Me().on_new_message(None, {'text': '/me'}))
        self.assertTrue('me' in Me().on_new_message(None, {'text': '/me foo'}))
        self.assertTrue('me' in Me().on_new_message(None, {'text': '/me:bar'}))
        self.assertTrue('me' in Me().on_new_message(None, {'text': '/meowth'}))
        self.assertTrue('me' in Me().on_new_message(None, {'text': 'foo'}))
        self.assertTrue('me' in Me().on_new_message(None, {'text': '/foo'}))
    
    def test_on_new_message_sets_me_to_true_if_text_begins_with_given_string(\
        self):
        self.assertTrue(Me().on_new_message(None, {'text': '/me foo'})['me'])
        self.assertTrue(Me().on_new_message(None, {'text': '/me '})['me'])
    
    def test_on_new_message_sets_me_to_false_if_text_equals_given_string(\
        self):
        self.assertFalse(Me().on_new_message(None, {'text': '/me'})['me'])
        self.assertFalse(Me().on_new_message(None, {'text': '/me:foo'})['me'])
        self.assertFalse(Me().on_new_message(None, {'text': '/mewoth'})['me'])

    def test_on_new_message_calls_given_callback(self):
        # prepare
        c = self.mox.CreateMockAnything()
        c(mox.IsA(dict))
        self.mox.ReplayAll()

        # test
        Me().on_new_message(None, {'text': ''}, callback=c)

        # verify
        self.mox.VerifyAll()


if "__main__" == __name__:
    unittest.main()
