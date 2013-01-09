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
        response = Response()
        response.mark_failure()
        error = {
            'code': status_code,
            'message': '',
        }
        if not exception is None:
            error['message'] = str(exception)
        response["error"] = error
        return self.prepare_response(response)

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
        return self.api.recv(arguments['message'][0], self.current_user, \
            auxArgs)

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
        self.api.attach_poller(self.current_user, \
            self._respond, self.get_argument("cursor", None))

    def _respond(self, response):
        """
        Send response
        """
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.finish(self.prepare_response(response))

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

    userStruct = {
        'id': -1,
        'name': 'Guest',
        'logged': False,
        'hasAccount': False
    }

    def login(self, user, ip):
        """
        Logs user in
        """
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
        response = Response()
        if not user:
            raise tornado.web.HTTPError(401, "Auth failed")
        # remember
        try:
            cookie = self.auth.login(user, self.request.remote_ip)
        except RuntimeError:
            raise tornado.web.HTTPError(403, "Login used")
        # response
        response["auth"]  = "Logged In"
        response["profile"] = self.auth.get_current_user(cookie)
        self.set_secure_cookie(self.cookie_name, cookie, self.cookie_lifetime)
        self.finish(self.prepare_response(response))

    @tornado.web.authenticated
    def delete(self):
        """
        Logout
        """
        cookie = self.get_secure_cookie(self.cookie_name)
        # logout
        self.auth.logout(cookie)
        # remove cookie
        self.set_secure_cookie(self.cookie_name, None, -1)
        response = Response()
        response.append("auth", "You are now logged out")
        self.finish(self.prepare_response(response))

    # TODO: periodic callback to logout users
