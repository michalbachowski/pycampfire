#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class Direct(Plugin):
    """
    Direct plugin.

    Handles messages posted directly to particular users
    ">recipient: blah"
    """

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message), \
            ('message.read.prevent', self.can_not_read)]

    @synchronous
    def on_new_message(self, event, data):
        """
        Searches for "sign of directness" (">username:" at the begining)
        If found - message is marked as direct
        """
        if data is None:
            return data
        # message does not begin with ">"
        if '>' != data['text'][0]:
            return data
        # ">" is directly followed by space
        if ' ' == data['text'][1]:
            return data
        # there is no colon (":") inside the message
        if not ':' in data['text']:
            return data
        # message ends with colon
        if data['text'].endswith(':'):
            return data
        # ok, we have user
        data['to'] = data['text'].split( ':' )[0][1:]
        data['text'] = data['text'][len(data['to'])+2:]
        event['response']['direct'] = 'Message has been sent'
        return data
    
    @synchronous
    def can_not_read(self, event):
        """
        Filters out direct messages for other people
        """
        user = event['user']
        data = event['message']
        # message is for everyone - display it
        if 'to' not in data:
            return False
        # no user given - hide message
        if user is None:
            return True
        # if current user is receiver or sender - display message
        if self.canRead(user, data):
            return False
        # otherwise - hide message
        return True
    
    def canRead(self, user, data):
        """
        Checks whether current user can read message
        """
        # possible matches
        possibilities = [data['to'], data['from']['name']]
        if data['from']['hasAccount']:
            possibilities.append(data['from']['id'])
        if len(self.match_user(user, possibilities)) > 0:
            return True
        # check puppet
        return 'puppet' in user and user['puppet'] in possibilities
