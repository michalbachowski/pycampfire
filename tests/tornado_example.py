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
import time

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
from campfire.utils import AuthHelper

# EventDispatcher modules
from event import Dispatcher

# args
define('port', default=21777, help="run on the given port", type=int)
define('debug', default=False, help="run in debug mode", type=bool)
define('f', default=False, help="fix Python PATH", type=bool)

def archive_formatter(data):
    if 'typing' in data and data['typing']:
        return None
    to = 'public'
    if 'to' in data:
        to = data['to']
    return [
        time.strftime(
            '%Y-%m-%d %H:%M:%S',
            time.gmtime(data['date'])
        ),
        data['from']['ip'],
        data['from']['name'],
        to,
        data['text']
    ]

class ChatServer(tornado.web.Application):
    """
    Main serwer class
    """
    def __init__(self, log):
        # logging
        if options.debug:
            log.setLevel(logging.DEBUG)

        # prepare config manager
        config = plugins.Config(os.path.abspath('./config.cfg'))

        # prepare dispatcher and listeners (plugins)
        dispatcher = Dispatcher()
        plugins.AntiFlood().register(dispatcher)
        plugins.Archive(os.path.abspath('./archive.%Y%m%d.csv'), \
            archive_formatter).register(dispatcher)
        plugins.Ban(config.get('ban', {})).register(dispatcher)
        plugins.Colors(config.get('colors', {})).register(dispatcher)
        plugins.Console().register(dispatcher)
        config.register(dispatcher)
        plugins.Dice().register(dispatcher)
        plugins.Direct().register(dispatcher)
        plugins.Me().register(dispatcher)
        plugins.Nap(config.get('nap', [])).register(dispatcher)
        plugins.NoAuth().register(dispatcher)
        plugins.Puppet(config.get('puppet', {})).register(dispatcher)
        plugins.Quotations(config.get('quotations', [])).register(dispatcher)
        plugins.Tidy().register(dispatcher)
        plugins.Typing().register(dispatcher)
        plugins.ValidateLogin(config.get('stopwords', [])).register(dispatcher)
        plugins.Voices(config.get('voices', {})).register(dispatcher)
        plugins.Whoami().register(dispatcher)

        # prepare API instance and run chat
        api = campfire.Api(log, dispatcher)
        api.init()

        # prepare auth handler
        auth = AuthHelper(api, dispatcher, log)

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

        # periodic callback
        p = tornado.ioloop.PeriodicCallback(api.periodic_notification, \
            1 * 60 * 1000) # 1 minute
        p.start()

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
