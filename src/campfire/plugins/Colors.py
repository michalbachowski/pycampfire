#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin
from event import Event, synchronous

class Colors(Plugin):
    """
    Colors plugin.

    Handles changing color for messages
    """

    def __init__(self, colors):
        """
        Plugin initialization
        """
        self.colors = dict(colors)

    def _init(self, event):
        """
        Plugin initialization
        """
        self.dispatcher.notify_until(Event(self, 'console.command.add', \
            {'plugin': 'color', 'actions': {'users': self.cmd_users, \
                'add': self.cmd_add, 'remove': self.cmd_remove}}))

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message)]

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        if not 'as_puppet' in data or not data['as_puppet']:
            data['color'] = self.color(self.match_user(data['from'], \
                self.colors.iterkeys()))
        elif "puppet" in user and user['puppet']:
            data['color'] = self.color([user['name']])
        return data

    def color(self, keys):
        """
        Fetches color for given keys.
        If more that one key matches - only first is returned.
        If no keys matches - None is returned
        """
        for k in keys:
            if k in self.colors:
                return self.colors[k]
    
    def cmd_add(self, msg, user, color):
        """
        Command handler for Console plugin for adding color
        """
        if '#' != color[0]:
            color = '#' + color
        self.colors[user] = color
        return "Color has been added"

    def cmd_remove(self, msg, user):
        """
        Command handler for Console plugin for removing color
        """
        try:
            del self.colors[user]
        except KeyError:
            return "Given user has no color set"
        return "Color has been removed"
    
    def cmd_users(self, currentUser):
        """
        Command handler for Console plugin for listing users with their colors
        """
        out = []
        for (who, color) in self.colors.iteritems():
            out.append({'param': who, 'color': color})
        return out
