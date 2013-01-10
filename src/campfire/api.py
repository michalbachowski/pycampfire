#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from itertools import takewhile
from collections import deque
from functools import partial
from event import Event
import time
import copy


class UninitializedChatError(RuntimeError):
    pass


class ChatReinitializationForbiddenError(RuntimeError):
    pass

class AuthError(RuntimeError):
    pass


class Api(object):
    """
    Main chat class
    """

    user_struct = {'id': -1, 'name': 'Guest', 'ip': '127.0.0.1', \
        'logged': False, 'hasAccount': False, 'system': False}

    system_user_struct = {'id': -1, 'name': 'System', 'ip': '127.0.0.1', \
        'logged': False, 'hasAccount': False, 'system': True}

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
        self._initialized = False
        self._cache = deque([], cache_size)
        self.pollers = []
        self._default_msg_num = 50

        self.log.debug('msg=init new api instance; cache_size=%u', cache_size)

    def init(self):
        """
        Notify chat initialization
        """
        self.log.info('msg=initialize chat')
        # prevent reinitialization
        if self._initialized:
            raise ChatReinitializationForbiddenError()
        self._initialized = True
        self.dispatcher.notify(Event(self, 'chat.init', {'log': self.log}))
        return self

    def shutdown(self):
        """
        Notify chat shutdown
        """
        self.log.debug('msg=shutting down chat')
        # prevent shutdown of unitialized app
        if not self._initialized:
            raise UninitializedChatError()
        self._initialized = False
        self.dispatcher.notify(Event(self, 'chat.shutdown'))
        # close connections
        self.log.debug('msg=closing remaining connections')
        pollers = copy.copy(self.pollers)
        self.pollers = []
        for (callback, user) in pollers:
            self.log.debug('msg=closing connection; poller=%s', repr(callback))
            self._respond([self._message('shutdown', self.system_user_struct, \
                {})], callback)
            self.log.debug('msg=closed connection; poller=%s', repr(callback))
        self.log.debug('msg=closed remaining connections')
        self.log.info('msg=shutdown chat')
        return self

    def recv(self, message, user, args):
        """
        Entry point for new massages
        """
        self.log.info('msg=received message; message=%s; user=%s; args=%s', \
            message, user, args)
        if not self._initialized:
            raise UninitializedChatError()
        # prepare message
        (msg, response) = self._prepare_message(message, user, args)
        if msg:
            self._cache.appendleft(msg)
            self._notify(msg)
        # prepare response to request
        return self._prepare_response(msg, response)

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
        return user

    def _message(self, message, user, args):
        """
        Prepares message object
        """
        return {'id': str(uuid.uuid4()), 'text': message, \
            'from': user, 'args': args, 'date': int(time.time())}

    def _prepare_message(self, message, user, args):
        """
        Prepares message data
        """
        self.log.debug('msg=preparing message; message=%s; user=%s; args=%s', \
            message, user, args)
        # filter message and prepare final message structure
        e = self.dispatcher.filter(Event(self, 'message.received', \
            {'response': {}}), self._message(message, self._auth_user(user), \
            args))
        response = e['response']
        self.log.debug('msg=message prepared; message=%s; user=%s; ' + \
            'args=%s; result=%s; response=%s;', message, user, args, \
            e.return_value, response)
        return (e.return_value, response)
    
    def _prepare_response(self, message, response):
        """
        Prepares response to Api.recv() request
        """
        self.log.debug('msg=prepare response to "recv()" request; ' + \
            'message=%s; response=%s', message, response)
        e = self.dispatcher.filter(Event(self, 'message.request.response', \
            {'message': message}), response)
        self.log.debug('msg=prepared response to "recv()" request; ' + \
            'message=%s; result=%s', message, e.return_value)
        return e.return_value

    def _filter_output(self, user, message, poller):
        """
        Filters messages before the will be send to user
        """
        # prevent from returning message to user,
        # that should not read it
        self.log.debug('msg=checking whether message can be send to user; ' + \
            'message=%s; user=%s; poller=%s', message, user, poller)
        e = self.dispatcher.notify_until(\
            Event(self, 'message.read.prevent', {'user': user, \
                'poller': poller, 'message': copy.deepcopy(message)}))
        self.log.debug('msg=checked whether message can be send to user; ' + \
            'message=%s; user=%s; poller=%s; result=%s', message, user, poller, \
            e.processed)
        if e.processed:
            return None
        # filter message
        self.log.debug('msg=filter output message; message=%s; user=%s; ' + \
            'poller=%s', message, user, poller)
        msg = self.dispatcher.filter(\
            Event(self, 'message.read.filter', {'user': user, \
                'poller': poller}), copy.deepcopy(message)).return_value
        self.log.debug('msg=filtered output message; message=%s; user=%s; ' + \
            'poller=%s; result=%s', message, user, poller, msg)
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
            tmp = self._filter_output(user, message, repr(callback))
            # prevent from forgetting connection when message should be not send
            if tmp is None:
                self.log.debug('msg=reattaching poller; ' + \
                    'user=%s; poller=%s', user, repr(callback))
                self.pollers.append((callback, user))
            # send message
            else:
                self.log.debug('msg=sending message to poller; ' + \
                    'user=%s; poller=%s', user, repr(callback))
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
        if not self._initialized:
            raise UninitializedChatError()
        self.log.debug('msg=processing new poller; ' + \
            'user=%s; cursor=%s; poller=%s', user, cursor, repr(callback))
        tmp = self._fetch_cached_messages(user, cursor, repr(callback))
        if tmp:
            self.log.debug('msg=found messages newer than given cursor; ' + \
                'user=%s; cursor=%s; poller=%s; nummsg=%u', user, cursor, \
                repr(callback), len(tmp))
            self._respond(tmp, callback)
            return
        self.log.debug('msg=attaching new poller; ' + \
            'user=%s; poller=%s', user, repr(callback))
        self.pollers.append((callback, user))
        return self

    def _do_detach(self, item):
        """
        Removed given item from pollers list
        """
        self.log.debug('msg=detaching poller; user=%s; poller=%s', item[1], \
            repr(item[0]))
        self.pollers.remove(item)

    def detach_poller(self, callback):
        """
        Detaches given poller from list of polles waiting for new messages
        """
        if not self._initialized:
            raise UninitializedChatError()
        self.log.debug('msg=detaching pollers for callback; poller=%s', \
            repr(callback))
        try:
            map(self._do_detach, (i for i in self.pollers if i[0] == callback))
        except ValueError:
            pass
        return self

    def _fetch_cached_messages(self, user, cursor, callback_repr):
        """
        Fetches cached messages beginning from given cursor
        """
        self.log.debug('msg=fetching cached messages; user=%s; cursor=%s; ' + \
            'poller=%s', user, cursor, callback_repr)
        tmp = filter(lambda a: a is not None, \
            (self._filter_output(user, i[1], callback_repr) \
                for i in takewhile(partial(self._compare_index, cursor), \
                    enumerate(self._cache)) if not self._is_current_item(\
                        cursor, i[1])))
        self.log.debug('msg=fetched cached messages; user=%s; cursor=%s; ' + \
            'nummsg=%u', user, cursor, len(tmp))
        return tmp

    def _is_current_item(self, cursor, item):
        """
        Checks whether given cursor indicates given item
        """
        return cursor == item['id']

    def _compare_index(self, cursor, item):
        """
        Compares cursor with index of given message
        """
        if cursor is None and item[0] < self._default_msg_num:
            return True
        return self._is_current_item(cursor, item[1])
