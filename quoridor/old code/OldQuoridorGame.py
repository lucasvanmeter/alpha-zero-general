import sys
sys.path.append('..')
from Game import Game
from .QuoridorLogic import State

class QuoridorGame(Game):
    """
    Use 1 for player1 and -1 for player2.

    Actions are encoded into a vector that has length 81 + 64 + 64. The first 81 correspond to moving the current players
    pawn to that square on the 9x9 grid. The latter pair of 64 correspond to placing a wall in one of the 8x8 intersections
    in either the horizontal (1) or vertical (2) positions.
    
    To translate from a index from 0 to 80 to a square use (x,y) = n // 8, n % 9.
    To translate from an index of 81 to 144 to an intersection use (x,y) = n-80 // 7, n-80 % 8
    
    
    The board will be passed to the NNet as a single vector. It will be length 2+81+81. The first two spots indiacte 
    how many walls player 1 and 2 have remaining. The next 81 indicate if there is no pawn (0) p1 pawn (1) or 
    p2 pawn (-1) in a given square. The next 81 indicate if the intersection in the bottom right of a square has a wall
    , empty is (0) horizontal is (1) and vertical is (2). Note that the entire right and bottom of board will always have
    0 since walls can't be placed in their bottom right corners.
    """
    
    def __init__(self):
        pass

    def getInitBoard(self):
        """
        Returns:
            an initial instance of the state object.
        """
        state = State('p1','p2',9,9)
        return state

    def getBoardSize(self):
        """
        Returns:
            n: the size of the input to the NN. The board is size 9x9 so it will be 2 + 81 + 81 for 
            the remaining wall counts, pawn tokens and wall tokens.
        """
        return 2 + 81 + 81

    def getActionSize(self):
        """
        Returns:
            actionSize: Actions are encoded into a vector that has length 81 + 64 + 64. 
            The first 81 correspond to moving the current players pawn to that square on 
            the 9x9 grid. The latter 64 correspond to placing a wall in one of the 8x8 intersections
            horizontal (1) and the last 64 for vertical (2) positions.
        """
        return 81 + 64 + 64

    def getNextState(self, board, player, action):
        """
        Input:
            board: current state
            player: current player (1 or -1)
            action: an integer corresponding to the action taken by current player in the action vector.

        Returns:
            nextBoard: board after applying action
            nextPlayer: player who plays in the next turn (should be -player)
            
        Actions are encoded into a vector that has length 81 + 64 + 64. The first 81 correspond to moving the current players
        pawn to that square on the 9x9 grid. The latter 64 correspond to placing a wall in one of the 8x8 intersections
        horizontal (1) and the last 64 for vertical (2) positions.

        To translate from a index from 0 to 80 to a square use (x,y) = n // 8, n % 9.
        To translate from an index of 81 to 144 to an intersection use (x,y) = n-80 // 7, n-80 % 8
        """
        state = board
        n = action
        if n <= 80:
            (x,y) = n // 8, n % 9
            token = player
        elif n <= 144:
            (x,y) = (n-80) // 7, (n-80) % 8
            token = 'H'
        else:
            (x,y) = (n-144) // 7, (n-144) % 8
            token = 'V'
        state.takeAction(((x,y),token))
        return (state, -1*player) 

    def getValidMoves(self, board, player):
        """
        Input:
            cononical board: current board
            player: current player

        Returns:
            validMoves: a binary vector of length self.getActionSize(), 1 for
                        moves that are valid from the current board and player,
                        0 for invalid moves
        """
        state = board
        validpawn = [0]*81
        validhwall = [0]*64
        validvwall = [0]*64
        walls = state.validWalls()
        for (x,y) in state.validPawnMoves():
            validpawn[x*9+y] = 1
        for move in state.validWalls():
            (x,y) = move[0]
            if move[1] == 'H':
                validhwall[x*8+y] = 1
            else:
                validvwall[x*8+y] = 1
                
        if state.currentPlayer == 2:
            for i in range(9):
                validpawn[i*9:i*9 + 9] = validpawn[i*9:i*9 + 9][::-1]
            for i in range(8):
                validhwall[i*8:i*8 + 8] = walls[i*8:i*8 + 8][::-1]
            for i in range(8):
                validvwall[i*8:i*8 + 8] = walls[i*8:i*8 + 8][::-1]
            
        return validpawn + validhwall + validvwall

    def getGameEnded(self, board, player):
        """
        Input:
            board: 
            player: current player (1 or -1)

        Returns:
            r: 0 if game has not ended. 1 if player won, -1 if player lost,
               small non-zero value for draw.
               
        """
        squares = board[2:2+81]
        row1 = [squares[9*i] for i in range(8)]
        row9 = [squares[9*i+8] for i in range(8)]
        if 1 in row9:
            return 1
        elif -1 in row1:
            return -1
        else:
            return 0
        return player*winner

    def getCanonicalForm(self, board, player):
        """
        Input:
            board: current board
            player: current player (1 or -1)

        Returns:
            Returns the form of board that can be read by NNet. 
            
            The board will be passed to the NNet as a single vector. It will be length 2+81+81. The first two spots indiacte 
            how many walls player 1 and 2 have remaining. The next 81 indicate if there is no pawn (0) p1 pawn (1) or 
            p2 pawn (-1) in a given square. The next 81 indicate if the intersection in the bottom right of a square has a wall
            , empty is (0) horizontal is (1) and vertical is (2). Note that the entire right and bottom of board will always have
            0 since walls can't be placed in their bottom right corners.
            
            To translate from a index from 0 to 80 to a square use (x,y) = n // 8, n % 9.

            The canonical form
            should be independent of player. For e.g. in chess,
            the canonical form can be chosen to be from the pov
            of white. When the player is white, we can return
            board as is. When the player is black, we can invert
            the colors and return the board.
        """
        state = board
        return state.getCanonicalVec(player)
                

    def getSymmetries(self, board, pi):
        """
        Input:
            CanonicalBoard: 
            pi: policy vector of size self.getActionSize()

        Returns:
            symmForms: a list of [(board,pi)] where each tuple is a symmetrical
                       form of the board and the corresponding pi vector. This
                       is used when training the neural network from examples.
        """
        return [(board,pi)]

    def stringRepresentation(self, board):
        """
        Input:
            cononical board: current board

        Returns:
            boardString: a quick conversion of board to a string format.
                         Required by MCTS for hashing.
        """
        return str(board)
