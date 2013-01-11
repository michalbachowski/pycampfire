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
import sys
import signal

# hack for loading modules
import _path
_path.fix()

# tornado modules
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.autoreload import add_reload_hook
from tornado.options import define, options, parse_command_line
from tornado.escape import json_encode

# chat modules
import campfire
import campfire.platform.tornadoweb as chat
import campfire.plugins as plugins

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
        # logging
        if options.debug:
            log.setLevel(logging.DEBUG)

        # prepare dispatcher and listeners (plugins)
        dispatcher = Dispatcher()
        plugins.Colors({}).register(dispatcher)
        plugins.Console().register(dispatcher)
        plugins.Dice().register(dispatcher)
        plugins.Me().register(dispatcher)
        plugins.Nap(['sleeps', 'is snoring']).register(dispatcher)
        plugins.NoAuth().register(dispatcher)
        plugins.Quotations([]).register(dispatcher)
        plugins.Tidy().register(dispatcher)
        plugins.Voices().register(dispatcher)
        plugins.Whoami().register(dispatcher)

        # prepare auth handler
        auth = chat.AuthHelper()

        # prepare API instance and run chat
        api = campfire.Api(log, dispatcher)
        api.init()

        auth.userStruct = api.user_struct

        args = {'log': log, 'api': api, 'auth': auth}

        # handlers and settings
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

        # signal handlers
        def _shutdown(signum, stack_frame):
            api.shutdown()
            sys.exit(1)
        
        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

        if options.debug:
            add_reload_hook(api.shutdown)

        # start app
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    parse_command_line()

    log = logging.getLogger('chat')
    log.info('msg=starting server; port=%u; debug=%s', options.port, \
        options.debug)

    http_server = tornado.httpserver.HTTPServer(ChatServer(log), \
        xheaders=True, no_keep_alive=True)
    http_server.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
