#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin
from event import Event, synchronous

class Puppet(Plugin):
    """
    Puppet plugin.

    Handles puppets
    """

    def __init__(self, puppets):
        """
        Initializes instance
        """
        self.puppets = puppets

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message), \
            ('auth.nick.check', self.on_login)]

    def _init(self, event):
        """
        Chat initialization
        """
        self.dispatcher.notify_until(Event(self, 'console.command.add', \
            {'plugin': 'puppet', 'actions': {'users': self.cmd_users, \
            'add': self.cmd_add, 'remove': self.cmd_remove, \
            'get': (self.cmd_get, self.permissions_get)}}))

    @synchronous
    def on_login(self, event):
        """
        Prevents guest from using Puppet names as nicknames
        """
        for v in self.puppets.itervalues():
            # compare puppet name with nick
            if event['nick'] == v[0]:
                return False
        return True

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        # message has been written by regular user - do nothing
        if not data['args'].get('as_puppet', False):
            data['from']['puppet'] = None
            return data
        # message has been written by puppet - overwrite 'from' information
        puppet = self.cmd_get(data)
        if puppet is not None:
            data['from']['name'] = puppet[0]
            data['from']['avatar'] = puppet[1]
            data['from']['puppet'] = True
            data['from']['id'] = -1
            data['from']['ip'] = '127.0.0.1'
        else:
            data['from']['puppet'] = False
        return data

    def cmd_add(self, msg, owner, puppet_name, avatar=None):
        """
        Adds new puppet to owner
        """
        self.puppets[owner] = (puppet_name, avatar)
        return 'Puppet has been created'

    def cmd_remove(self, msg, owner):
        """
        Remove puppet from owner
        """
        try:
            del self.puppets[owner]
        except KeyError:
            return 'User does not own a puppet'
        return 'Puppet has been removed'

    def cmd_get(self, msg):
        """
        Returns information about current user's puppet
        """
        for arg in self.match_user(msg['from'], self.puppets.iterkeys()):
            return self.puppets[arg]

    def permissions_get(self, plugin, action, user):
        """
        Permission checker for 'self.cmd_get' method
        """
        # only logged users can have puppets
        return True
        return user['logged'] and user['hasAccount']

    def cmd_users(self, msg):
        """
        Lists all puppets
        """
        out = []
        for (who, puppet) in self.puppets.iteritems():
            out.append({'owner': who, 'puppet': puppet[0], 'avatar': puppet[1]})
        return out
