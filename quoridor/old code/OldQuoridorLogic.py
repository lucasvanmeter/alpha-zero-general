import sys
sys.path.append('..')
import copy
import numpy as np

class Square:
    def __init__(self, position, status, neighbors):
        self.position = position
        self.status = status
        self.neighbors = neighbors
        
class Intersection:
    def __init__(self, position, status):
        self.position = position
        self.status = status
        
class Board:
    """
    The board will be modeled as a graph
    """
    def __init__(self, rows, cols, p1walls = 10, p2walls = 10):
        self.rows = rows
        self.cols = cols
        # generate a dictionary of squares in the board with key
        # position and value a square class object.
        squares = {}
        for x in range(cols):
            for y in range(rows):
                neighbors = []
                if x == 0:
                    neighbors += [(x+1,y)]
                elif x == cols-1:
                    neighbors += [(x-1,y)]
                else:
                    neighbors += [(x+1,y)]
                    neighbors += [(x-1,y)]
                if y == 0:
                    neighbors += [(x,y+1)]
                elif y == rows-1:
                    neighbors += [(x,y-1)]
                else:
                    neighbors += [(x,y+1)]
                    neighbors += [(x,y-1)]
                squares[(x,y)] = Square((x,y),0,neighbors)
        self.squares = squares
        
        self.squares[(cols // 2, 0)].status = 1
        self.squares[(cols // 2), rows - 1].status = -1
        
        intersections = {}
        for x in range(cols-1):
            for y in range(rows-1):
                intersections[(x,y)] = Intersection((x,y),0)
        self.intersections = intersections
                
        self.p1walls = p1walls
        self.p2walls = p2walls
    
    def squareDistance(self, player):
        """
        Computes the distance for all squares on the board from the winning squares for a given player.
        
        Returns a dictionary containing all squares that can reach the goal and their distances. Squares
        that can not reach the goal will not be in the dictionary.
        
        Can probably be made more efficient...
        """
        distDict = {}
        if player == 1:
            goalRow = self.rows - 1
        else:
            goalRow = 0
        for square in self.squares:
            if square[1] == goalRow:
                distDict[square] = 0
        newNeighbors = True
        newsquares = {square for square in distDict}
        while newNeighbors:
            newNeighbors = False
            tempsquares = {}
            for square in newsquares:
                for neighbor in self.squares[square].neighbors:
                    if neighbor not in distDict:
                        distDict[neighbor] = distDict[square] + 1
                        newNeighbors = True
                        tempsquares[neighbor] = distDict[neighbor]
            newsquares = tempsquares
        return distDict
    
    # Need to add implimintation of walls
    def showBoard(self):
        switch = True
        row = 0
        # iterate through rows
        while row < self.rows:
            square = True
            out = ''
            col = 0
            # iterate through a row with squares and vert walls
            if switch:
                out += ' '
                while col < self.cols:
                    if square:
                        if self.squares[(col,row)].status == 0:
                            out += '   '
                        if self.squares[(col,row)].status == 1:
                            out += ' 1 '
                        elif self.squares[(col,row)].status == -1:
                            out += ' -1 '
                        col += 1  
                    else:
                        if row != self.rows - 1 and self.intersections[(col - 1,row)].status == 'V':
                            out += ' I '
                        elif row != 0 and self.intersections[(col - 1,row - 1)].status == 'V':
                            out += ' I '
                        else:
                            out += ' : '  
                    square  = not square
                row += 1
            # iterate through a row of horz walls
            else:
                while col < self.cols:
                    if col !=  self.cols-1 and self.intersections[(col,row - 1)].status == 'H':
                        out += '====='
                    elif col != 0 and self.intersections[(col - 1,row - 1)].status == 'H':
                        out += '====='
                    else:
                        out += '.....'
                    if col != self.cols -1 :
                        out += '+'
                    col += 1
            # print row and next row is a different type of row
            print(out)
            switch = not switch
            
class State:
    def __init__(self, p1, p2, rows, cols):
        self.board = Board(rows, cols)
        self.p1 = p1
        self.p2 = p2
        self.p1Pos = (cols // 2, 0)
        self.p2Pos = (cols // 2, rows - 1)
        allPossibleWalls = set()
        for intersection in self.board.intersections:
                allPossibleWalls.add((intersection, 'H'))
                allPossibleWalls.add((intersection, 'V'))
        self.possibleWalls = allPossibleWalls
        self.isEnd = False
        self.boardHash = None
        self.currentPlayer = 1
        
    def getBoardVec(self):
        """
        The board will be passed to the NNet as a single vector. It will be length 2+81+81. The first two spots indiacte 
        how many walls player 1 and 2 have remaining. The next 81 indicate if there is no pawn (0) p1 pawn (1) or 
        p2 pawn (-1) in a given square. The next 81 indicate if the intersection in the bottom right of a square has a wall
        , empty is (0) horizontal is (1) and vertical is (2). Note that the entire right and bottom of board will always have
        0 since walls can't be placed in their bottom right corners.

        To translate from a index from 0 to 80 to a square use (x,y) = n // 8, n % 9.
        To translate from an index of 81 to 144 to an intersection use (x,y) = n-80 // 7, n-80 % 8
        """
        sq = [1 if self.board.squares[x].status == 1 else
              2 if self.board.squares[x].status == -1 else
              0 for x in self.board.squares]
        wa = [1 if self.board.intersections[x].status == 'H' else
              2 if self.board.intersections[x].status == 'V' else
              0 for x in self.board.intersections]
        i = self.board.cols-1
        while i < len(wa):
            wa.insert(i, 0)
            i += self.board.cols
        wa = wa + (self.board.cols+1)*[0]
        rw = [self.board.p1walls, self.board.p2walls]
        return rw + sq + wa
    
    def getCanonicalVec(self, player):
        """
        same as getBoardVec() but we need to reverse the board and negate the player pawns if
        it's player 2's turn.
        """
        vec = self.getBoardVec()
        if player == 1:
            return vec
        else:
            res = [self.board.p1walls, self.board.p2walls]
            squares = vec[2:2 + 81]
            walls = vec[2 + 81:]
            for i in range(self.board.rows):
                squares[i*9:i*9 + 9] = squares[i*9:i*9 + 9][::-1]
                squares = [2 if x == 1 else
                           1 if x == -1 else
                           0 for x in squares]
            for i in range(self.board.rows - 1):
                walls[i*8:i*8 + 8] = walls[i*8:i*8 + 8][::-1]
            return res + squares + walls
            
        
    def validPawnMoves(self):
        """
        Finds all current legal pawn moves. 
        
        NEEDS TO BE UPDATED TO ACCOMODATE JUMPING PAWNS.
        """
        if self.currentPlayer == 1:
            return self.board.squares[self.p1Pos].neighbors
        else:
            return self.board.squares[self.p2Pos].neighbors
            
    def movePawn(self, old, new, player):
        """
        old and new are positions written as (x,y) tuples. Player is either 1 or -1.
        """
        #update board player position
        self.board.squares[old].status = 0
        self.board.squares[new].status = player
        
        # update state info of where player is
        if player == 1:
            self.p1Pos = new
        else:
            self.p2Pos = new
    
    def testWallPlacement(self, position, orientation):
        # check to see if this cuts of a player from reaching the other side
        # this requires moddifying neighbors and if it's not a valid wall then undoing this modification
        tempBoard = copy.deepcopy(self.board)
        if orientation == 'H':
            # update neighbors for squares
            tempBoard.squares[(position[0],position[1])].neighbors.remove((position[0],position[1] + 1))
            tempBoard.squares[(position[0],position[1] + 1)].neighbors.remove((position[0],position[1]))
            tempBoard.squares[(position[0] + 1,position[1])].neighbors.remove((position[0] + 1,position[1] + 1))
            tempBoard.squares[(position[0] + 1,position[1] + 1)].neighbors.remove((position[0] + 1,position[1]))
            
            #check to see if move cuts of a player
            distGraph1 = tempBoard.squareDistance(1)
            distGraph2 = tempBoard.squareDistance(2)
            if self.p1Pos not in distGraph1 or self.p2Pos not in distGraph2:
                return False
            else:
                return True
            
        if orientation == 'V':
            tempBoard.squares[(position[0],position[1])].neighbors.remove((position[0] + 1,position[1]))
            tempBoard.squares[(position[0] + 1,position[1])].neighbors.remove((position[0],position[1]))
            tempBoard.squares[(position[0],position[1] + 1)].neighbors.remove((position[0] + 1,position[1] + 1))
            tempBoard.squares[(position[0] + 1,position[1] + 1)].neighbors.remove((position[0],position[1] + 1))
            
            distGraph1 = tempBoard.squareDistance(1)
            distGraph2 = tempBoard.squareDistance(2)
            if self.p1Pos not in distGraph1 or self.p2Pos not in distGraph2:
                return False
            else:
                return True
            
    def validWalls(self):
        if self.currentPlayer == 1 and self.board.p1walls == 0:
            return []
        if self.currentPlayer == 2 and self.board.p2walls == 0:
            return []
        res = []
        for placement in self.possibleWalls:
            if self.testWallPlacement(placement[0],placement[1]):
                res.append(placement)
        return res
    
    def placeWall(self, position, orientation): 
        """
        Position is a tuple written as (x,y). Orientations are either 'H' for horizontal or 
        'V' for vertical. Returns false if not a valid wall placement. Otherwise updates the board and
        states copy of legalWalls and returns True.
        """
        if orientation == 'H':
            # update neighbors for squares
            self.board.squares[(position[0],position[1])].neighbors.remove((position[0],position[1] + 1))
            self.board.squares[(position[0],position[1] + 1)].neighbors.remove((position[0],position[1]))
            self.board.squares[(position[0] + 1,position[1])].neighbors.remove((position[0] + 1,position[1] + 1))
            self.board.squares[(position[0] + 1,position[1] + 1)].neighbors.remove((position[0] + 1,position[1]))
            
            # update possible walls
            if ((position[0], position[1]),'V') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1]),'H'))
            if ((position[0], position[1]),'V') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1]),'V'))
            if ((position[0] - 1, position[1]),'H') in self.possibleWalls:
                self.possibleWalls.remove(((position[0] - 1, position[1]),'H'))
            if ((position[0] + 1, position[1]),'H') in self.possibleWalls:
                self.possibleWalls.remove(((position[0] + 1, position[1]),'H'))
            
        if orientation == 'V':
            self.board.squares[(position[0],position[1])].neighbors.remove((position[0] + 1,position[1]))
            self.board.squares[(position[0] + 1,position[1])].neighbors.remove((position[0],position[1]))
            self.board.squares[(position[0],position[1] + 1)].neighbors.remove((position[0] + 1,position[1] + 1))
            self.board.squares[(position[0] + 1,position[1] + 1)].neighbors.remove((position[0],position[1] + 1))
            
            if ((position[0], position[1]),'V') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1]),'V'))
            if ((position[0], position[1]),'H') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1]),'H'))
            if ((position[0], position[1] - 1),'V') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1] - 1),'V'))
            if ((position[0], position[1] + 1),'V') in self.possibleWalls:
                self.possibleWalls.remove(((position[0], position[1] + 1),'V'))
            
        # update intersections
        self.board.intersections[position].status = orientation
        
        # update remaining walls
        if self.currentPlayer == 1:
            self.board.p1walls -= 1
        else:
            self.board.p2walls -= 1
        
    def takeAction(self, action):
        """
        Actions are of the form ((x,y), z) where z is either 1 or 2 if it is a pawn move 
        and "H" or "V" if it is a wall placement. Returns False if the action is not legal
        and otherwise performes the action and returns True.
        """
        if action[1] == 1:
            self.movePawn(self.p1Pos,action[0],action[1])
        elif action[1] == -1:
            self.movePawn(self.p2Pos,action[0],action[1])
        else:
            self.placeWall(action[0],action[1])
        self.currentPlayer = -1*self.currentPlayer
        
    def availActions(self, player):
        return [(x, player) for x in state.legalPawnMoves(player)] + list(state.legalWalls)
        
        
    def winner(self):
        if self.p1Pos[1] == self.board.rows-1:
            return 1
        elif self.p2Pos[1] == 0:
            return -1
        else:
            return 0