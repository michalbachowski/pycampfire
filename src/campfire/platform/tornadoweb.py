#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.escape import json_encode, json_decode

import os.path
import copy
import uuid
import time
import functools
import logging


class Response(dict):
    def __init__(self):
        self.__setitem__('status', 1)

    def mark_failure(self):
        self.__setitem__('status', 0)

    def mark_succeded( self ):
        self.__setitem__('status', 1)


class BaseHandler(tornado.web.RequestHandler):
    """
    Base class for chat handlers
    """
    
    def initialize(self, log, api, auth):
        """
        Prepares instance
        """
        self.api = api
        self.auth = auth
        self.cookie_name = 'chat_user'
    
    def prepare_response(self, response):
        """
        Prepare response ("stringify")
        """
        return json_encode(response)

    def get_error_html(self, status_code, exception=None, **kwargs):
        """
        Handles error response
        """
        return self.prepare_response(self._get_error_response(status_code, \
            exception, kwargs))

    def _get_error_response(self, status_code, exception=None, kwargs=None):
        """
        Prepares structure for error information
        """
        response = Response()
        response.mark_failure()
        error = {
            'code': status_code,
            'message': '',
        }
        if not exception is None:
            error['message'] = str(exception)
        response["error"] = error
        return response

    def post_message(self, arguments):
        """
        Posts new message to chat
        """
        # prepare auxyliary arguments
        auxArgs = {}
        for arg in arguments:
            if "message" == arg:
                continue
            auxArgs[arg] = arguments.get(arg, None)
        # write message
        try:
            return self.api.recv(arguments['message'][0], self.current_user, \
                auxArgs)
        except RuntimeError, e:
            self.set_status(500)
            return self._get_error_response(500, e)

    def get_current_user(self):
        """
        Fetches current user
        """
        cookie = self.get_secure_cookie(self.cookie_name)
        return self.auth.get_current_user(cookie)


class HttpHandler(BaseHandler):
    """
    Handler that allows posting new messages and polling via HTTP
    """

    @tornado.web.authenticated
    def post(self):
        """
        Write message
        """
        response = Response()
        response.update(self.post_message(self.request.arguments))
        self.write(response)

    @tornado.web.asynchronous
    def get(self):
        """
        Wait for new messages
        """
        cursor = self.get_argument("cursor", None)
        if 'null' == cursor:
            cursor = None
        self.api.attach_poller(self.current_user, self._respond, cursor)

    def _respond(self, messages):
        """
        Send response
        """
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        r = Response()
        r['messages'] = messages
        self.finish(self.prepare_response(r))

    def on_connection_close(self):
        """
        Cleanup async connections on close
        """
        self.api.detach_poller(self._respond)


class SocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):
    """
    Handler that allows posting new messages and polling via WebSockets
    """

    def attach_poller(self):
        """
        Attaches poller
        """
        self.api.attach_poller(self.current_user, \
            self._respond, self.get_argument("cursor", None))

    @tornado.web.asynchronous
    def open(self):
        """
        Open WebSocket
        """
        self.attach_poller()

    def on_message(self, message):
        """
        Post new message
        """
        self.write_message(self.post_message(json_decode(message)))

    def on_close(self):
        """
        Cleanup when socket gets closed
        """
        pass

    def allow_draft76(self):
        """
        Allow old version of WS protocol
        """
        return true

    def _respond(self, response):
        """
        Send response
        """
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.write_message(self.prepare_response(response))
        self.attach_poller()


class AuthHelper(object):
    profiles = {} # list of profiles
    tokens = {}   # map token to profile

    userStruct = None
    session_time = 30 # minutes

    def login(self, user, ip):
        """
        Logs user in
        """
        # logout old sessions
        treshold = time.time() - self.session_time * 60
        for (token, data) in self.tokens.iteritems():
            if data['lastvisit'] >= treshold:
                continue
            self.logout(token)

        if user in self.profiles:
            raise RuntimeError("Login used")
        # profile
        profile = copy.deepcopy(self.userStruct)
        profile.update({'name': user, 'logged': True, \
            'ip': ip})
        # cookie
        token = str(uuid.uuid4())
        self.profiles[user] = profile
        self.tokens[token] = {'user': user, 'lastvisit': time.time()}
        return token

    def logout(self, token):
        """
        Logs user out
        """
        del self.profiles[self.tokens[token]['user']]
        del self.tokens[token]

    def get_current_user(self, token):
        """
        Fetches current user profile
        """
        # bump lastvisit time
        try:
            self.tokens[token]['lastvisit'] = time.time()
            return self.profiles[self.tokens[token]['user']]
        except KeyError:
            if token in self.tokens:
                del self.tokens[token]
            return None


class AuthHandler(BaseHandler):
    """
    Chat authentication handler
    """
    cookie_lifetime = 1 # days

    def post(self):
        """
        Login
        """
        user = self.get_argument("login")
        if not user:
            raise tornado.web.HTTPError(401, "Auth failed")
        # remember
        try:
            cookie = self.auth.login(user, self.request.remote_ip)
        except RuntimeError:
            raise tornado.web.HTTPError(403, "Login used")
        # response
        response = Response()
        response["auth"]  = "Logged In"
        response["profile"] = self.auth.get_current_user(cookie)
        self.set_secure_cookie(self.cookie_name, cookie, self.cookie_lifetime)
        self.finish(self.prepare_response(response))

    @tornado.web.authenticated
    def get(self):
        """
        Logout (not all browsers support DELETE method)
        """
        self.delete()
    
    @tornado.web.authenticated
    def delete(self):
        """
        Logout
        """
        cookie = self.get_secure_cookie(self.cookie_name)
        # logout
        self.auth.logout(cookie)
        # remove cookie
        self.set_secure_cookie(self.cookie_name, '', -1)
        response = Response()
        response["auth"] = "You are now logged out"
        self.finish(self.prepare_response(response))

    # TODO: periodic callback to logout users
