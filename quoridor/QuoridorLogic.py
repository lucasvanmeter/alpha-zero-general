import copy
import numpy as np

class Board():
    """
    The board can be generate from the current board positions stored as a vector.
    This vector has length 2 + 2 + 64, corresponding to 
    (a) the players remaining walls, [p1,p2]
    (b) the position of p1 pawn and p2 pawn [(a,b),(x,y)]
    (c) the wall spots with 0 if no wall, 1 if horizontal wall, and 2 if vertical wall.
    An initial board vector is given by [10,10]+[(4,0),(4,8)]+64*[0]
    
    We use this generation technique to play nicely with existing code in which the board is passed
    around as just this vector. We can also pass the NNet this vector as input.
    
    It is also easy to get a canonical board position by inverting the board and switching the positions
    of p1 and p2 pawns.
    
    It is always assumed that player 1 is currently going.
    """
    def __init__(self, vec = [10,10]+[(4,0),(4,8)]+64*[0]):
        self.vec = vec
        self.p1walls = vec[0]
        self.p2walls = vec[1]
        self.p1pos = vec[2]
        self.p2pos = vec[3]
        
        # Walls are stored in an 8x8 grid which can be accesed by [x,y] coordinates.
        walls = vec[4:]
        self.walls = np.array([walls[8*i:8+8*i] for i in range(8)])
        
        # The board is stored as graph. The data structure is a dictionary with the keys as
        # positions and the values and adjacent connected positions.
        graph = {}
        for x in range(9):
            for y in range(9):
                graph[(x,y)] = []
                if x > 0:
                    graph[(x,y)].append((x-1,y))
                if x < 8:
                    graph[(x,y)].append((x+1,y))
                if y > 0:
                    graph[(x,y)].append((x,y-1))
                if y < 8:
                    graph[(x,y)].append((x,y+1))
        self.boardGraph = graph
        
    def getBoardVec(self):
        """
        Returns: A vector of length 2+2+64 encoding the remaining walls, squares, and walls.
        """
        return [self.p1walls, self.p2walls, self.p1pos, self.p2pos] + list(self.walls.flatten())
    
    def getInverseBoardVec(self):
        remWalls = [self.p2walls, self.p1walls]
        pos = [(self.p2pos[0],8-self.p2pos[1]),(self.p1pos[0],8-self.p1pos[1])]
        walls = [x for col in self.walls for x in col[::-1]]
        return remWalls + pos + walls

    
    def validPawnMoves(self, player):
        """
        Input:
            player: 1 or -1
        
        Description:    
            Normall you can move to any adjacent square not blocked by a wall. If your 
            opponents pawn occupies an adjacent square you can jump over them. If there is
            a wall behind them then you can jump and turn over them.

        Returns:
            A list of all valid squares the player may move to.
        """
        if player == 1:
            x,y = self.p1pos
            other = self.p2pos
        else:
            x,y = self.p2pos
            other = self.p1pos
        
        moves = []
        # Check left and right
        for i in [1,-1]:
            if (x+i,y) in self.boardGraph[(x,y)]:
                # if space open add to moves
                if other != (x+i,y):
                    moves.append((x+i,y))
                else: 
                    # otherwise see if jumping over is allowed
                    if (x+2*i,y) in self.boardGraph[(x+i,y)]:
                        moves.append((x+2*i,y))
                    else:
                        # last, add the diagonal jumps if available.
                        if (x+i,y+i) in self.boardGraph[(x+i,y)]:
                            moves.append((x+i,y+i))
                        if (x+i,y-i) in self.boardGraph[(x+i,y)]:
                            moves.append((x+i,y-i))
        
        for i in [1,-1]:
            if (x,y+i) in self.boardGraph[(x,y)]:
                if other != (x,y+i):
                    moves.append((x,y+i))
                else: 
                    if (x,y+2*i) in self.boardGraph[(x,y+i)]:
                        moves.append((x,y+2*i))
                    else:
                        if (x+i,y+i) in self.boardGraph[(x,y+i)]:
                            moves.append((x+i,y+i))
                        if (x-i,y+i) in self.boardGraph[(x,y+i)]:
                            moves.append((x-i,y+i))
                            
        return moves
    
    def movePawn(self, x,y, player):
        """
        x,y: coordinates to move the pawn to.
        player: 1 or -1
        
        Updates self.p1pos or self.p2pos
        """
        if player == 1:
            self.p1pos = (x,y)
        else:
            self.p2pos = (x,y)
        
    def validWalls(self, player):
        """
        player: 1 or -1
        
        Returns a length 64+64 list of 1's and 0's. In particular a wall cannot 
        be placed if it would hit another wall, or if it would cut of a player from their goal. 
        This second case (which requires a DFS of the board graph) is handeled by testWallPlacement()
        """
        if player == 1 and self.p1walls == 0:
            return 128*[0]
        if player == -1 and self.p2walls == 0:
            return 128*[0]
        
        horz = 64*[0]
        for x in range(8):
            for y in range(8):
                n = 8*x+y
                if x == 0:
                    if self.walls[x,y] == 0 and self.walls[x+1,y] != 1:
                        if self.testWallPlacement(x,y,1):
                            horz[n]=1
                elif x == 7:
                    if self.walls[x,y] == 0 and self.walls[x-1,y] != 1:
                        if self.testWallPlacement(x,y,1):
                            horz[n]=1
                else:
                    if self.walls[x,y] == 0 and self.walls[x+1,y] != 1 and self.walls[x-1,y] != 1:
                        if self.testWallPlacement(x,y,1):
                            horz[n]=1
                            
        vert = 64*[0]
        for x in range(8):
            for y in range(8):
                n = 8*x+y
                if y == 0:
                    if self.walls[x,y] == 0 and self.walls[x,y+1] != 2:
                        if self.testWallPlacement(x,y,2):
                            vert[n]=1
                elif y == 7:
                    if self.walls[x,y] == 0 and self.walls[x,y-1] != 2:
                        if self.testWallPlacement(x,y,2):
                            vert[n]=1
                else:
                    if self.walls[x,y] == 0 and self.walls[x,y+1] != 2 and self.walls[x,y-1] != 2:
                        if self.testWallPlacement(x,y,2):
                            vert[n]=1
                            
        return horz+vert
    
    def testWallPlacement(self,x,y,orientation):
        """
        position: (x,y)
        orientation: 1 for horizontal, 2 for vertical
        
        Returns True if placing such a wall does not disconnect either player from their goal, else False.
        
        This is done by a DFS of the boardGraph after the wall has been placed.
        """
        #update the boardGraph after the wall placement
        graph = copy.deepcopy(self.boardGraph)
        
        if orientation == 1:
            graph[(x,y)].remove((x,y+1))
            graph[(x,y+1)].remove((x,y))
            graph[(x+1,y)].remove((x+1,y+1))
            graph[(x+1,y+1)].remove((x+1,y))
            
        else:
            graph[(x,y)].remove((x+1,y))
            graph[(x+1,y)].remove((x,y))
            graph[(x,y+1)].remove((x+1,y+1))
            graph[(x+1,y+1)].remove((x,y+1))
        
        # check if p1 is disconnected from goal
        p1connected = False
        visited = set()
        queue = [self.p1pos]
        while queue and not p1connected:
            vert = queue.pop(0)
            if vert[1] == 8:
                p1connected = True
            for i in graph[vert]:
                if i not in visited:
                    queue.append(i)
                    visited.add(i)
        
        # check if p2 is disconnected from goal
        p2connected = False
        visited = set()
        queue = [self.p2pos]
        while queue and not p2connected:
            vert = queue.pop(0)
            if vert[1] == 0:
                p2connected = True
            for i in graph[vert]:
                if i not in visited:
                    queue.append(i)
                    visited.add(i)
                    
        return p1connected and p2connected
        
    
    def placeWall(self,x,y,orientation):
        """
        x,y: location in 8x8 grid to place a wall. Note that this also corresponds to the lower right
        corner of a square on the game board.
        orientation: 1 for horz and 2 for vert
        
        updates self.walls and self.boardGraph
        """
        self.walls[x,y] = orientation
        
        if orientation == 1:
            self.boardGraph[(x,y)].remove((x,y+1))
            self.boardGraph[(x,y+1)].remove((x,y))
            self.boardGraph[(x+1,y)].remove((x+1,y+1))
            self.boardGraph[(x+1,y+1)].remove((x+1,y))
            
        else:
            self.boardGraph[(x,y)].remove((x+1,y))
            self.boardGraph[(x+1,y)].remove((x,y))
            self.boardGraph[(x,y+1)].remove((x+1,y+1))
            self.boardGraph[(x+1,y+1)].remove((x,y+1))
    
    def validActions(self, player):
        """
        returns a list of length 81+64+64 corresponding to pawn moves and wall placements (horz,vert).
        """
        moves = 81*[0]
        for x,y in self.validPawnMoves(player):
            moves[9*x+y] = 1
        return moves + self.validWalls(player)
    
    def takeAction(self, player, action):
        """
        Input:
            player: 1 or -1
            action: an int from 0 to 81+64+64 correpsonding to moving a pawn, placing a horz wall
            or placing a vert wall.

        Calls movePawn() which updates self.p1pos or placeWall() which updates self.walls and self.p1walls.
        """
        n = action
        if n <= 80:
            x,y = n // 9, n % 9
            self.movePawn(x,y,player)
        elif n <= 144:
            x,y = (n-81) // 8, (n-81) % 8
            self.placeWall(x,y,1)
            if player == 1:
                self.p1walls -= 1
            else:
                self.p2walls -= 1
        else:
            x,y = (n-145) // 8, (n-145) % 8
            self.placeWall(x,y,2)
            if player == 1:
                self.p1walls -= 1
            else:
                self.p2walls -= 1
    
    def getWinner(self):
        """
        returns 1 if player 1 has won, -1 if player 2 has won, and 0 if neither has won.
        """
        if self.p1pos[1] == 8:
            return 1
        elif self.p2pos[1] == 0:
            return -1
        else:
            return 0
        
    def displayBoard(self):
        switch = True
        row = 0
        # iterate through rows
        while row < 9:
            square = True
            out = ''
            col = 0
            # iterate through a row with squares and vert walls
            if switch:
                out += ' '
                while col < 9:
                    if square:
                        if self.p1pos == (col,row):
                            out += ' 1 '
                        elif self.p2pos == (col,row):
                            out += ' 2 '
                        else:
                            out += '   '
                        col += 1  
                    else:
                        if row != 8 and self.walls[col - 1,row] == 2:
                            out += ' I '
                        elif row != 0 and self.walls[col - 1,row - 1] == 2:
                            out += ' I '
                        else:
                            out += ' : '  
                    square = not square
                row += 1
            # iterate through a row of horz walls
            else:
                while col < 9:
                    if col !=  8 and self.walls[col,row - 1] == 1:
                        out += '====='
                    elif col != 0 and self.walls[col - 1,row - 1] == 1:
                        out += '====='
                    else:
                        out += '.....'
                    if col != 8:
                        out += '+'
                    col += 1
            # print row and next row is a different type of row
            print(out)
            switch = not switch