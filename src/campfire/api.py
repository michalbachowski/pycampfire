#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from itertools import takewhile
from collections import deque
from functools import partial
from event import Event
import copy


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

        self.init()

    def init(self):
        """
        Notify chat initialization
        """
        self.log.info('msg=initialize chat')
        self.dispatcher.notify(Event(self, 'chat.init'))

    def shutdown(self):
        """
        Notify chat shutdown
        """
        self.log.info('msg=shutdown chat')
        self.dispatcher.notify(Event(self, 'chat.shutdown'))

    def recv(self, message, user, args):
        """
        Entry point for new massages
        """
        self.log.info('msg=received message; message=%s; user=%s; args=%s', \
            message, user, args)
        tmp = self._prepare_data(message, user, args)
        self._cache.appendleft(tmp)
        self._notify(tmp)

    def _auth_user(self, user):
        """
        Checks authentication for given user
        """
        self.log.debug('msg=authenticating user; user=%s', user)
        e = self.dispatcher.notify_until(Event(self, 'auth.check', user))
        if not e.processed:
            self.log.warning('msg=error while authenticating user; user=%s', \
                user)
            raise AuthError()
        self.log.debug('msg=user authenticated; user=%s; result=%s', \
            user, e.return_value)
        return e.return_value

    def _prepare_data(self, message, user, args):
        """
        Prepares message data
        """
        self.log.debug('msg=preparing message; message=%s; user=%s; args=%s', \
            message, user, args)
        # filter message and prepare final message structure
        e = self.dispatcher.filter(\
            Event(self, 'message.written'), \
            {'id': str(uuid.uuid4()), 'data': {\
                'message': message, 'from': self._auth_user(user), \
                    'args': args}})
        self.log.debug('msg=message prepared; message=%s; user=%s; ' + \
            'args=%s; result=%s', message, user, args, e.return_value)
        return e.return_value

    def _filter_output(self, user, message):
        """
        Filters messages before the will be send to user
        """
        # filter message
        self.log.debug('msg=filter output message; message=%s; user=%s', \
            message, user)
        msg = self.dispatcher.filter(\
            Event(self, 'message.read.filter', {'user': user}), \
            copy.deepcopy(message)).return_value
        self.log.debug('msg=filtered output message; message=%s; user=%s; ' + \
            'result=%s', message, user, msg)
        # prevent from returning message to user,
        # that should not read it
        self.log.debug('msg=checking whether message can be send to user; ' + \
            'message=%s; user=%s', msg, user)
        e = self.dispatcher.notify_until(\
            Event(self, 'message.read.prevent', {'user': user, \
                'message': copy.deepcopy(message)}))
        self.log.debug('msg=checked whether message can be send to user; ' + \
            'message=%s; user=%s; result=%s', msg, user, e.processed)
        if e.processed:
            return None
        return msg

    def _notify(self, message):
        """
        Sends response to all pollers
        """
        self.log.debug('msg=sending new message to pollers; ' + \
            'message=%s', message)
        pollers = copy.copy(self.pollers)
        self.pollers = []
        for (callback, user) in pollers:
            tmp = self._filter_output(user, message)
            # prevent from forgetting connection when message should be not send
            if tmp is None:
                self.log.debug('msg=reattaching poller; ' + \
                    'user=%s; callback=%s', user, callback)
                self.pollers.append((callback, user))
            # send message
            else:
                self.log.debug('msg=sending message to poller; ' + \
                    'user=%s; callback=%s', user, callback)
                self._respond([tmp], callback)

    def _respond(self, message, callback):
        """
        Sends response to given callback about new messages
        """
        callback(message)

    def attach_poller(self, user, callback, cursor=None):
        """
        Attaches poller to list of pollers waiting for message
        """
        self.log.debug('msg=processing new poller; ' + \
            'user=%s; cursor=%s', user, cursor)
        tmp = self._fetch_cached_messages(user, cursor)
        if tmp:
            self.log.debug('msg=found messages newer than given cursor; ' + \
                'user=%s; cursor=%s; nummsg=%u', user, cursor, len(tmp))
            self._respond(tmp, callback)
            return
        self.log.debug('msg=attaching new poller; ' + \
            'user=%s; callback=%s', user, callback)
        self.pollers.append((callback, user))
        return self

    def _do_detach(self, item):
        """
        Removed given item from pollers list
        """
        self.log.debug('msg=detaching poller; user=%s; callback=%s', item[1], \
            item[0])
        self.pollers.remove(item)

    def detach_poller(self, callback):
        """
        Detaches given poller from list of polles waiting for new messages
        """
        self.log.debug('msg=detaching pollers for callback; callback=%s', \
            callback)
        try:
            map(self._do_detach, (i for i in self.pollers if i[0] == callback))
        except ValueError:
            pass
        return self

    def _fetch_cached_messages(self, user, cursor=None):
        """
        Fetches cached messages beginning from given cursor
        """
        self.log.debug('msg=fetching cached messages; user=%s; cursor=%s', \
            user, cursor)
        tmp = map(lambda a: a is not None, [self._prepare_output(user, i) \
            for i in takewhile(partial(self._compare_index, cursor), \
                self._cache)])
        self.log.debug('msg=fetched cached messages; user=%s; cursor=%s; ' + \
            'nummsg=%u', user, cursor, len(tmp))
        return tmp

    def _compare_index(self, cursor, item):
        """
        Compares cursor with index of given message
        """
        return cursor == item['id']
