from typing import List, Tuple, NoReturn
import os
import sys
import tty
import termios
import re

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
                if (x, (7-y)) in valid_moves:
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
    
    def move_piece(self, x: int, y: int, target_x: int, target_y: int) -> NoReturn:
        """Move a piece to a new position"""
        piece = self.get_piece_at(x, y)
        self.__board[y][x] = None
        self.__board[target_y][target_x] = piece
        self.render_board()
        self.__current_player = "black" if self.__current_player == "white" else "white"

    def is_check(self, player: str) -> bool:
        """Check if the specified player is in check"""
        king_position = None
        opponent_pieces = []
        
        # Find the king's position and collect opponent's pieces
        for y in range(8):
            for x in range(8):
                piece = self.get_piece_at(x, y)
                if piece is not None:
                    if piece.team == player:
                        if isinstance(piece, King):
                            king_position = (x, y)
                    else:
                        opponent_pieces.append(piece)
        
        # Check if any opponent's piece can attack the king
        for piece in opponent_pieces:
            valid_moves = piece.get_valid_moves()
            if king_position in valid_moves:
                return True
        
        return False

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
    game: Game
    team: str
    x = y = 0
    unicode = ''
    def __init__(self, game: Game, team: str, x: int, y: int, unicode: str) -> NoReturn:
        self.game = game
        self.team = team
        self.x = x
        self.y = y
        color = "\033[97m" if team == "white" else "\033[30m"
        self.unicode = f"{color}{unicode}"
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        """Return a List of Tuples with valid Moves"""
        pass

    def get_game(self) -> Game:
        return self.game

class Pawn(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        super().__init__(game, team, x, y, "\u265F")
    
    def get_valid_moves(self) -> List[Tuple[int,int]]:
        valid_moves = []
        if self.team == "white":
            # Move one forward
            if self.y + 1 < 8 and self.game.get_piece_at(self.x, self.y + 1) is None:
                valid_moves.append((self.x, self.y + 1))
            # Move two forward on start field
            if self.y == 1 and self.game.get_piece_at(self.x, self.y + 1) is None and self.game.get_piece_at(self.x, self.y + 2) is None:
                valid_moves.append((self.x, self.y + 2))
            # Take sideways
            if self.x - 1 >= 0 and self.y + 1 < 8 and self.game.get_piece_at(self.x - 1, self.y + 1) is not None:
                valid_moves.append((self.x - 1, self.y + 1))
            if self.x + 1 < 8 and self.y + 1 < 8 and self.game.get_piece_at(self.x + 1, self.y + 1) is not None:
                valid_moves.append((self.x + 1, self.y + 1))
        else:
            # Move one forward
            if self.y - 1 >= 0 and self.game.get_piece_at(self.x, self.y - 1) is None:
                valid_moves.append((self.x, self.y - 1))
            # Move two forward on start field
            if self.y == 6 and self.game.get_piece_at(self.x, self.y - 1) is None and self.game.get_piece_at(self.x, self.y - 2) is None:
                valid_moves.append((self.x, self.y - 2))
            # Take sideways
            if self.x - 1 >= 0 and self.y - 1 >= 0 and self.game.get_piece_at(self.x - 1, self.y - 1) is not None:
                valid_moves.append((self.x - 1, self.y - 1))
            if self.x + 1 < 8 and self.y - 1 >= 0 and self.game.get_piece_at(self.x + 1, self.y - 1) is not None:
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
            if self.game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.x - 1, -1, -1):
            valid_moves.append((i, self.y))
            if self.game.get_piece_at(i, self.y) is not None:
                break
        # Vertical moves
        for i in range(self.y + 1, 8):
            valid_moves.append((self.x, i))
            if self.game.get_piece_at(self.x, i) is not None:
                break
        for i in range(self.y - 1, -1, -1):
            valid_moves.append((self.x, i))
            if self.game.get_piece_at(self.x, i) is not None:
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
                if self.game.get_piece_at(self.x + i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x + i < 8 and self.y - i >= 0:
                valid_moves.append((self.x + i, self.y - i))
                if self.game.get_piece_at(self.x + i, self.y - i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y + i < 8:
                valid_moves.append((self.x - i, self.y + i))
                if self.game.get_piece_at(self.x - i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y - i >= 0:
                valid_moves.append((self.x - i, self.y - i))
                if self.game.get_piece_at(self.x - i, self.y - i) is not None:
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
            if self.game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.x - 1, -1, -1):
            valid_moves.append((i, self.y))
            if self.game.get_piece_at(i, self.y) is not None:
                break
        for i in range(self.y + 1, 8):
            valid_moves.append((self.x, i))
            if self.game.get_piece_at(self.x, i) is not None:
                break
        for i in range(self.y - 1, -1, -1):
            valid_moves.append((self.x, i))
            if self.game.get_piece_at(self.x, i) is not None:
                break
        # Diagonal moves
        for i in range(1, 8):
            if self.x + i < 8 and self.y + i < 8:
                valid_moves.append((self.x + i, self.y + i))
                if self.game.get_piece_at(self.x + i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x + i < 8 and self.y - i >= 0:
                valid_moves.append((self.x + i, self.y - i))
                if self.game.get_piece_at(self.x + i, self.y - i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y + i < 8:
                valid_moves.append((self.x - i, self.y + i))
                if self.game.get_piece_at(self.x - i, self.y + i) is not None:
                    break
            else:
                break
        for i in range(1, 8):
            if self.x - i >= 0 and self.y - i >= 0:
                valid_moves.append((self.x - i, self.y - i))
                if self.game.get_piece_at(self.x - i, self.y - i) is not None:
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

def get_key_press():
    # Set raw mode to read a single character without waiting for Enter
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        # Read a single character from the user
        key_press = sys.stdin.read(1)
        return key_press
    finally:
        # Reset terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

game = Game()
game.create_board()
game.render_board()

while True:

    source_x = None
    source_y = None
    target_x = None
    target_y = None

    while source_x is None or source_y is None:
        move_input = get_key_press()
        if re.match(r"^([A-H]|[a-h])$", move_input):
            source_x = ord(move_input[0].lower()) - 97
        elif re.match(r"^[1-8]$", move_input):
            source_y = int(move_input) - 1
    game.render_board(game.get_piece_at(source_x, source_y).get_valid_moves())
    print(source_x, source_y)
    while target_x is None or target_y is None:
        move_input = get_key_press()
        if re.match(r"^([A-H]|[a-h])$", move_input):
            target_x = ord(move_input[0].lower()) - 97
        elif re.match(r"^[1-8]$", move_input):
            target_y = int(move_input) - 1
    # Check if the move is valid and make the move
    if source_x is not None and source_y is not None and target_x is not None and target_y is not None:
        piece = game.get_piece_at(source_x, source_y)
        if piece is None:
            print("Invalid move. Please enter a valid move.")
            continue

        valid_moves = piece.get_valid_moves()
        if (target_x, target_y) not in valid_moves:
            print("Invalid move. Please enter a valid move.")
            continue

        game.move_piece(source_x, source_y, target_x, target_y)
    else:
        print("Invalid move. Please enter a valid move.")