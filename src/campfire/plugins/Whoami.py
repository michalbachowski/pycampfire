#!/usr/bin/env python
# -*- coding: utf-8 -*-
from campfire.utils import Plugin
from event import Event


class Whoami(Plugin):
    """
    Plugin that tells caller about itself profile
    """

    def tell(self, msg):
        """
        Returns information about current user`s profile
        """
        return msg['from']
    
    def _init(self, event):
        """
        Initializes application (registers console command)
        """
        self.dispatcher.notify_until(Event(self, 'console.command.add', \
            {'plugin': self.__class__.__name__, 'actions': {'tell': \
                (self.tell, lambda p, a, u: True)}}))
