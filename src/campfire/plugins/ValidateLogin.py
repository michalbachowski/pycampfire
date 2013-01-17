#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import re

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous


class ValidateLogin(Plugin):
    """
    ValidateLogin plugin.

    Checks login
    """

    def __init__(self, stopwords):
        """
        Object initialization.

        stopwords should be a "set"
        """
        self.stopwords = set(stopwords)

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('auth.login.reject', self.reject_login)]

    def _init(self, event):
        """
        Plugin initialization
        """
        self.pattern = re.compile("^([A-Z][a-z]+[ ]?)+$")

    @synchronous
    def reject_login(self, event):
        """
        Checks whether login fullfills criteria, that is:
        - consists only of letters [a-zA-Z] and spaces
        - each word in login begins from uppercase latter
        - is 3 - 30 characters long
        - does not contain common stopwords
        """
        login = event['login']
        # check length
        if len(login) > 30:
            event.return_value = 'Login can not be longer than 30 chars'
            return True
        if len(login) < 3:
            event.return_value = 'Login can not be shorter than 3 chars'
            return True
        # check pattern
        if self.pattern.match(login) is None:
            event.return_value = 'Login can contain only letters and ' + \
                'spaces. Each wort must begin with uppercase letter'
            return True
        # common stopwords
        if len(set(login.split(' ')) & self.stopwords) > 0:
            event.return_value = 'Login contains at least one forbidden word'
            return True
        return False
