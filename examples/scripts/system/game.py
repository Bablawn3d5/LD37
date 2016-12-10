import entityx
from _entityx_components import Body, Renderable, InputResponder
from gamemath import vector2
from system.tile import Tile, TileType, Stats
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
        self.moveableMap[2][1] = Tile(TileType.chest, 2, 1)
        self.moveableMap[1][2] = Tile(TileType.clue, 1, 2)

    def update(self, dt):
        # Move Nick Cage based on InputResponder
        input_events = self.inputResponder.responds
        if "-MoveUp" in input_events:
            self.nickCage.body.direction.x = 0
            self.nickCage.body.direction.y = -1
        if "-MoveDown" in input_events:
            self.nickCage.body.direction.x = 0
            self.nickCage.body.direction.y = 1
        if "-MoveRight" in input_events:
            self.nickCage.body.direction.x = 1
            self.nickCage.body.direction.y = 0
        if "-MoveLeft" in input_events:
            self.nickCage.body.direction.x = -1
            self.nickCage.body.direction.y = 0
        
        # Damage loop. If damage is dealt, indicate that the tile cannot move
        for x in range(0, len(self.moveableMap)-1):
            for y in range(0, len(self.moveableMap[x])-1):
                tile = self.moveableMap[x][y]
                if tile != None:
                    # Calculate the new tile position
                    newTileX = tile.gameBody.x + int(tile.body.direction.x)
                    newTileY = tile.gameBody.y + int(tile.body.direction.y)
                    tileInNewPosition = self.moveableMap[newTileX][newTileY]
                    if tileInNewPosition != None:
                        if tileInNewPosition.stats != None and tile.stats != None:
                            # Do damage to each other
                            tileInNewPosition.gameBody.canMove = False
                            tile.gameBody.canMove = False
                        else:
                            if self.staticMap[newTileX][newTileY].tileType != TileType.wall:
                                tile.gameBody.x = newTileX
                                tile.gameBody.y = newTileY
                                tile.gameBody.canMove = True
                            else:
                                tile.gameBody.canMove = False
                    else:
                        tile.gameBody.canMove = True
                        
        # Movement loop. If the tile can move, do it.
        for x in range(0, len(self.moveableMap)-1):
            for y in range(0, len(self.moveableMap[x])-1):
                tile = self.moveableMap[x][y]
                if tile != None and tile.gameBody.canMove == True:
                    self.moveableMap[tile.gameBody.x][tile.gameBody.x] = tile
                    self.moveableMap[x][y] = None
                        
                    # Sync the physical body based on the new tile position
                    tile.body.position.x = tile.gameBody.x * TILESIZE_X
                    tile.body.position.y = tile.gameBody.y * TILESIZE_Y
    
    def GenerateLevelLayout(self, tileMap):
        for x in range(0, len(tileMap)-1):
            for y in range(0, len(tileMap[x])-1):
                self.staticMap[x][y] = Tile(tileMap[x][y], x, y)