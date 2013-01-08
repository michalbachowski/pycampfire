#!/usr/bin/env python
# -*- coding: utf-8 -*-
from campfire.utils import Plugin
from event import synchronous


class NoAuth(Plugin):
    """
    Dummy Auth plugin that accepts any user
    """

    @synchronous
    def notify(self, event):
        """
        Accept user
        """
        return True

    def _mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        return [('auth.check', self.notify)]
