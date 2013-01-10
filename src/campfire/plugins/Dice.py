#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import random

##
# campfire.api
from campfire.utils import Plugin


class Dice(Plugin):
    """
    Dice plugin.

    Handles "/roll" messages
    """
    dices = [2, 3, 4, 6, 8, 10, 12, 20, 100]

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message)]
    
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if '/roll' != data['text'][0:5]:
            return data
        try:
            dice = int(data['text'].split(' ')[1])
            if dice not in self.dices:
                raise RuntimeError()
        except:
            dice = 6
        data['me'] = True
        data['dice'] = True
        data['text'] = u'rzuca kością k%u i wyrzuca %u' %\
            (dice, random.randint(1, dice))
        return data
