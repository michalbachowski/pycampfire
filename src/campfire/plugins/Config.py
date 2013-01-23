#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import json

##
# campfire.api
from campfire.utils import Plugin
from event import Event, synchronous


class Config(Plugin):
    """
    Config plugin.

    Handles configuration read/write
    """

    def __init__(self, path):
        """
        Initializes instance
        """
        self.path = path
        self.storage = {}

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('chat.periodic', self.periodic)]

    @synchronous
    def periodic(self, event):
        """
        Handles periodic event
        """
        self.write()

    def _init(self, event):
        """
        Plugin initialization
        """
        # initialize config storages
        try:
            with open(self.path, "r") as f:
                tmp = json.load(f)
                for k in tmp.iterkeys():
                    # dict and set
                    try:
                        self.storage[k].update(tmp[k])
                    except KeyError:
                        pass
                    except AttributeError:
                        # list
                        self.storage[k].extend(tmp[k])
        except IOError, e:
            self.log.info('msg=configuration not loaded; path=%s; error=%s', \
                self.path, e.strerror)

    def _shutdown(self, event):
        """
        Chat shutdown
        """
        self.write()
        
    def clear(self):
        """
        Clears all configuration
        """
        # clear config
        for k in self.storage.iterkeys():
            try:
                # dicts and sets
                self.storage[k].clear()
            except:
                # lists
                del self.storage[k][:]

    def write(self):
        """
        Writes configuration
        """
        with open(self.path, "w+") as f:
            json.dump(self.storage, f)
        self.log.info('msg=configuration has been written; path=%s', self.path)

    def get(self, plugin, default):
        """
        Fetches configuration for given plugin
        """
        if plugin not in self.storage:
            self.storage[plugin] = default
        return self.storage[plugin]
