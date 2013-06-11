# -*- coding: utf-8 -*-

# Copyright (C) 2007-2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


class Pubsub(object):
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, topic, callback):
        self._subscribers.setdefault(topic, []).append(callback)

    def publish(self, topic, message):
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                callback(message)

    def unsubscribe(self, topic, callback):
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)
            if len(self._subscribers[topic]) == 0:
                self._subscribers.pop(topic)
