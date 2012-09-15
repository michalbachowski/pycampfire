#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from collections import deque


class Api(object):
    """
    Api class that provides two main methods:
    """

    def __init__(self, log, listeners, cache_size=120):
        ##
        # input args
        #
        self.log = log
        self.listeners = listeners

        ##
        # some important values
        #
        self.cache = deque([], cache_size)
        self.pollers = []

        self.log.debug('msg=init new api instance; cache_size=%u', cache_size)

    def recv(self, message, user, args):
        self.log.info('msg=received message; message=%s; user=%s; args=%s', \
            message, user, args)
        tmp = {'id': str(uuid.uuid4()), 'data': self._prepare_data(message, \
            user, args)}
        self.cache.append(tmp)
        self._notify(tmp)

    def _prepare_data(self, message, user, args):
        e = self.listeners.notify_until(Event(self, 'auth.check', user))
        if not e.processed:
            raise AuthError()
        return {'message': message, 'user': user, 'args': args}

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

    def attach_poller(self, cursor, callback):
        """
        Adds callback to being notified about new message
        """
        tmp = self._fetch_cached_messages(cursor)
        if tmp:
            self._respond(tmp, callback)
            return
        self.pollers.append(callback)
        return self

    def detach_poller(self):
        try:
            self.pollers.remove(callback)
        except ValueError:
            pass
        return self

    def _fetch_cached_messages(self, cursor=None):
        """
        Fetches cached messages beginning from given cursor
        """
        try:
            return self.cache[\
                self._find_index_of_last_value(cursor):]
        except KeyError:
            return []

    def _find_index_of_last_value(self, cursor=None):
        """
        Finds index of messages newer than given cursor
        """
        cache_len = len(self.cache)
        for i in xrange(cache_len - 1, -1, -1):
            if self.cache[i]['id'] == cursor:
                return i + 1
        return (self.cache_size, 0)[int(cursor is None)]
