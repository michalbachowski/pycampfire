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
        self.commands = defaultdict(dict)
        self.permissions = defaultdict(dict)
        self.permission_checkers = defaultdict(dict)

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('console.command.add', self.add_command), \
            ('message.received', self.on_new_message, 10)]

    @synchronous
    def add_command(self, event):
        """
        Adds new command with proper permissions
        """
        plugin = event['plugin']
        for (action, data) in event['actions'].iteritems():
            try:
                # more often we will handle case: method => action
                # rather than: method => (action, perms)
                # so by default we try to unpack single value instead of topule
                # (that single comma is crucial!)
                method, = data
            except ValueError:
                method, permissions = data
            else:
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

###
###
###
###
###




    def initPlugin( self ):
        self._attachPlugin( ( None, self ) )

    def _allow( self, action, user ):
        if "allowed" == action:
            return True
        return None

    def _notify( self, action, data, response = None, user = None ):
        if "plugin.attach" == action:
            return self._attachPlugin( data )
        elif "message.read" == action:
            try:
                self._checkCommand( user, 'ban', 'user' )
            except AccessDeniedError:
                data['from']['ip'] = ''
        elif "message.write" == action:
            try:
                return self._checkMessage( data, response, user )
            except ConsoleError as e:
                response.append( self.name(), str( e ) )
                return None
        return data

    def _parseCommand( self, command ):
        #return [ e.strip() for e in command.split( " " ) ]
        try:
            return csv.reader( [ command.strip().encode('utf-8') ], delimiter=" " ).next()
        except:
            return []

    def _checkMessage( self, data, response, user ):
        # console message musy begins with "$"
        if not '$' == data['message'][0]:
            return data
        # parse command (without "$" sign)
        params = self._parseCommand( data['message'][1:] )
        if len( params ) < 2:
            return data
        plugin = params.pop(0)
        action = params.pop(0)
        # check command
        self._checkCommand( user, plugin, action )
        params.insert( 0, user )
        # set proper room
        self.roomSetter[plugin]( self.room )
        # call plugin
        output = self.plugins[plugin][action]( *params )
        if output is not None:
            response.append( plugin, output )
        return None

    def _checkCommand( self, user, plugin, action ):
        # plugin and action must be declared
        if not plugin in self.plugins:
            raise NoPluginError( "Plugin not found" )
        if not action in self.plugins[plugin]:
            raise NoActionError( "Action not found" )
        # user have to be allowed
        if not self._isAllowed( user, plugin, action ):
            raise AccessDeniedError( "Access denied" )

    def _attachPlugin( self, data ):
        try:
            ( action, plugin ) = data
        except:
            return data
        defaultMembers = dir( chatlib.PluginBase )
        pluginMembers = dir( plugin )
        members = {}
        for member in pluginMembers:
            # omit default members
            if member in defaultMembers:
                continue
            try:
                func = getattr( plugin, member )
                # special case - function that determines whether user is allowed do use given plugin
                if "_allow" == func.__name__:
                    self.permissions[plugin.name()] = func
                    continue
                # omit private members
                if "_" == func.__name__[0]:
                    continue
                members[func.__name__] = func
            except AttributeError:
                continue
        if members:
            self.plugins[plugin.name()] = members
            self.roomSetter[plugin.name()] = plugin.setRoom
        return data

    def _isAllowed( self, user, plugin, action ):
        # plugin itself can both allow and deny. None means that console should check
        if plugin in self.permissions:
            access = self.permissions[plugin]( action, user )
            if access is not None:
                return access
        return self.checkUser( user, self._isUserAllowed( plugin, action ) )

    def _isUserAllowed( self, plugin, action ):
        plugin = plugin.decode('utf-8')
        def callback( param ):
            plugins = self.fetch( str( param ) )
            if not plugins:
                return False
            if u'*' in plugins:
                return True
            if not plugin in plugins:
                return False
            if u'*' in plugins[plugin]:
                return True
            if not action in plugins[plugin]:
                return False
            return True

        return callback

    def grant( self, currentUser, user, pluginName = None, action = None ):
        user = str( user )
        if pluginName is None:
            pluginName = '*'
        if action is None:
            action = '*'
        plugins = self.fetch( user )
        if not plugins:
            plugins = {}
        if not pluginName in plugins:
            plugins[pluginName] = []
        if not action in plugins[pluginName]:
            plugins[pluginName].append( action )
        self.store( user, plugins )
        return "Permission granted"

    def revoke( self, currentUser, user, pluginName = None, action = None ):
        user = str( user )
        plugins = self.fetch( user )
        if not plugins:
            return "There are no premissions to revoke"
        if '*' == pluginName or pluginName is None:
            self.unset( user )
            return "All permissions have been revoked from user"
        if not pluginName in plugins:
            return "There are no premissions to revoke"
        if '*' == action or action is None:
            del plugins[pluginName]
        elif not action in plugins[pluginName]:
            return
        plugins[pluginName].remove( action )
        if len( plugins[pluginName] ) == 0:
            del plugins[pluginName]
        if len( plugins ) == 0:
            self.unset( user )
            return
        self.store( user, plugins )

    def allowed( self, currentUser, plugin, action ):
        try:
            self._checkCommand( currentUser, plugin, action )
        except AccessDeniedError:
            return False
        except ConsoleError:
            return None
        return True

    def list_commands(self, currentUser):
        out = [];
        for plugin in self.plugins.iterkeys():
            for (method, func) in self.plugins[plugin].iteritems():
                if not self._isAllowed(currentUser, plugin, method):
                    continue
                out.append({'plugin': plugin, 'method': method,\
                    'args': ' '.join(map(lambda a: '[%s]' % a, \
                        inspect.getargspec(func)[0][2:]))})
        return out
    
    def list_perms(self, currentUser):
        """
        List users with their permissions
        """
        out = []
        for (who, perm) in self.storage.fetchAll(self.name(), \
            self.room).iteritems():
            for plugin, actions in perm.iteritems():
                # prepare response
                out.append({'user': who, 'plugin': plugin, \
                    'actions': ','.join(list(actions))})
        return out
