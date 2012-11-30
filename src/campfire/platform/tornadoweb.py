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
import os.path
import copy
import functools
import logging
from tornado.escape import json_encode, json_decode


class Response(dict):
    def __init__(self):
        self.__setitem__('status', 1)
        self.__setitem__('response', {})

    def append(self, prefix, message, extend=False):
        if prefix not in self['response']:
            self['response'][prefix] = []
        if type(message) == type(list()) and extend:
            self['response'][prefix].extend(message)
        else:
            self['response'][prefix].append(message)

    def mark_failure(self):
        self.__setitem__('status', 0)

    def mark_succeded( self ):
        self.__setitem__('status', 1)


class BaseHandler(tornado.web.RequestHandler):
    """
    Base class for chat handlers
    """

    def initialize(self, log, api):
        """
        Prepares instance
        """
        self.api = api

    def get_error_html(self, status_code, exception=None, **kwargs):
        """
        Handles error response
        """
        response = Response()
        response.mark_failure()
        error = {
            'status': status_code,
            'message': '',
        }
        if not exception is None:
            error['message'] = str(exception)
        response.append("error", error)
        return json_encode(response)

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
        return self.api.recv(arguments['message'], self.current_user, auxArgs)


class HttpHandler(BaseHandler):
    """
    Handler that allows posting new messages and polling via HTTP
    """

    @tornado.web.authenticated
    def post(self):
        """
        Write message
        """
        self.write(self.post_message(arguments))

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


class AuthHandler(BaseHandler):
    """
    Chat authentication handler
    """

    @tornado.web.asynchronous
    def post(self):
        """
        Login
        """
        user = self.get_argument("login")
        response = Response()
        if user:
            (response, user) = self.login(self, user, self.current_user)
        if not user:
            raise tornado.web.HTTPError(401, "Auth failed")
        response.append( "auth", "Logged In" )
        self.finish( self.encodeOutput( response, ext ) )

    @tornado.web.authenticated
    def delete(self):
        """
        Logout
        """
        response = self.logout(self, self.current_user)
        response.append( "auth", "You are now logged out" )
        self.write( self.encodeOutput( response, ext ) )
