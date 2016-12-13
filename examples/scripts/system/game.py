import entityx
from _entityx_components import Body, Renderable, InputResponder, Destroyed
from gamemath import vector2
from system.tile import Tile, TileType, Stats, Upgrade
from system.eventur import EventID
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

LEVEL_WIDTH = 34
LEVEL_HEIGHT = 27

GameCoord = collections.namedtuple("GameCoord", "x y")

class RoomInfo(object):
    def __init__(self, width, height, x, y):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        
    def __repr__(self):
        return "x: " + str(self.x) + " y: " + str(self.y) + " w: " + str(self.width) + " h: " + str(self.height)

    def isOnEdge(self, cord):
        return (
                # Is on left or right edge
                (((self.x-1 == cord.x) or (self.x + self.width == cord.x)) and (self.y-1 <= cord.y and cord.y <= self.y +1 + self.height)) or 
                # Is on top or bottom edge
                (((self.y-1 == cord.y) or (self.y + self.height == cord.y)) and (self.x-1 <= cord.x and cord.x <= self.x +1 + self.width))
                ) 
        
    def intersects(self, other):
        return self.x <= (other.x + other.width) and (self.x + self.width) >= other.x and self.y <= (other.y + other.height) and (self.y + self.height) >= other.y
        
    def range_overlap(self, a_min, a_max, b_min, b_max):
        return (a_min <= b_max) and (b_min <= a_max)
        
    def center(self):
        return GameCoord(int((2*self.x + self.width)/2), int((2*self.y + self.height)/2));

    # Returns a random xy for a given room
    def randomXY(self):
        spawnX = randint(self.x + 1, self.x + self.width - 1)
        spawnY = randint(self.y + 1, self.y + self.height - 1)
        return GameCoord(spawnX, spawnY)

class Game(entityx.Entity):
    # Tile that is the center of the playing area
    SCREEN_TILE_CENTER_X = 16
    SCREEN_TILE_CENTER_Y = 8

    def __init__(self, event_signal):
        self.staticMap   = [[TileType.wall]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        self.moveableMap = [[None]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        self.fogofwar    = [[None]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)]
        self.inputResponder = self.Component(InputResponder)
        self.level = 0
        self.totalClues = 0
        # Generate five random rooms
        self.rooms = self.GenerateLevel([None,None,None,None,RoomInfo(3,3,1,1)]) 
        print str(self.rooms)

        # clear out the room in the static map
        for room in self.rooms:
            for x in range(room.x, room.x + room.width):
                for y in range(room.y, room.y + room.height):
                    if randint(0, 10) == 1:
                        self.staticMap[x][y] = TileType.lava
                    else:
                        self.staticMap[x][y] = TileType.floor
                        
        # Connect rooms together with hallways
        for i in range(1,len(self.rooms)):
            # Connect previous room to newest room
            room = self.rooms[i]
            prevRoom = self.rooms[i-1]
            print "id:%i, x: %i, x2: %i" % (i, room.x,prevRoom.x)
            self.connectRooms(prevRoom, room)

        spawnRoom = self.rooms[-1]
        self.GenerateLevelLayout(self.staticMap, self.staticMap)
        self.GenerateLevelLayout(self.fogofwar, [[TileType.fow3]*LEVEL_WIDTH for i in range(LEVEL_WIDTH)])
        
        spawn = spawnRoom.center()
        self.nickCage = self.addMoveable( Tile(TileType.nickCage, spawn.x, spawn.y, Stats(10, 1, light = 1)) )
        self.addClue(spawn.x, spawn.y-1)
        self.addMoveable( Tile(TileType.chest, spawn.x+1, spawn.y, upgrade = Upgrade(5, 1)) )
        self.addMoveable( Tile(TileType.torch, spawn.x+1, spawn.y+1, upgrade = Upgrade(light = 1)) )
        self.addMoveable( Tile(TileType.torch, spawn.x-1, spawn.y+1, upgrade = Upgrade(light = 1)) )
        self.event = event_signal
        self.event.signal(EventID.level_start, [self.totalClues])
        self.sync_bodies(-1*self.nickCage.gameBody.x + Game.SCREEN_TILE_CENTER_X, -1*self.nickCage.gameBody.y + Game.SCREEN_TILE_CENTER_Y)

    def addClue(self, x, y):
        self.addMoveable( Tile(TileType.clue, x, y, upgrade = Upgrade(level=1)))
        self.totalClues += 1

    def addMoveable(self, tile):
        assert self.moveableMap[tile.gameBody.x][tile.gameBody.y] == None, "Attempted to add tile that's already occupied in the map."
        self.moveableMap[tile.gameBody.x][tile.gameBody.y] = tile
        return tile

    # Returns true if the moveable map at tileX, tileY is occupied by any of tpyes
    def isMoveableOccupied(self, tileX, tileY, types = [TileType.wall, TileType.door]):
        return (self.moveableMap[tileX][tileY] != None and self.moveableMap[tileX][tileY].tileType in types)

    # Returns true if a given gameTileX gameTileY is occupied by items in types
    def isOccupied(self, tileX, tileY, types = [TileType.wall, TileType.door]):
        return ( self.isMoveableOccupied(tileX, tileY, types) or 
                (self.staticMap[tileX][tileY] != None and self.staticMap[tileX][tileY].tileType in types))

    # Generates a bunch of rooms that will produce a 'level' containing a bunch of rooms.
    # Rooms are garanteed to not overlap, and not spawn beside eachother.
    def GenerateLevel(self, rooms, maxAttempts = 200):
        genRooms = []
        attempts = 0
        for room in rooms:
            failed = True
            randomRoom = False
            # If user passes in 'none' in room type, then generate a random room.
            if room is None:
                randomRoom = True
            while failed and attempts <= maxAttempts:
                attempts += 1
                if randomRoom == True:
                    width = MIN_ROOM_WIDTH + randint(0, MAX_ROOM_WIDTH - MIN_ROOM_WIDTH + 1)
                    height = MIN_ROOM_HEIGHT + randint(0, MAX_ROOM_HEIGHT - MIN_ROOM_HEIGHT + 1)
                    room = RoomInfo(width, height, 0 , 0)
                # Randomly move the room around the level, don't place room on top or bottom edges
                room.x = randint(2, LEVEL_WIDTH - width - 3)
                room.y = randint(2, LEVEL_HEIGHT - height - 3)
                
                failed = False
                # Check to see if the room fits on the map using the x,y cordinates chosen
                for oldRoom in genRooms:
                    if room.intersects(oldRoom):
                        failed = True
                        break
                        
                if not failed:
                    genRooms.append(room)
        return genRooms

    # Joins room one with room two with a hallway
    def connectRooms(self, roomOne, roomTwo):                        
        prevRoomCenter = roomOne.center()
        newRoomCenter = roomTwo.center()                    
        # Randomly join rooms verticaly or horizontally first
        if randint(0, 2) == 1:
            self.placeHorizontalHallway(prevRoomCenter.x, newRoomCenter.x, prevRoomCenter.y)
            self.placeVerticalHallway(prevRoomCenter.y, newRoomCenter.y, newRoomCenter.x)
        else:
            self.placeVerticalHallway(prevRoomCenter.y, newRoomCenter.y, newRoomCenter.x)
            self.placeHorizontalHallway(prevRoomCenter.x, newRoomCenter.x, prevRoomCenter.y)

    def placeHorizontalHallway(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for room in self.rooms:
                # Check to see if the coordinate is on the edge of any room, and is not occupied by any normal movable.
                if (room.isOnEdge(GameCoord(x, y)) and 
                    self.moveableMap[x][y] == None ):
                    self.addMoveable(Tile(TileType.door, x, y, stats = Stats(0,0)))
            self.staticMap[x][y] = TileType.floor

    def placeVerticalHallway(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for room in self.rooms:
                # Check to see if the coordinate is on the edge of any room, and is not occupied by any normal movable.
                if (room.isOnEdge(GameCoord(x, y)) and
                    self.moveableMap[x][y] == None ):
                    self.addMoveable(Tile(TileType.door, x, y, stats = Stats(0,0)))
            self.staticMap[x][y] = TileType.floor
    
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
                dist2 = (x - lit_obj.gameBody.x - lit_obj.body.direction.x)**2 + (y -lit_obj.gameBody.y - lit_obj.body.direction.y) ** 2 
                if( dist2 < (lit_obj.stats.lightlevel + 0.5)**2 ):
                    self.fogofwar[x][y].setTile(TileType.fow0)
                elif( dist2 < (lit_obj.stats.lightlevel + 1.5)**2 ):
                    self.fogofwar[x][y].setTile(TileType.fow1)
                elif( dist2 < (lit_obj.stats.lightlevel + 2.5)**2 ):
                    self.fogofwar[x][y].setTile(TileType.fow2)
                else:
                    if(self.fogofwar[x][y].tileType == TileType.fow3):
                        self.fogofwar[x][y].setTile(TileType.fow3)

        if self.nickCage.body.direction.x == 0 and self.nickCage.body.direction.y == 0:
            return # Nothing more to do for this frame

                    
        
        # Damage loop/Logic loop. 
        #  Do AI pathing.
        #  Do combat
        #    x2If damage is dealt, indicate that the tile cannot move
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None:
                    # Calculate the direction of FBI (AI)
                    if tile.tileType == TileType.fbi:
                        path = self.getPath(GameCoord(tile.gameBody.x, tile.gameBody.y), GameCoord(self.nickCage.gameBody.x, self.nickCage.gameBody.y))
                        if path != None and len(path) > 1:
                            tile.body.direction.x = path[1].x - tile.gameBody.x
                            tile.body.direction.y = path[1].y - tile.gameBody.y
                        else:
                            tile.body.direction.x = 0
                            tile.body.direction.y = 0

                    # Calculate the new tile position
                    newTileX = tile.gameBody.x + int(tile.body.direction.x)
                    newTileY = tile.gameBody.y + int(tile.body.direction.y)
                    tileInNewPosition = self.moveableMap[newTileX][newTileY]
                    if tileInNewPosition != None and tileInNewPosition != tile:
                        if tileInNewPosition.stats != None and tile.stats != None:
                            # Do damage to each other
                            tileInNewPosition.stats.health -= tile.stats.weapon
                            tile.stats.health -= tileInNewPosition.stats.weapon
                            self.event.signal(EventID.combat, [tile, tileInNewPosition.stats.weapon])
                            self.event.signal(EventID.combat, [tileInNewPosition, tile.stats.weapon])
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
                            if tileInNewPosition != None and tileInNewPosition.upgrade != None:
                                self.event.signal(EventID.upgrade, [tile, tileInNewPosition])
                                tile.stats.health += tileInNewPosition.upgrade.health
                                tile.stats.weapon += tileInNewPosition.upgrade.weapon
                                tile.stats.lightlevel += tileInNewPosition.upgrade.lightlevel
                                self.level += tileInNewPosition.upgrade.level
                                tileInNewPosition.destroyed = tileInNewPosition.Component(Destroyed) # Destroy the upgrade (single-use)
                                self.moveableMap[newTileX][newTileY] = None
                                tile.gameBody.canMove = True
                    elif tileInNewPosition == None and self.staticMap[newTileX][newTileY].tileType != TileType.wall:
                        if self.staticMap[newTileX][newTileY].tileType == TileType.lava:
                            dmg = self.staticMap[newTileX][newTileY].stats.weapon
                            tile.stats.health -= dmg
                            self.event.signal(EventID.combat, [tile, dmg])
                            if tile.stats.health <= 0:
                                tile.destroyed = tile.Component(Destroyed)
                                self.moveableMap[x][y] = None
                        tile.gameBody.canMove = True
                    else:
                        tile.gameBody.canMove = False
                    
                    if tile.gameBody.canMove:
                        tile.gameBody.x = newTileX
                        tile.gameBody.y = newTileY
                    

        # Movement loop. If the tile can move, do it.
        for x in range(0, len(self.moveableMap)):
            for y in range(0, len(self.moveableMap[x])):
                tile = self.moveableMap[x][y]
                if tile != None:
                    if tile.gameBody.canMove == True and self.moveableMap[tile.gameBody.x][tile.gameBody.y] == None:
                        # Sync the map to wherever the entity thinks it is
                        self.moveableMap[tile.gameBody.x][tile.gameBody.y] = tile
                        self.moveableMap[x][y] = None
                    else:
                        # Revert any movement that may have tried to occur
                        tile.gameBody.x = x
                        tile.gameBody.y = y

        self.sync_bodies(-1*self.nickCage.gameBody.x + Game.SCREEN_TILE_CENTER_X, -1*self.nickCage.gameBody.y + Game.SCREEN_TILE_CENTER_Y)

    def sync_bodies(self, shiftX = 0, shiftY = 0):
        for row in self.moveableMap:
            for tile in row:
                if tile is None:
                    continue                        
                # Sync the physical body based on the tile position
                tile.body.position.x = (tile.gameBody.x + shiftX) * TILESIZE_X
                tile.body.position.y = (tile.gameBody.y + shiftY) * TILESIZE_Y

        for row in self.staticMap:
            for tile in row:        
                if tile is None:
                    continue                            
                # Sync the physical body based on the tile position
                tile.body.position.x = (tile.gameBody.x + shiftX) * TILESIZE_X
                tile.body.position.y = (tile.gameBody.y + shiftY) * TILESIZE_Y

        for row in self.fogofwar:
            for tile in row:            
                if tile is None:
                    continue                        
                # Sync the physical body based on the tile position
                tile.body.position.x = (tile.gameBody.x + shiftX) * TILESIZE_X
                tile.body.position.y = (tile.gameBody.y + shiftY) * TILESIZE_Y
    
    def GenerateLevelLayout(self, targetMap, tileMap):
        for x in range(0, len(tileMap)):
            for y in range(0, len(tileMap[x])):
                if tileMap[x][y] == TileType.lava:
                     targetMap[x][y] = Tile(tileMap[x][y], x, y, stats = Stats(0, 2))
                else:
                    targetMap[x][y] = Tile(tileMap[x][y], x, y)