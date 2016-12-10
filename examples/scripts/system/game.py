import entityx
from _entityx_components import Body, Renderable, InputResponder, Destroyed
from gamemath import vector2
from system.tile import Tile, TileType, Stats, Upgrade
import sys
Vector2 = vector2.Vector2

TILESIZE_X = 32
TILESIZE_Y = 32

class Game(entityx.Entity):
    def __init__(self):
        self.staticMap = [[None]*5 for i in range(5)]
        self.moveableMap = [[None]*5 for i in range(5)]
        self.inputResponder = self.Component(InputResponder)
        
        self.GenerateLevelLayout([[TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall], 
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall]]);
                
        self.nickCage = Tile(TileType.nickCage, 1, 1, Stats(5, 1))
        self.moveableMap[1][1] = self.nickCage
        self.moveableMap[2][1] = Tile(TileType.chest, 2, 1, upgrade = Upgrade(1, 1))
        self.moveableMap[1][2] = Tile(TileType.clue, 1, 2)

    def update(self, dt):
        # Move Nick Cage based on InputResponder
        input_events = self.inputResponder.responds
        if "-MoveUp" in input_events:
            print "Move Up"
            self.nickCage.body.direction.x = 0
            self.nickCage.body.direction.y = -1
        if "-MoveDown" in input_events:
            print "Move Down"
            self.nickCage.body.direction.x = 0
            self.nickCage.body.direction.y = 1
        if "-MoveRight" in input_events:
            print "Move Right"
            self.nickCage.body.direction.x = 1
            self.nickCage.body.direction.y = 0
        if "-MoveLeft" in input_events:
            print "Move Left"
            self.nickCage.body.direction.x = -1
            self.nickCage.body.direction.y = 0
        
        # Damage loop. If damage is dealt, indicate that the tile cannot move
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None:
                    # Calculate the new tile position
                    newTileX = tile.gameBody.x + int(tile.body.direction.x)
                    newTileY = tile.gameBody.y + int(tile.body.direction.y)
                    tileInNewPosition = self.moveableMap[newTileX][newTileY]
                    if tileInNewPosition != None and tileInNewPosition != tile:
                        if tileInNewPosition.stats != None and tile.stats != None:
                            # Do damage to each other
                            tileInNewPosition.stats.health -= tile.stats.weapon
                            tile.stats.health -= tileInNewPosition.stats.weapon
                            if tile.stats.health <= 0:
                                tile.destroyed = tile.Component(Destroyed)
                            if tileInNewPosition.stats.health <= 0:
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed)
                            tileInNewPosition.gameBody.canMove = False
                            tile.gameBody.canMove = False
                        else:
                            print "Collision detected with non-stat entity!"
                            if tileInNewPosition != None and tileInNewPosition.upgrade != None:
                                print "Upgrade obtained!"
                                tile.stats.health += tileInNewPosition.upgrade.health
                                tile.stats.weapon += tileInNewPosition.upgrade.weapon
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed) # Destroy the upgrade (single-use)
                                tile.gameBody.x = newTileX
                                tile.gameBody.y = newTileY
                                tile.gameBody.canMove = True
                            elif self.staticMap[newTileX][newTileY].tileType != TileType.wall:
                                tile.gameBody.x = newTileX
                                tile.gameBody.y = newTileY
                                tile.gameBody.canMove = True
                            else:
                                print "Trying to wall hack?"
                                tile.gameBody.canMove = False
                    elif tileInNewPosition != tile:
                        tile.gameBody.canMove = True
                    else:
                        tile.gameBody.canMove = False
                        
        # Movement loop. If the tile can move, do it.
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None:
                    if tile.gameBody.canMove == True:
                        # Sync the map to wherever the entity thinks it is
                        self.moveableMap[tile.gameBody.x][tile.gameBody.x] = tile
                        self.moveableMap[x][y] = None
                    else:
                        # Revert any movement that may have tried to occur
                        tile.gameBody.x = x
                        tile.gameBody.y = y
                        
                    # Sync the physical body based on the tile position
                    tile.body.position.x = tile.gameBody.x * TILESIZE_X
                    tile.body.position.y = tile.gameBody.y * TILESIZE_Y
    
    def GenerateLevelLayout(self, tileMap):
        for x in range(0, len(tileMap)):
            for y in range(0, len(tileMap[x])):
                self.staticMap[x][y] = Tile(tileMap[x][y], x, y)