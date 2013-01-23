#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
from itertools import takewhile, imap
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
        self._time_treshold = 15 # minutes after message will become unaccessible

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

    def periodic_notification(self):
        """
        Sends periodic notifications to plugins
        """
        self.log.debug('msg=periodic notification')
        self.dispatcher.notify(Event(self, 'chat.periodic'))

    def recv(self, message, user, args):
        """
        Entry point for new massages
        """
        self.log.debug('msg=received message; message=%s; user=%s; args=%s', \
            message, user, args)
        if not self._initialized:
            raise UninitializedChatError()
        # prepare message
        (msg, response) = self._prepare_message(message, user, args)
        if msg:
            self.log.info('msg=stored message; message=%s; user=%s; args=%s', \
                msg['id'], user, args)
            self._cache.appendleft(msg)
            self._notify(msg)
        else:
            msg = {'id': None}
            self.log.debug('msg=message NOT stored; message=%s; user=%s; ' + \
                'args=%s', msg['id'], user, args)
        # prepare response to request
        return self._prepare_response(msg, response)

    def _auth_user(self, user):
        """
        Checks authentication for given user
        """
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
        # filter message and prepare final message structure
        e = self.dispatcher.filter(Event(self, 'message.received', \
            {'response': {}}), self._message(message, self._auth_user(user), \
            args))
        response = e['response']
        return (e.return_value, response)
    
    def _prepare_response(self, message, response):
        """
        Prepares response to Api.recv() request
        """
        e = self.dispatcher.filter(Event(self, 'message.request.response', \
            {'message': message}), response)
        self.log.debug('msg=prepared response to "recv()" request; ' + \
            'message=%s; result=%s', message['id'], e.return_value)
        return e.return_value

    def _filter_output(self, user, message, poller):
        """
        Filters messages before the will be send to user
        """
        # prevent from returning message to user,
        # that should not read it
        e = self.dispatcher.notify_until(\
            Event(self, 'message.read.prevent', {'user': user, \
                'poller': poller, 'message': copy.deepcopy(message)}))
        if e.processed:
            self.log.debug('msg=message can not be send to user, skipping; ' + \
            'message=%s; user=%s; poller=%s; result=%s', message['id'], user, \
            poller, e.processed)
            return None
        # filter message
        msg = self.dispatcher.filter(\
            Event(self, 'message.read.filter', {'user': user, \
                'poller': poller}), copy.deepcopy(message)).return_value
        return msg

    def _notify(self, message):
        """
        Sends response to all pollers
        """
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
                self.log.debug('msg=sending message to poller; user=%s; ' + \
                    'poller=%s; message=%s', user, repr(callback), tmp['id'])
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
        self.log.debug('msg=new messages not found, attaching new poller; ' + \
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
        map(self._do_detach, (i for i in self.pollers if i[0] == callback))
        return self

    def _fetch_cached_messages(self, user, cursor, callback_repr):
        """
        Fetches cached messages beginning from given cursor
        """
        time_treshold = time.time() - self._time_treshold * 60
        out = []
        for (idx, msg) in enumerate(self._cache):
            # cursor indicates current message - break
            if cursor == msg['id']:
                break
            # cursor is None - check date or message index
            elif cursor is None:
                # message is too old
                if msg['date'] < time_treshold:
                    break
            # prepare message
            tmp = self._filter_output(user, msg, callback_repr)
            # message returned is None - it can not be returned to user
            if tmp is None:
                continue
            out.append(tmp)
        out.reverse()
        return out
