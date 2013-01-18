#!/usr/bin/env python
# -*- coding: utf-8 -*-
import heapq
import itertools
from functools import partial, wraps


class Event(object):
    """
    Class that represents single event to be handled

    Provides information about:
    
    subject - subject which sends event
    name - name of an event
    parameters - event parameters
    return_value - event return value
    processed - whether event has been processed or not

    Example:

    subject = self
    e = Event(subject, 'test', {'a' :1})
    e.subject           # subject
    e.name              # 'test'
    e.parameters        # {'a': 1}
    e['a']              # 1
    e.parameters['a']   # 1
    e.return_value      # None
    e.return_value = 'a'
    e.return_value      # 'a'
    e.processed         # False
    e.mark_procesed()
    e.processed         # True
    """

    def __init__(self, subject, name, parameters={}):
        """
        Initializes class instance
        """
        self.subject = subject
        self.name = name
        self.parameters = parameters
        self.return_value = None
        self._processed = False

    @property
    def processed(self):
        """
        Returns information whether event has been processed
        """
        return self._processed

    def mark_processed(self):
        """
        Marks event as processed
        """
        self._processed = True
        return self

    def __getitem__(self, key):
        """
        Allows to treat class instances as dicts
        """
        return self.parameters[key]

    def __setitem__(self, key, value):
        """
        Allows to treat class instances as dicts
        """
        raise RuntimeError('Event is read-only')

    def __delitem__(self, key):
        """
        Allows to treat class instances as dicts
        """
        raise RuntimeError('Event is read-only')

    def __contains__(self, item):
        """
        Allows to treat class instances as dicts
        """
        return item in self.parameters


class Dispatcher(object):
    """
    Dispatches given events according to previously set listeners
    """

    def __init__(self):
        """
        Initializes class instance
        """
        self._listeners = {}
        self.counter = itertools.count()

    def attach(self, name, listener, priority=0):
        """
        Attaches new listener to dispatcher
        """
        if name not in self._listeners:
            self._listeners[name] = []
        heapq.heappush(self._listeners[name], self._prepare(listener, priority))

    def _prepare(self, listener, priority=0):
        """
        Prepares internal listener structure
        """
        return (priority, next(self.counter), listener)

    def has_listeners(self, name):
        """
        Returns information whether there are any listeners 
        attached to given event name
        """
        return name in self._listeners and len(self._listeners[name])>0

    def get_listeners(self, name):
        """
        Fetches list of listeners attached to given event.
        Returns iterator
        """
        if name not in self._listeners:
            return []
        return (l[2] for l in self._listeners[name])

    def notify(self, event, callback=None):
        """
        Notifies each listener about new event
        """
        # asynchronous call
        if callback:
            return self._async_notify(self.get_listeners(event.name), \
                event, callback)
        # synchronous call
        for listener in self.get_listeners(event.name):
            listener(event)
        return event
    
    def _async_notify(self, listeners, event, callback):
        """
        Notifies each listener about new event in asynchronous manner
        """
        try:
            listeners.next()(event, partial(self._async_notify, \
                listeners, event, callback=callback))
        except StopIteration:
            callback(event)

    
    def notify_until(self, event, callback=None):
        """
        Notifies listeners about new event until any of then returns True
        """
        # asynchronous call
        if callback:
            return self._async_notify_until(self.get_listeners(event.name), \
                event, False, callback)
        # synchronous call
        for listener in self.get_listeners(event.name):
            if listener(event):
                event.mark_processed()
                break
        return event

    def _async_notify_until(self, listeners, event, value, callback):
        """
        Notifies listeners about new event until any of then returns True 
        in asynchronous manner
        """
        try:
            if value:
                event.mark_processed()
                raise StopIteration
            listeners.next()(event, partial(self._async_notify_until, \
                listeners, event, callback=callback))
        except StopIteration:
            callback(event)

    def filter(self, event, value, callback=None):
        """
        Filters given value using given event
        """
        # asynchronous call
        if callback:
            return self._async_filter(self.get_listeners(event.name), event, \
                value, callback)
        # synchronous call
        for listener in self.get_listeners(event.name):
            value = listener(event, value)
        event.return_value = value
        return event

    def _async_filter(self, listeners, event, value, callback):
        """
        Filters given value using given event in asynchronous manner
        """
        try:
            listeners.next()(event, value, partial(self._async_filter, \
                listeners, event, callback=callback))
        except StopIteration:
            event.return_value = value
            callback(event)


class Listener(object):
    """
    Class that simplifies attaching listeners
    """

    def register(self, dispatcher):
        """
        Registers event listeners to given dispatcher
        """
        self.dispatcher = dispatcher

        for t in self.mapping():
            try:
                priority = t[2]
            except IndexError:
                priority = 100
            dispatcher.attach(t[0], t[1], priority)

    def mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        raise NotImplementedError('Return list of tuples with ' +\
            '(event, callback priority) mappings')


def synchronous(function):
    """
    Decorator that marks event listeners as synchronous
    It allows handling callback (passed when event is invoced asynchronously)
    """
    @wraps(function)
    def wrapper(self, event, *args, **kwargs):
        callback = None
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        ret = function(self, event, *args, **kwargs)
        if callback:
            callback(ret)
        return ret
    return wrapper


def asynchronous(function):
    """
    Decorator that marks event listeners as asynchronous
    It raises exception when callback is not passed!
    """
    @wraps(function)
    def wrapper(self, event, *args, **kwargs):
        if not 'callback' in kwargs:
            raise RuntimeError('"callback" is required when calling %s' % \
                function)
        function(self, event, *args, **kwargs)
    return wrapper
