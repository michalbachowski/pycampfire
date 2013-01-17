#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import copy
import uuid
import time

##
# event module
from event import Event, Listener, synchronous


class Plugin(Listener):
    """
    Base abstract Plugin class
    """
    user_attrs = ['id', 'ip', 'name']
    log = None


    def match_user(self, user, possibilities):
        """
        Tests whether something within given user structure is contained in 
        given possibilities
        """
        return [v for (k, v) in user.iteritems() \
            if k in Plugin.user_attrs and str(v) in possibilities]

    def get_uid(self, user):
        """
        Fetches user ID for given user
        """
        if user is None:
            return None
        if user['hasAccount']:
            return user['id']
        if user['logged']:
            return user['name']
        if 'ip' in user:
            return user['ip']
        return None

    @synchronous
    def init(self, event):
        """
        Method called on chat initialization
        """
        self.log = event['log']
        self.log.debug('msg=initializing plugin; plugin=%s', \
            self.__class__.__name__)
        return self._init(event)

    def _init(self, event):
        """
        Method called on chat initialization (this should be implemented)
        """
        pass

    @synchronous
    def shutdown(self, event):
        """
        Method called on chat shutdown
        """
        self.log.debug('msg=shutting down plugin; plugin=%s', \
            self.__class__.__name__)
        return self._shutdown(event)

    def _shutdown(self, event):
        """
        Method called on chat shutdown (this should be implemented)
        """
        pass

    def mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        return [('chat.init', self.init), ('chat.shutdown', self.shutdown)] + \
            self._mapping()

    def _mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        return []


class AuthHelper(object):
    """
    Helper that provides basic auth mechanism
    """
    profiles = {} # list of profiles
    tokens = {}   # map token to profile

    session_time = 30 # minutes

    def __init__(self, api, dispatcher, log):
        """
        Object initializtion
        """
        self.log = log
        self.user_struct = api.user_struct
        self.dispatcher = dispatcher
        dispatcher.attach('chat.periodic', self.periodic)

    @synchronous
    def periodic(self, event):
        """
        Handles periodic events
        """
        self.cleanup()

    @property
    def session_max_age(self):
        """
        Calculates max lastvisit time that makes session valid
        """
        return time.time() - self.session_time * 60

    def cleanup(self):
        """
        Method cleans up old session
        """
        treshold = self.session_max_age
        tokens = self.tokens.copy()
        for (token, data) in tokens.iteritems():
            if data['lastvisit'] >= treshold:
                continue
            self.logout(token)

    def login(self, user, ip):
        """
        Logs user in
        """
        self.cleanup()

        # login has been used already
        if user in self.profiles:
            raise RuntimeError("Login used")

        # check whether login is allowed
        e = self.dispatcher.notify_until(Event(self, 'auth.login.reject', \
            {'login': name}))

        if e.processed:
            raise RuntimeError("Login rejected")

        # create profile
        profile = copy.deepcopy(self.user_struct)
        profile.update({'name': user, 'logged': True, \
            'ip': ip})

        # prepare profile information
        e = self.dispatcher.filter(Event(self, 'auth.profile.prepare'), profile)
        if e.return_value is None:
            raise RuntimeError("Login terminated")
        profile = e.return_value

        # create token
        token = str(uuid.uuid4())
        self.profiles[user] = profile
        self.tokens[token] = {'user': user, 'lastvisit': time.time()}

        # notify plugin that user has been logged in
        e = self.dispatcher.notify(Event(self, 'auth.logged.in', \
            {'profile': copy.deepcopy(profile), 'token': token}))
        self.log.debug('msg=user logged in; login=%s; profile=%s', user, \
            profile)
        return token

    def logout(self, token):
        """
        Logs user out
        """
        # notify plugin that user has been logged out
        e = self.dispatcher.notify(Event(self, 'auth.logged.out', \
            {'profile': self.profiles[self.tokens[token]['user']], \
            'token': token}))
        del self.profiles[self.tokens[token]['user']]
        del self.tokens[token]

    def get_current_user(self, token):
        """
        Fetches current user profile
        """
        # bump lastvisit time
        try:
            if self.tokens[token]['lastvisit'] <= self.session_max_age:
                return None
            self.tokens[token]['lastvisit'] = time.time()
            return self.profiles[self.tokens[token]['user']]
        except KeyError:
            if token in self.tokens:
                del self.tokens[token]
            return None
