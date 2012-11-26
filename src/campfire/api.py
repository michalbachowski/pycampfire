#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from itertools import takewhile
from collections import deque
from functools import partial
from event import Event


class Api(object):
    """
    Api class that provides two main methods:
    """

    def __init__(self, log, dispatcher, cache_size=120):
        """
        Instance initialization
        """
        ##
        # input args
        #
        self.log = log
        self.dispatcher = dispatcher

        ##
        # some important values
        #
        self._cache = deque([], cache_size)
        self.pollers = []

        self.log.debug('msg=init new api instance; cache_size=%u', cache_size)

    def recv(self, message, user, args):
        """
        Entry point for new massages
        """
        self.log.debug('msg=received message; message=%s; user=%s; args=%s', \
            message, user, args)
        tmp = self._prepare_data(message, user, args)
        self._cache.appendleft(tmp)
        self._notify(tmp)

    def _auth_user(self, user):
        """
        Checks authentication for given user
        """
        e = self.dispatcher.notify_until(Event(self, 'auth.check', user))
        if not e.processed:
            raise AuthError()
        return e.return_value

    def _prepare_data(self, message, user, args):
        """
        Prepares message data
        """
        # filter message and prepare final message structure
        e = self.dispatcher.filter(\
            Event(self, 'message.written'), \
            {'id': str(uuid.uuid4()), 'data': {\
                'message': message, 'from': self._auth_user(user), \
                    'args': args}})
        return e.return_value

    def _notify(self, data):
        """
        Sends response to all pollers
        """
        for callback in self.pollers:
            self._respond([data], callback)
        self.pollers = []

    def _respond(self, message, callback):
        """
        Sends response to given callback about new messages
        """
        callback(message)

    def attach_poller(self, callback, cursor=None):
        """
        Attaches poller to list of pollers waiting for message
        """
        tmp = self._fetch_cached_messages(cursor)
        if tmp:
            self._respond(tmp, callback)
            return
        self.pollers.append(callback)
        return self

    def detach_poller(self):
        """
        Detaches given poller from list of polles waiting for new messages
        """
        try:
            self.pollers.remove(callback)
        except ValueError:
            pass
        return self

    def _fetch_cached_messages(self, cursor=None):
        """
        Fetches cached messages beginning from given cursor
        """
        return [i for i in takewhile(partial(self._compare_index, cursor), \
            self._cache)]

    def _compare_index(self, cursor, item):
        """
        Compares cursor with index of given message
        """
        return cursor == item['id']
