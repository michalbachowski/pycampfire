#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import time
from datetime import datetime

##
# campfire.api
from campfire.utils import Plugin
from event import Event, synchronous


class Ban(Plugin):
    """
    Ban plugin.

    Handles banning users
    """

    def __init__(self, banned={}):
        """
        Object initialization
        """
        self.banned = banned

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message), \
            ('message.read.prevent', self.prevent)]

    def _init(self, event):
        """
        Plugin initialization
        """
        self.dispatcher.notify_until(Event(self, 'console.command.add', \
            {'plugin': 'ban', 'actions': {'users': self.cmd_users, \
                'user': self.cmd_add, 'remove': self.cmd_remove}}))

    def cleanup(self):
        """
        Cleans up banned list
        """
        banned = self.banned.copy()
        for (param, date) in banned.iteritems():
            if self.check_ban_date(date):
                continue
            del self.banned[param]

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        data['banned'] = self.is_banned(data['from'])
        return data

    @synchronous
    def prevent(self, event):
        """
        Prevents messages that comes from banned user to be pushed
        to non-banned pollers
        """
        """
        Filters out messages from banned users for other people
        """
        data = event['message']
        # no 'banned' property in message - show message
        if not 'banned' in data:
            return False
        
        # remove 'banned' property from message dict
        # so noone could guess whether is he/she banned or not
        banned = data['banned']
        del data['banned']
        
        # message not banned - show it to anybody
        if not banned:
            return False
        
        # message is banned, but user is banned too
        # let`s allow banned users to talk to each other :]
        if self.is_banned(event['user']):
            return False
        
        # banned message, not banned user - hide message
        return True

    def is_banned(self, user):
        """
        Check whether user is banned.
        """
        for param in self.match_user(user, self.banned.iterkeys()):
            if self.check_ban_date(self.banned[param]):
                return True
        return False

    def check_ban_date(self, date):
        """
        Checks ban date
        """
        if date is None:
            return False
        if date < int(time.time()):
            return False
        return True

    def cmd_add(self, msg, param, expire=86400, reason=None):
        """
        Ban given user for given amount of time for given reason
        """
        self.banned[param] = int(time.time()) + int(expire)
        self.log.info('msg=param banned; param=%s; time=%s; end=%s; reason=%s',\
            param, int(expire), \
            datetime.fromtimestamp(self.banned[param]).isoformat(), reason)
        return 'Param banned'

    def cmd_remove(self, msg, param):
        """
        Remove ban
        """
        try:
            del self.banned[param]
        except KeyError:
            raise RuntimeError("Parameter '%s' is not banned", param)
        return 'Ban removed'

    def cmd_users(self, msg):
        """
        List banned users
        """
        out = []
        for (param, date) in self.banned.iteritems():
            if not self.check_ban_date(date):
                continue
            # prepare response
            out.append({'param': param, 'type': self.ban_type(param), 'date': \
                datetime.fromtimestamp(date).isoformat()})
        return out
    
    def ban_type(self, param):
        """
        Determines ban type
        """
        try:
            int(param)
            return 'user_id'
        except ValueError:
            if param.count(':') >= 4 or param.count('.') == 3:
                return 'ip'
            else:
                return 'nick'
