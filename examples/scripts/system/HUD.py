import entityx
from _entityx_components import Body, Renderable
from system.game import Game
from system.tile import TileType
from system.eventur import EventController, Event, EventID
import sys

HUD_TILE_X = 32
HUD_TILE_Y = 32
SCREEN_X = 1024
SCREEN_Y = 768
HUD_X = 0
HUD_Y = 608

class HUD_TEXT(entityx.Entity):
    def __init__(self, string):
        self.body = self.Component(Body)
        self.rend = self.Component(Renderable)
        self.rend.layer = 10
        self.rend.font = "./images/arial.ttf"
        self.rend.fontString = ""
        self.rend.fontSize = 24
        self.text = str(string)
        self.rend.r = 250
        self.rend.g = 250
        self.rend.b = 210
        self.rend.a = 255
        self.rend.dirty = True

    def update(self, dt):
        self.rend.fontString = str(self.text)
        self.rend.dirty = True

    def position(self, x, y):
        self.body.position.x = x
        self.body.position.y = y

class HUD(entityx.Entity):
    def __init__(self):
        self.HP = HUD_TEXT(10)
        self.HP.position(HUD_X + HUD_TILE_X * 3, HUD_Y)

        self.ATTACK = HUD_TEXT(10)
        self.ATTACK.position(HUD_X + HUD_TILE_X * 3, HUD_Y + HUD_TILE_Y * 1)

        self.LIGHT = HUD_TEXT(10)
        self.LIGHT.position(HUD_X + HUD_TILE_X * 3, HUD_Y + HUD_TILE_Y * 2)

        self.LEVEL = HUD_TEXT(10)
        self.LEVEL.position(HUD_X + HUD_TILE_X * 3, HUD_Y + HUD_TILE_Y * 3)
        self.eventController = EventController()
        self.eventController.body.position.x = HUD_X + HUD_TILE_X * 6
        self.eventController.body.position.y = HUD_Y
        self.game = Game(self)

    def update(self, dt):
        self.HP.text     = self.game.nickCage.stats.health
        self.ATTACK.text = self.game.nickCage.stats.weapon
        self.LIGHT.text  = self.game.nickCage.stats.lightlevel
        self.LEVEL.text  = "%i/%i" % (self.game.level, self.game.totalClues)

    def signal(self, event, items = []):
        if(event == EventID.level_start):
            self.eventController.playEvent(Event("Nick: This must be the spot! I just need to find %i clues and get outta here.\nI'm one step closer to finding 'the one room'." % (items[0])))
        elif(event == EventID.combat ):
            name = items[0].getName()
            dmg  = items[1]
            self.eventController.playEvent(Event("[Combat] %s took %i damage" % (name, dmg)))
            if(name == "Nick"):
                self.eventController.playEvent(Event("Nick: TAKE THAT!"))
        elif(event == EventID.upgrade ):
            self.eventController.playEvent(Event("Nick: Oh that thing looks like will help in combat"))
        elif(event == EventID.combat_lava ):
            name = items[0].getName()
            dmg  = items[1]
            self.eventController.playEvent(Event("[Combat] %s took %i damage" % (name, dmg)))
            self.eventController.playEvent(Event("Nick: Ouch! that lava looks like it is hot stuff"))
        else:
            print "Unhandled event: " + str(event)