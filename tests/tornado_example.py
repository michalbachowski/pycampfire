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

# python std library
import logging
import os

# hack for loading modules
import _path
_path.fix()

# tornado modules
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options, parse_command_line
from tornado.escape import json_encode

# chat modules
import campfire
import campfire.platform.tornadoweb as chat

# EventDispatcher modules
from event import Dispatcher

# args
define('port', default=21777, help="run on the given port", type=int)
define('debug', default=False, help="run in debug mode", type=bool)
define('f', default=False, help="fix Python PATH", type=bool)


class ChatServer(tornado.web.Application):
    """
    Main serwer class
    """
    def __init__(self, log):

        dispatcher = Dispatcher()
        api = campfire.Api(log, dispatcher)
        args = {'log': log, 'api': api}

        handlers = [
            (r"/chat/login", chat.AuthHandler, args),
            (r"/chat/logout", chat.AuthHandler, args),
            (r"/chat/reply", chat.HttpHandler, args),
            (r"/chat/poll", chat.HttpHandler, args),
            (r"/chat/socket", chat.SocketHandler, args),
            (r"/", tornado.web.RedirectHandler, {"url": \
                '/example/index.html'}),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": \
                os.path.abspath('../vendors/js-campfire/')})
        ]
        settings = dict(
            cookie_secret = "6s3oEoTlzJKX^OGa=dko5gwmGgJJnuY@7Emup0XdrP13/Vka",
            debug = options.debug
        )

        tornado.web.Application.__init__(self, handlers, **settings)


class CommentsHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.log = logging.getLogger('')

    @tornado.web.authenticated
    def post(self, realm, item_type, item_id, ect):
        status = 200
        ret = int(JBComments.add(self.request.remote_ip,\
            self.current_user['id'], self.get_argument('comment_text'),\
            self.get_argument('nick', None), item_type, item_id, realm,))
        if not ret:
            status = 500
        self.log.info('method: POST; status: %u; ip: %s, user: %u; cid: %u', \
            status, self.request.remote_ip, self.current_user['id'], ret)
        if not ret:
            raise tornado.web.HTTPError(500)
        self.write(json_encode({'comment_id': ret}))


def main():
    parse_command_line()

    log = logging.getLogger('chat')
    http_server = tornado.httpserver.HTTPServer(ChatServer(log), \
        xheaders=True, no_keep_alive=True)
    http_server.listen(options.port)

    log.info('msg=server started; port=%u; debug=%s', options.port, \
        options.debug)
    
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
