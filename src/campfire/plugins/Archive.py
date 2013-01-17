#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import time
import csv
import copy

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous


class Archive(Plugin):
    """
    Archive plugin.

    Writes messages to archive
    """

    def __init__(self, backup_path, formatter, treshold=100):
        """
        Object initialization
        """
        self.backup_path = backup_path
        self.formatter = formatter
        self.treshold = treshold

    def _init(self, event):
        """
        Chat initialization
        """
        self.lines = []

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message, 10000), \
            ('chat.periodic', self.periodic)]

    @synchronous
    def periodic(self, event):
        """
        Handles periodic event
        """
        self.write()

    def _shutdown(self, event):
        """
        Chat shutdown
        """
        self.write()

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        tmp = copy.deepcopy(data)
        tmp['text'] = tmp['text'].encode('utf-8')
        line = self.formatter(tmp)
        if line is None:
            return data
        self.lines.append(line)
        if len(self.lines) >= self.treshold:
            self.write()
        return data

    def write(self):
        """
        Writes lines to backup file
        """
        lines = self.lines
        self.lines = []
        self.log.debug('msg=archiving messages; lines=%u', len(lines))
        with open(self._path(), 'a+' ) as f:
            archiver = csv.writer(f, delimiter = ' ', quoting=csv.QUOTE_MINIMAL)
            try:
                archiver.writerows(lines)
            except:
                self.log.exception('msg=an error occurred while archiving ' + \
                    'messages')
        self.log.info('msg=messages archived; lines=%u', len(lines))

    def _path(self):
        """
        Prepares path to archive file
        """
        return time.strftime(self.backup_path)
