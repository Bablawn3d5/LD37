'''
Stolen from LD36 Project
'''

import entityx
from _entityx_components import Body, Renderable, Destroyed, Sound
from gamemath import vector2
import re
import math


class EventID(object):
    error, level_start, combat, upgrade, combat_lava = range(0,5) 

class Event(object):
    def __eq__(self,other):
        if other is None:
            return False
        return self.event_text == other.event_text

    def __init__(self, string, delay = 0, length = 0.25):
        assert string is not None, "wtf did you pass into event(string)?"
        self.delay = delay
        self.old_count = 0
        self.event_current = 0
        self.event_final = length
        self.event_text = string
        self.is_rendering = True
        self.sound_player_prog = re.compile("[AEIOUaeiouYyZzHhMmTtfF.-]")

    def play(self,dt):
        # Wait till we can print
        if (self.delay > 0 ):
            self.delay -= dt
            return ""

        # Print
        if self.is_rendering:
            self.event_current += dt
            if self.event_current >= self.event_final:
                self.is_rendering = False
            percent =  min(1,self.event_current / self.event_final)
            char_disp_count = int(percent * len(self.event_text))
            new_chars = self.event_text[self.old_count:char_disp_count]
            # If there's a character that matches the regex, play a sound
            if self.sound_player_prog.search(new_chars):
                e = entityx.Entity()
                e.death = e.Component(Destroyed)
                e.death.timer = 1
                sound = e.Component(Sound)
                sound.name = "./sounds/boop.wav"
            self.old_count = char_disp_count
            return self.event_text[:char_disp_count]
        return self.event_text

class EventController(entityx.Entity):
    NUMBER_OF_EVENTS = 5

    def __init__(self):
        self.body = self.Component(Body)
        self.rend = self.Component(Renderable)
        self.rend.layer = 10
        self.rend.font = "./images/arial.ttf"
        self.rend.fontString = ""
        self.rend.fontSize = 24
        self.rend.r = 240
        self.rend.g = 240
        self.rend.b = 180
        self.rend.a = 250
        # Support for 5 events because thats how many
        # height we gots
        self.events = [None] * EventController.NUMBER_OF_EVENTS
        self.event_text = [""]*EventController.NUMBER_OF_EVENTS
        self.rainbow_text = False
        self.dt = 0

        self.events_seen = []

    def setColor(self, level):
        self.rainbow_text = False
        if level == 1:
            self.rend.r = 200
            self.rend.g = 170
            self.rend.b = 160
            self.rend.a = 200
        if level == 2:
            self.rend.r = 200
            self.rend.g = 150
            self.rend.b = 130
            self.rend.a = 200
        if level == 3:
            self.rend.r = 210
            self.rend.g = 140
            self.rend.b = 130
            self.rend.a = 200
        if level == 4:
            self.rend.r = 210
            self.rend.g = 130
            self.rend.b = 120
            self.rend.a = 200
        if level == 5:
            self.rend.r = 230
            self.rend.g = 120
            self.rend.b = 100
            self.rend.a = 200
        if level == 6:
            self.rend.r = 230
            self.rend.g = 110
            self.rend.b = 95
            self.rend.a = 200
        if level == 7:
            self.rend.r = 230
            self.rend.g = 90
            self.rend.b = 70
            self.rend.a = 200
        if level == 8:
            self.rend.r = 230
            self.rend.g = 90
            self.rend.b = 70
            self.rend.a = 200
            self.rainbow_text = True

    def update(self, dt):
        for i in range(0, EventController.NUMBER_OF_EVENTS):
            if(self.events[i] != None):
                self.event_text[i]= self.events[i].play(dt)
        self.rend.fontString = "\n".join(self.event_text)
        if self.rainbow_text:
            self.dt += min(0.00055,dt)
            cur = self.dt * math.pi
            self.rend.r = max( 20, int(abs(255 * math.sin(cur)) + 20) )
            self.rend.g = max( 0, int(abs(255 * (math.sin(cur/2)))) )
            self.rend.b = max( 5, int(abs(255 * math.cos(cur)) + 20) )
        self.rend.dirty = True

    def flushEvents(self):
        self.events = [None] * EventController.NUMBER_OF_EVENTS

    def playEvent(self, event):
        try:
            none_index = self.events.index(None)
            self.events[none_index]=event
        except ValueError:
            self.events.pop(0)
            self.events.append(event)

