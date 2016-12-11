import entityx
from _entityx_components import Body, Renderable, InputResponder, Destroyed
from gamemath import vector2
from system.tile import Tile, TileType, Stats, Upgrade
from random import randint
import sys
import Queue
import time
import collections
Vector2 = vector2.Vector2

TILESIZE_X = 32
TILESIZE_Y = 32

MAX_ROOM_WIDTH = 10
MIN_ROOM_WIDTH = 5
MAX_ROOM_HEIGHT = 10
MIN_ROOM_HEIGHT = 5

LEVEL_WIDTH = 32
LEVEL_HEIGHT = 25

GameCoord = collections.namedtuple("GameCoord", "x y")

class RoomInfo(object):
    def __init__(self, width, height, x, y):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        
    def __repr__(self):
        return "x: " + str(self.x) + " y: " + str(self.y) + " w: " + str(self.width) + " h: " + str(self.height)
        
    def intersects(self, other):
        return self.x <= (other.x + other.width) and (self.x + self.width) >= other.x and self.y <= (other.y + other.height) and (self.y + self.height) >= other.y
        
    def range_overlap(self, a_min, a_max, b_min, b_max):
        return (a_min <= b_max) and (b_min <= a_max)
        
    def center(self):
        return GameCoord(int((2*self.x + self.width)/2), int((2*self.y + self.height)/2));

class Game(entityx.Entity):
    def __init__(self):
        #self.staticMap   = [[None]*9 for i in range(5)]
        self.staticMap   = [[TileType.wall]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        #self.moveableMap = [[None]*9 for i in range(5)]
        self.moveableMap = [[None]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        #self.fogofwar    = [[None]*9 for i in range(5)]
        self.fogofwar    = [[None]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        self.inputResponder = self.Component(InputResponder)
        self.level = 1
        self.lightlevel = 1
        
        #self.GenerateLevelLayout(self.staticMap, [[TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall], 
        #                    [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall, TileType.lava, TileType.floor, TileType.floor, TileType.wall],
        #                    [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
        #                    [TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall, TileType.floor, TileType.floor, TileType.floor, TileType.wall],
        #                    [TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall, TileType.wall]]);
        # Cover everything in fog tiles
        #self.moveableMap[1][1] = self.nickCage
        #self.moveableMap[2][1] = Tile(TileType.chest, 2, 1, upgrade = Upgrade(1, 1))
        #self.moveableMap[1][2] = Tile(TileType.clue, 1, 2, upgrade = Upgrade(level = 1))
        #self.moveableMap[2][4] = Tile(TileType.door, 2, 4, stats = Stats(0,0))
        #self.moveableMap[3][6] = Tile(TileType.fbi, 3, 6, stats = Stats(2,1))
        
        self.GenerateLevel(3)
        
        spawnRoom = self.rooms[randint(0, len(self.rooms) - 1)];
        spawnX = randint(spawnRoom.x + 1, spawnRoom.x + spawnRoom.width - 1)
        spawnY = randint(spawnRoom.y + 1, spawnRoom.y + spawnRoom.height - 1)
        self.nickCage = Tile(TileType.nickCage, spawnX, spawnY, Stats(10, 1))
        self.moveableMap[spawnX][spawnY] = self.nickCage
        
        self.GenerateLevelLayout(self.staticMap, self.staticMap)
        self.GenerateLevelLayout(self.fogofwar, [[TileType.fow3]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)])

    # Returns true if a given gameTileX gameTileY is occupied by items in types
    def isOccupied(self, tileX, tileY, types = [TileType.wall, TileType.door]):
        return (self.moveableMap[tileX][tileY] != None and self.moveableMap[tileX][tileY].tileType in types) or (self.staticMap[tileX][tileY] != None and self.staticMap[tileX][tileY].tileType in types)

    def GenerateLevel(self, numRooms):
        self.rooms = []
        for i in range(0, numRooms):
            failed = True
            while failed:
                width = MIN_ROOM_WIDTH + randint(0, MAX_ROOM_WIDTH - MIN_ROOM_WIDTH + 1)
                height = MIN_ROOM_HEIGHT + randint(0, MAX_ROOM_HEIGHT - MIN_ROOM_HEIGHT + 1)
                x = randint(0, LEVEL_WIDTH - width - 1) + 1
                y = randint(0, LEVEL_HEIGHT - height - 1) + 1
                room = RoomInfo(width, height, x , y)
                
                failed = False
                for j in range(0, len(self.rooms)):
                    if room.intersects(self.rooms[j]):
                        failed = True
                        break
                        
                if not failed:
                    # clear out the room in the static map
                    for x in range(room.x, room.x + room.width):
                        for y in range(room.y, room.y + room.height):
                            self.staticMap[x][y] = TileType.floor
                            
                    if len(self.rooms) != 0:
                        # clear out hallways
                        prevRoom = self.rooms[len(self.rooms) - 1]
                        prevRoomCenter = prevRoom.center();
                        newRoomCenter = room.center();
                        print str(prevRoomCenter) + " " + str(newRoomCenter)
                        
                        if randint(0, 2) == 1:
                            self.placeHorizontalHallway(prevRoomCenter.x, newRoomCenter.x, prevRoomCenter.y)
                            #self.placeHorizontalHallway2(prevRoom, room)
                            self.placeVerticalHallway(prevRoomCenter.y, newRoomCenter.y, newRoomCenter.x)
                            #self.placeVerticalHallway2(prevRoom, room)
                        else:
                            self.placeVerticalHallway(prevRoomCenter.y, newRoomCenter.y, newRoomCenter.x)
                            #self.placeVerticalHallway2(prevRoom, room)
                            self.placeHorizontalHallway(prevRoomCenter.x, newRoomCenter.x, prevRoomCenter.y)
                            #self.placeHorizontalHallway2(prevRoom, room)
                        
                    self.rooms.append(room)
                    print room
    
    def placeHorizontalHallway(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.staticMap[x][y] = TileType.floor
    
    # This function attempts to place doors (broken)
    def placeHorizontalHallway2(self, r1, r2):
        r1Center = r1.center()
        r2Center = r2.center()
        for x in range(min(r1Center.x, r2Center.x), max(r1Center.x, r2Center.x) + 1):
            if x == r1.x + r1.width or x == r2.x + r2.width:
                self.moveableMap[x][r1Center.y] = Tile(TileType.door, x, r1Center.y, stats = Stats(0,0))
            self.staticMap[x][r1Center.y] = TileType.floor
            
    def placeVerticalHallway(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.staticMap[x][y] = TileType.floor
    
    # This function attempts to place doors (broken)
    def placeVerticalHallway2(self, r1, r2):
        r1Center = r1.center()
        r2Center = r2.center()
        for y in range(min(r1Center.y, r2Center.y), max(r1Center.y, r2Center.y) + 1):
            if y == r1.y + r1.height or y == r2.y + r2.height:
                self.moveableMap[r2Center.x][y] = Tile(TileType.door, r2Center.x, y, stats = Stats(0,0))
            self.staticMap[r2Center.x][y] = TileType.floor
    
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

        # Update fog of war based on NC's position
        for x in range(0, len(self.fogofwar)):
            for y in range(0, len(self.fogofwar[x])):
                lit_obj = self.nickCage
                dist2 = (x - lit_obj.gameBody.x)**2 + (y -lit_obj.gameBody.y) ** 2 
                if( dist2 < lit_obj.stats.lightlevel + 3 ):
                    self.fogofwar[x][y].setTile(TileType.fow0)
                elif( dist2 < lit_obj.stats.lightlevel + 5 ):
                    self.fogofwar[x][y].setTile(TileType.fow1)
                elif( dist2 < lit_obj.stats.lightlevel + 10 ):
                    self.fogofwar[x][y].setTile(TileType.fow2)
                else:
                    if(self.fogofwar[x][y].tileType == TileType.fow3):
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
                                tile.stats.lightlevel += tileInNewPosition.upgrade.lightlevel
                                self.level += tileInNewPosition.upgrade.level
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed) # Destroy the upgrade (single-use)
                                self.moveableMap[newTileX][newTileY] = None
                                tile.gameBody.canMove = True
                    elif tileInNewPosition == None and self.staticMap[newTileX][newTileY].tileType != TileType.wall:
                        if self.staticMap[newTileX][newTileY].tileType == TileType.lava:
                            tile.stats.health -= self.staticMap[newTileX][newTileY].stats.weapon
                            if tile.stats.health <= 0:
                                tile.destroyed = tile.Component(Destroyed)
                                self.moveableMap[x][y] = None
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
                    if tile.gameBody.canMove == True and self.moveableMap[tile.gameBody.x][tile.gameBody.y] == None:
                        # Sync the map to wherever the entity thinks it is
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
                if tileMap[x][y] == TileType.lava:
                     targetMap[x][y] = Tile(tileMap[x][y], x, y, stats = Stats(0, 2))
                else:
                    targetMap[x][y] = Tile(tileMap[x][y], x, y)