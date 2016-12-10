import entityx
from _entityx_components import Body, Renderable
from gamemath import vector2
import sys
Vector2 = vector2.Vector2

TILESIZE_X = 32
TILESIZE_Y = 32

class Tile(entityx.Entity):
    def __init__(self, tileType, tileX, tileY, stats = None):
        self.body = self.Component(Body)
        self.body.x = tileX * TILESIZE_X
        self.body.y = tileY * TILESIZE_Y
        self.stats = stats
        self.gameBody = GameBody()
        self.gameBody.x = tileX
        self.gameBody.y = tileY
        self.tileType = tileType

    def update(self, dt):
        # Do nothing.
        self.updated = True
        
class Stats(object):
    def __init__(self, health = 0, weapon = 1):
        self.health = health
        self.weapon = weapon

    def update(self, dt):
        # Do nothing.
        self.updated = True
        
class GameBody(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.canMove = True

    def update(self, dt):
        # Do nothing.
        self.updated = True
        
class TileType(object):
    wall = 1
    floor = 2
    door = 3
    chest = 4
    clue = 5
    lava = 6
    nickCage = 7
    fbi = 8