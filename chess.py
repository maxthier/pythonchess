from typing import List, Tuple, NoReturn
import os

class Game:
    __board = None
    __current_player = None
    def __init__(self):
        # Initialize the chess game
        self.__board = self.create_board()
        self.__current_player = "white"

    def get_piece_at(self, x: int, y: int) -> 'Piece | None':
        """Return the piece at the specified x and y coordinates"""
        return self.__board[y][x]
    
    # Render the board in the terminal
    def render_board(self, valid_moves: List[Tuple[int,int]] = []):
        """Render the board in the terminal with a checkboard pattern"""
        os.system('clear')  # Clear the terminal output
        print("  A B C D E F G H")
        for y in range(8):
            print(f"{8-y} ", end="")
            for x in range(8):
                piece = self.get_piece_at(x, (7-y))
                if (x, y) in valid_moves:
                    print("\033[48;2;0;255;0m", end="")
                    pass
                elif (x + y) % 2 == 0:
                    print("\033[48;2;215;135;0m", end="")
                    pass
                else:
                    print("\033[48;2;255;174;94m", end="")
                    pass
                if piece is not None:
                    print(f"{piece.unicode} ", end="")
                else:
                    print("  ", end="")
                print("\033[m", end="")
            print(f" {8-y}")
        print("  A B C D E F G H")

    def create_board(self):
        """Create and return the initial chess board"""
        self.__board = [[Rook(self, "white", 0, 0), Knight(self, "white", 1, 0), Bishop(self, "white", 2, 0), Queen(self, "white", 3, 0), King(self, "white", 4, 0), Bishop(self, "white", 5, 0), Knight(self, "white", 6, 0), Rook(self, "white", 7, 0)],
             [Pawn(self, "white", 0, 1), Pawn(self, "white", 1, 1), Pawn(self, "white", 2, 1), Pawn(self, "white", 3, 1), Pawn(self, "white", 4, 1), Pawn(self, "white", 5, 1), Pawn(self, "white", 6, 1), Pawn(self, "white", 7, 1)],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [Pawn(self, "black", 0, 6), Pawn(self, "black", 1, 6), Pawn(self, "black", 2, 6), Pawn(self, "black", 3, 6), Pawn(self, "black", 4, 6), Pawn(self, "black", 5, 6), Pawn(self, "black", 6, 6), Pawn(self, "black", 7, 6)],
             [Rook(self, "black", 0, 7), Knight(self, "black", 1, 7), Bishop(self, "black", 2, 7), Queen(self, "black", 3, 7), King(self, "black", 4, 7), Bishop(self, "black", 5, 7), Knight(self, "black", 6, 7), Rook(self, "black", 7, 7)]]

class Piece:
    __game = None
    _team = ""
    x = y = 0
    unicode = ''
    def __init__(self, game: Game, team: str, x: int, y: int, unicode: str) -> NoReturn:
        self.__game = game
        self._team = team
        self.x = x
        self.y = y
        color = "\033[97m" if team == "white" else "\033[30m"
        self.unicode = f"{color}{unicode}"
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        """Return a List of Tuples with valid Moves"""
        pass

class Pawn(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265F")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        if self._team == "white":
            # Move one forward
            if self.y + 1 < 8 and self.__game.get_piece_at(self.x, self.y + 1) is None:
                valid_moves.append((self.x, self.y + 1))
            # Move two forward on start field
            if self.y == 1 and self.__game.get_piece_at(self.x, self.y + 1) is None and self.__game.get_piece_at(self.x, self.y + 2) is None:
                valid_moves.append((self.x, self.y + 2))
            # Take sideways
            if self.x - 1 >= 0 and self.y + 1 < 8 and self.__game.get_piece_at(self.x - 1, self.y + 1) is not None:
                valid_moves.append((self.x - 1, self.y + 1))
            if self.x + 1 < 8 and self.y + 1 < 8 and self.__game.get_piece_at(self.x + 1, self.y + 1) is not None:
                valid_moves.append((self.x + 1, self.y + 1))
        else:
            # Move one forward
            if self.y - 1 >= 0 and self.__game.get_piece_at(self.x, self.y - 1) is None:
                valid_moves.append((self.x, self.y - 1))
            # Move two forward on start field
            if self.y == 6 and self.__game.get_piece_at(self.x, self.y - 1) is None and self.__game.get_piece_at(self.x, self.y - 2) is None:
                valid_moves.append((self.x, self.y - 2))
            # Take sideways
            if self.x - 1 >= 0 and self.y - 1 >= 0 and self.__game.get_piece_at(self.x - 1, self.y - 1) is not None:
                valid_moves.append((self.x - 1, self.y - 1))
            if self.x + 1 < 8 and self.y - 1 >= 0 and self.__game.get_piece_at(self.x + 1, self.y - 1) is not None:
                valid_moves.append((self.x + 1, self.y - 1))
        return valid_moves

class Rook(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265C")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        # Horizontal moves
        for i in range(self.x + 1, 8):
            valid_moves.append((i, self.y))
            if self.__game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.x - 1, -1, -1):
            valid_moves.append((i, self.y))
            if self.__game.get_piece_at(i, self.y) is not None:
                break
        # Vertical moves
        for i in range(self.y + 1, 8):
            valid_moves.append((self.x, i))
            if self.__game.get_piece_at(self.x, i) is not None:
                break
        for i in range(self.y - 1, -1, -1):
            valid_moves.append((self.x, i))
            if self.__game.get_piece_at(self.x, i) is not None:
                break
        return valid_moves

class Knight(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265E")

    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        moves = [(self.x + 2, self.y + 1), (self.x + 2, self.y - 1),
                    (self.x - 2, self.y + 1), (self.x - 2, self.y - 1),
                    (self.x + 1, self.y + 2), (self.x + 1, self.y - 2),
                    (self.x - 1, self.y + 2), (self.x - 1, self.y - 2)]
        for move in moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                valid_moves.append(move)
        return valid_moves

class Bishop(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265D")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        # Diagonal moves
        for i in range(1, 8):
            if self.x + i < 8 and self.y + i < 8:
                valid_moves.append((self.x + i, self.y + i))
                if self.__game.get_piece_at(self.x + i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x + i < 8 and self.y - i >= 0:
                valid_moves.append((self.x + i, self.y - i))
                if self.__game.get_piece_at(self.x + i, self.y - i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y + i < 8:
                valid_moves.append((self.x - i, self.y + i))
                if self.__game.get_piece_at(self.x - i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y - i >= 0:
                valid_moves.append((self.x - i, self.y - i))
                if self.__game.get_piece_at(self.x - i, self.y - i) is not None:
                    break
            else:
                break
        return valid_moves

class Queen(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265B")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        # Horizontal and vertical moves
        for i in range(self.x + 1, 8):
            valid_moves.append((i, self.y))
            if self.__game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.x - 1, -1, -1):
            valid_moves.append((i, self.y))
            if self.__game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.y + 1, 8):
            valid_moves.append((self.x, i))
            if self.__game.get_piece_at(self.x, i) is not None:
                break
        for i in range(self.y - 1, -1, -1):
            valid_moves.append((self.x, i))
            if self.__game.get_piece_at(self.x, i) is not None:
                break
        # Diagonal moves
        for i in range(1, 8):
            if self.x + i < 8 and self.y + i < 8:
                valid_moves.append((self.x + i, self.y + i))
                if self.__game.get_piece_at(self.x + i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x + i < 8 and self.y - i >= 0:
                valid_moves.append((self.x + i, self.y - i))
                if self.__game.get_piece_at(self.x + i, self.y - i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y + i < 8:
                valid_moves.append((self.x - i, self.y + i))
                if self.__game.get_piece_at(self.x - i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y - i >= 0:
                valid_moves.append((self.x - i, self.y - i))
                if self.__game.get_piece_at(self.x - i, self.y - i) is not None:
                    break
            else:
                break
        return valid_moves

class King(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265A")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        moves = [(self.x + 1, self.y), (self.x - 1, self.y),
                    (self.x, self.y + 1), (self.x, self.y - 1),
                    (self.x + 1, self.y + 1), (self.x + 1, self.y - 1),
                    (self.x - 1, self.y + 1), (self.x - 1, self.y - 1)]
        for move in moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                valid_moves.append(move)
        return valid_moves

game = Game()
game.create_board()
game.render_board(valid_moves=[(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)])