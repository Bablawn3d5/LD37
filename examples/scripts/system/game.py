import entityx
from _entityx_components import Body, Renderable, InputResponder, Destroyed
from gamemath import vector2
from system.tile import Tile, TileType, Stats, Upgrade
import sys
import Queue
import time
import collections
Vector2 = vector2.Vector2

TILESIZE_X = 32
TILESIZE_Y = 32

GameCoord = collections.namedtuple("GameCoord", "x y")

class Game(entityx.Entity):
    def __init__(self):
        self.staticMap   = [[None]*9 for i in range(5)]
        self.moveableMap = [[None]*9 for i in range(5)]
        self.fogofwar    = [[None]*9 for i in range(5)]
        self.inputResponder = self.Component(InputResponder)
        self.level = 1
        self.lightLevel = 2
        
        self.GenerateLevelLayout(self.staticMap, [[TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall], 
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
                            [TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall]]);
        # Cover everything in fog tiles
        self.GenerateLevelLayout(self.fogofwar, [[TileType.fow3]*9 for i in range(5)])

        self.nickCage = Tile(TileType.nickCage, 1, 1, Stats(5, 1))
        self.moveableMap[1][1] = self.nickCage
        self.moveableMap[2][1] = Tile(TileType.chest, 2, 1, upgrade = Upgrade(1, 1))
        self.moveableMap[1][2] = Tile(TileType.clue, 1, 2, upgrade = Upgrade(level = 1))
        self.moveableMap[2][4] = Tile(TileType.door, 2, 4, stats = Stats(0,0))
        self.moveableMap[3][6] = Tile(TileType.fbi, 3, 6, stats = Stats(2,1))

    # Returns true if a given gameTileX gameTileY is occupied by items in types
    def isOccupied(self, tileX, tileY, types = [TileType.wall, TileType.door]):
        return (self.moveableMap[tileX][tileY] != None and self.moveableMap[tileX][tileY].tileType in types) or (self.staticMap[tileX][tileY] != None and self.staticMap[tileX][tileY].tileType in types)

    def bfs(self, start, end):
        frontier = Queue.Queue()
        frontier.put(start)
        came_from = {}
        came_from[start] = None
        while not frontier.empty():
            current = frontier.get()
            if current == end:
                break
                
            left = GameCoord(current.x - 1,current.y)
            right = GameCoord(current.x + 1,current.y)
            up = GameCoord(current.x ,current.y - 1)
            down = GameCoord(current.x,current.y + 1)
            if not self.isOccupied(left.x, left.y) and not came_from.has_key(left):
                came_from[left] = current
                frontier.put(left)
            if not self.isOccupied(right.x, right.y) and not came_from.has_key(right):
                came_from[right] = current
                frontier.put(right)
            if not self.isOccupied(up.x, up.y) and not came_from.has_key(up):
                came_from[up] = current
                frontier.put(up)
            if not self.isOccupied(down.x, down.y) and not came_from.has_key(down):
                came_from[down] = current
                frontier.put(down)
        return came_from
        
    def getPath(self, start, end):
        came_from = self.bfs(start, end)
        if not end in came_from.keys():
            print "No AI path found!"
            return None
        current = end
        path = [end]
        while not current == start:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
        
    def update(self, dt):
        # Move Nick Cage based on InputResponder
        self.nickCage.body.direction.x = 0
        self.nickCage.body.direction.y = 0
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

        # Update fog of war based on NC's position
        for x in range(0, len(self.fogofwar)):
            for y in range(0, len(self.fogofwar[x])):
                dist2 = (x - self.nickCage.gameBody.x)**2 + (y -self.nickCage.gameBody.y) ** 2 
                if( dist2 < self.lightLevel + 2 ):
                    self.fogofwar[x][y].setTile(TileType.fow0)
                elif( dist2 < self.lightLevel + 5 ):
                    self.fogofwar[x][y].setTile(TileType.fow1)
                elif( dist2 < self.lightLevel + 10 ):
                    self.fogofwar[x][y].setTile(TileType.fow2)
                else:
                    self.fogofwar[x][y].setTile(TileType.fow3)

        if self.nickCage.body.direction.x == 0 and self.nickCage.body.direction.y == 0:
            return # Nothing more to do for this frame

        # Calculate the direction of FBI (AI)
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None and tile.tileType == TileType.fbi:
                    path = self.getPath(GameCoord(tile.gameBody.x, tile.gameBody.y), GameCoord(self.nickCage.gameBody.x, self.nickCage.gameBody.y))
                    print str(path)
                    if path != None and len(path) > 1:
                        tile.body.direction.x = path[1].x - tile.gameBody.x
                        tile.body.direction.y = path[1].y - tile.gameBody.y
                    else:
                        tile.body.direction.x = 0
                        tile.body.direction.y = 0
                    
        
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
                            print "Combat detected."
                            tileInNewPosition.stats.health -= tile.stats.weapon
                            tile.stats.health -= tileInNewPosition.stats.weapon
                            # Destroy entities if <= 0 HP, and manually cleanup the map
                            # since we only reconcile changes if movement happens (below)
                            if tile.stats.health <= 0:
                                tile.destroyed = tile.Component(Destroyed)
                                self.moveableMap[x][y] = None
                            if tileInNewPosition.stats.health <= 0:
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed)
                                self.moveableMap[newTileX][newTileY] = None
                            tileInNewPosition.gameBody.canMove = False
                            tile.gameBody.canMove = False
                        else:
                            print "Collision detected with non-stat entity!"
                            if tileInNewPosition != None and tileInNewPosition.upgrade != None:
                                print "Upgrade obtained!"
                                tile.stats.health += tileInNewPosition.upgrade.health
                                tile.stats.weapon += tileInNewPosition.upgrade.weapon
                                self.level += tileInNewPosition.upgrade.level
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed) # Destroy the upgrade (single-use)
                                tile.gameBody.canMove = True
                    elif tileInNewPosition == None and self.staticMap[newTileX][newTileY].tileType != TileType.wall:
                        print "Normal movement detected."
                        tile.gameBody.canMove = True
                    else:
                        tile.gameBody.canMove = False
                    
                    if tile.gameBody.canMove:
                        tile.gameBody.x = newTileX
                        tile.gameBody.y = newTileY
                    
        
        # Reset all updated flags before doing movement
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None:
                    tile.gameBody.updated = False
        
        # Movement loop. If the tile can move, do it.
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None and tile.gameBody.updated == False:
                    if tile.gameBody.canMove == True:
                        # Sync the map to wherever the entity thinks it is
                        print "Syncing map with entity position"
                        self.moveableMap[tile.gameBody.x][tile.gameBody.y] = tile
                        self.moveableMap[x][y] = None
                    else:
                        # Revert any movement that may have tried to occur
                        tile.gameBody.x = x
                        tile.gameBody.y = y
                        
                    # Sync the physical body based on the tile position
                    tile.body.position.x = tile.gameBody.x * TILESIZE_X
                    tile.body.position.y = tile.gameBody.y * TILESIZE_Y
                    tile.gameBody.updated = True
    
    def GenerateLevelLayout(self, targetMap, tileMap):
        for x in range(0, len(tileMap)):
            for y in range(0, len(tileMap[x])):
                targetMap[x][y] = Tile(tileMap[x][y], x, y)