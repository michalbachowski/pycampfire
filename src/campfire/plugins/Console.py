#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import csv
import inspect
from collections import defaultdict

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class Console(Plugin):
    """
    Console plugin.

    Simplifies managing console-like commands
    """

    def __init__(self):
        """
        Object initialziation
        """
        self._reset()

    def _init(self, event):
        """
        Initializes plugin
        """
        # initialize some variables
        self._reset()

        # attach commands
        plugin = self.__class__.__name__
        self.attach_command(plugin, 'grant', self.cmd_grant)
        self.attach_command(plugin, 'revoke', self.cmd_revoke)
        self.attach_command(plugin, 'list_commands', self.cmd_list_commands)
        self.attach_command(plugin, 'list_perms', self.cmd_list_perms)
        self.attach_command(plugin, 'allowed', self.cmd_allowed, \
            lambda p, a, u: True) # anyone can call that method

    def _reset(self):
        """
        Re-setting default variables for object
        """
        self.commands = defaultdict(dict)
        self.permissions = defaultdict(dict)
        self.permission_checkers = defaultdict(dict)

    def mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]

        It is overriden on purpose (in order to set priority for 'chat.init')
        """
        return [('chat.init', self.init, 10), \
            ('chat.shutdown', self.shutdown), \
            ('console.command.add', self.add_command), \
            ('message.received', self.on_new_message, 10)]

    @synchronous
    def add_command(self, event):
        """
        Adds new command with proper permissions
        """
        plugin = event['plugin']
        self.log.debug('msg=adding commands; plugin=%s; actions=%s', \
            event['plugin'], event['actions'])
        for (action, data) in event['actions'].iteritems():
            # check for iterable
            try:
                iter(data)
                # case: method => (action, perms)
                method, permissions = data
            # case: method => action
            except (TypeError, ValueError):
                method = data
                permissions = None
            self.attach_command(plugin, action, method, permissions)
        return True

    def attach_command(self, plugin, action, method, checker=None):
        """
        Method attaches new console command
        """
        plugin = plugin.lower()
        action = action.lower()
        self.commands[plugin][action] = method
        self.permission_checkers[plugin][action] = checker or self.allow
        self.log.debug('msg=attached command; plugin=%s; action=%s; ' + \
            'method=%s; checker=%s', plugin, action, repr(method), \
            repr(self.permission_checkers[plugin][action]))

    def check_permissions(self, plugin, action, user):
        """
        Checks permissions for given plugin and action
        """
        try:
            return self.permission_checkers[plugin][action](plugin, action, \
                user)
        except KeyError, e:
            return False

    def allow(self, plugin, action, user):
        """
        Default permission checker
        """
        try:
            return self.match_user(user, self.permissions[plugin][action])
        except ValueError:
            return False 

    def parse_command(self, command):
        """
        Parses command and returns each part as separated list elements eg.:\n
        \n
        'plugin action "foo bar" baz'\n
        \n
        becomes:\n
        \n
        ['plugin, 'action', 'foo bar', 'baz']
        """
        try:
            return csv.reader([command.strip().encode('utf-8')], \
                delimiter=" ").next()
        except:
            return []

    @synchronous
    def on_new_message(self, event, data):
        """
        Checks whether given message is 'command'
        """
        # console command must begins with "$"
        if not '$' == data['text'][0]:
            return data
        # parse command (without "$" sign)
        params = self.parse_command(data['text'][1:])
        # we have less than 2 arguments - it`s not  command
        if len(params) < 2:
            return data

        # prepare params
        plugin = params.pop(0)
        action = params.pop(0)
        params.insert(0, data)

        # check permissions
        if not self.check_permissions(plugin, action, data['from']):
            return None

        # call plugin
        try:
            event['response'][plugin] = self.commands[plugin][action](*params)
        except:
            self.log.exception('msg=exception while calling command; ' + \
                'plugin=%s; action=%s; params=%s', plugin, action, params)
        return None

    def cmd_grant(self, msg, user, plugin=None, action=None):
        """
        Grants user with permissions to given plugin and action
        """
        pass

    def cmd_revoke(self, msg, user, plugin=None, action=None):
        """
        Revokes permission to use given plugin and action by user
        """
        pass

    def cmd_allowed(self, msg, plugin, action):
        """
        Checks whether user is allowed to use given action in given plugin
        """
        return self.check_permissions(plugin, action, msg['from'])

    def cmd_list_commands(self, msg):
        """
        lists commands with information about arguments
        """
        out = [];
        for plugin in self.commands.iterkeys():
            for (action, method) in self.commands[plugin].iteritems():
                if not self.check_permissions(plugin, action, msg['from']):
                    continue
                out.append({'plugin': plugin, 'action': action,\
                    'args': ' '.join(map(lambda a: '[%s]' % a, \
                        inspect.getargspec(method)[0][2:]))})
        return out
    
    def cmd_list_perms(self, msg):
        """
        List users with their permissions
        """
        out = []
        for (plugin, actions) in self.permissions.iteritems():
            for (action, users) in actions.iteritems():
                # prepare response
                out.append({'plugin': plugin, 'action': action, \
                    'users': ','.join(list(users))})
        return out
