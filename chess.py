from typing import List, Tuple, NoReturn
import os
import sys
import tty
import termios
import re
import sqlite3
import ast

class Game:
    board: list = None
    current_player: str = None
    black_castling_kingside = black_castling_queenside = white_castling_kingside = white_castling_queenside = True
    last_move = None
    moves_since_last_significant: int = 0
    game_over: bool = False
    result: str = None
    end_message: str = None

    def __init__(self):
        # Initialize the chess game
        self.board = self.create_board()
        self.current_player = "white"

    def get_piece_at(self, x: int, y: int) -> 'Piece | None':
        """Return the piece at the specified x and y coordinates"""
        return self.board[y][x]
    
    # Render the board in the terminal
    def render_board(self, valid_moves: List[Tuple[int,int]] = []):
        """Render the board in the terminal with a checkboard pattern"""
        os.system('clear')  # Clear the terminal output
        print("It's {}'s turn.".format(self.current_player))
        print("  A B C D E F G H")
        for y in range(8):
            print(f"{8-y} ", end="")
            for x in range(8):
                piece = self.get_piece_at(x, (7-y))
                if (x, (7-y)) in valid_moves:
                    print("\033[48;2;0;255;0m", end="")
                    pass
                elif (x + y) % 2 == 1:
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
        if self.moves_since_last_significant >= 100:
            print("50 or more unsignificant moves passed. Press (r) for remis or continue playing.")
    
    def move_piece(self, x: int, y: int, target_x: int, target_y: int, sim: bool = False):
        """Move a piece to a new position"""
        piece = self.get_piece_at(x, y)
        self.board[y][x] = None
        # add support for pawn promotion
        if isinstance(piece, Pawn) and ((piece.team == "white" and target_y == 7) or (piece.team == "black" and target_y == 0)):
            while True:
                if sim:
                    wish = "q"
                else:
                    print("Which piece do you want to promote to? (q, r, b, n): ")
                    wish = get_key_press()
                if re.match(r"^[qrbn]$", wish):
                    break
            match wish:
                case "q":
                    piece = Queen(self, piece.team, target_x, target_y)
                case "r":
                    piece = Rook(self, piece.team, target_x, target_y)
                case "b":
                    piece = Bishop(self, piece.team, target_x, target_y)
                case "n":
                    piece = Knight(self, piece.team, target_x, target_y)
        # add support for en passant
        if isinstance(piece, Pawn) and x != target_x and self.get_piece_at(target_x, target_y) is None:
            self.board[y][target_x] = None
        # add support for castling
        if isinstance(piece, King):
            if piece.team == "white":
                if not sim:
                    self.white_castling_queenside = self.white_castling_kingside = False
                if target_x == 6 and x == 4:
                    rook = self.get_piece_at(7, 0)
                    self.board[0][7] = None
                    self.board[0][5] = rook
                    rook.x = 5
                    rook.y = 0
                elif target_x == 2 and x == 4:
                    rook = self.get_piece_at(0, 0)
                    self.board[0][0] = None
                    self.board[0][3] = rook
                    rook.x = 3
                    rook.y = 0
            elif piece.team == "black":
                if not sim:
                    self.black_castling_queenside = self.black_castling_kingside = False
                if target_x == 6 and x == 4:
                    rook = self.get_piece_at(7, 7)
                    self.board[7][7] = None
                    self.board[7][5] = rook
                    rook.x = 5
                    rook.y = 7
                elif target_x == 2 and x == 4:
                    rook = self.get_piece_at(0, 7)
                    self.board[7][0] = None
                    self.board[7][3] = rook
                    rook.x = 3
                    rook.y = 7
        # dissalow castling if rook gets moved or taken
        if not sim:
            if (piece.x == 0 and piece.y == 0) or (target_x == 0 and target_y == 0):
                self.white_castling_queenside = False
            elif (piece.x == 7 and piece.y == 0) or (target_x == 7 and target_y == 0):
                self.white_castling_kingside = False
            elif (piece.x == 0 and piece.y == 7) or (target_x == 0 and target_y == 7):
                self.black_castling_queenside = False
            elif (piece.x == 7 and piece.y == 7) or (target_x == 7 and target_y == 7):
                self.black_castling_kingside = False
            if isinstance(piece, Pawn) or self.get_piece_at(target_x, target_y) is not None:
                self.moves_since_last_significant = 0

        self.board[target_y][target_x] = piece
        piece.x = target_x
        piece.y = target_y
        if not sim:
            self.current_player = "black" if self.current_player == "white" else "white"
            self.render_board()
            self.last_move = (x, y, target_x, target_y)
            self.moves_since_last_significant += 1

    def is_check(self, player: str, no_recursion: bool = False) -> bool:
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
            valid_moves = piece.get_valid_moves(no_recursion)
            if king_position in valid_moves:
                return True
        
        return False

    def is_check_after_move(self, x: int, y: int, target_x: int, target_y: int) -> bool:
        """Check if the current player is in check after a move"""
        piece = self.get_piece_at(x, y)
        target_piece = self.get_piece_at(target_x, target_y)
        self.board[y][x] = None
        self.board[target_y][target_x] = piece
        piece.x = target_x
        piece.y = target_y
        is_check = self.is_check(self.current_player, True)
        self.board[y][x] = piece
        self.board[target_y][target_x] = target_piece
        piece.x = x
        piece.y = y
        return is_check
    
    def has_valid_mvoes(self, player: str) -> bool:
        """Check if the specified player has any valid moves"""
        for y in range(8):
            for x in range(8):
                piece = self.get_piece_at(x, y)
                if piece is not None and piece.team == player and piece.get_valid_moves() != []:
                    return True
        return False

    def create_board(self):
        """Create and return the initial chess board"""
        self.board = [[Rook(self, "white", 0, 0), Knight(self, "white", 1, 0), Bishop(self, "white", 2, 0), Queen(self, "white", 3, 0), King(self, "white", 4, 0), Bishop(self, "white", 5, 0), Knight(self, "white", 6, 0), Rook(self, "white", 7, 0)],
             [Pawn(self, "white", 0, 1), Pawn(self, "white", 1, 1), Pawn(self, "white", 2, 1), Pawn(self, "white", 3, 1), Pawn(self, "white", 4, 1), Pawn(self, "white", 5, 1), Pawn(self, "white", 6, 1), Pawn(self, "white", 7, 1)],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [None, None, None, None, None, None, None, None],
             [Pawn(self, "black", 0, 6), Pawn(self, "black", 1, 6), Pawn(self, "black", 2, 6), Pawn(self, "black", 3, 6), Pawn(self, "black", 4, 6), Pawn(self, "black", 5, 6), Pawn(self, "black", 6, 6), Pawn(self, "black", 7, 6)],
             [Rook(self, "black", 0, 7), Knight(self, "black", 1, 7), Bishop(self, "black", 2, 7), Queen(self, "black", 3, 7), King(self, "black", 4, 7), Bishop(self, "black", 5, 7), Knight(self, "black", 6, 7), Rook(self, "black", 7, 7)]]
        #self.board = [[Rook(self, "white", 0, 0), None, None, None, King(self, "white", 4, 0), None, None, Rook(self, "white", 7, 0)],
        #     [None, Pawn(self, "white", 1, 1), None, None, None, None, None, None],
        #     [None, None, None, None, None, None, None, None],
        #     [None, None, None, None, None, None, None, None],
        #     [None, None, None, None, None, None, King(self, "black", 6, 4), None],
        #     [None, None, None, None, None, None, None, None],
        #     [Pawn(self, "black", 0, 6), None, None, None, None, None, None, None],
        #     [None, None, None, None, None, None, None, None]]

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
    
    def get_valid_moves(self, moves, no_recursion: bool = False) -> List[Tuple[int,int]]:
        """Return a List of Tuples with valid Moves"""
        # remove self taking moves
        valid_moves = []
        for move in moves:
            piece = self.game.get_piece_at(move[0], move[1])
            if piece is not None and piece.team == self.team:
                continue
            valid_moves.append(move)
        if not no_recursion:
            cache = valid_moves
            valid_moves = []
            for move in cache:
                if not self.game.is_check_after_move(self.x, self.y, move[0], move[1]):
                    valid_moves.append(move)
        return valid_moves

    def get_game(self) -> Game:
        return self.game

class Pawn(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        super().__init__(game, team, x, y, "\u265F")
    
    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
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
            # En passant
            if self.y == 4:
                if self.x - 1 >= 0 and self.game.get_piece_at(self.x - 1, self.y) is not None and isinstance(self.game.get_piece_at(self.x - 1, self.y), Pawn) and self.game.last_move == (self.x - 1, self.y + 2, self.x - 1, self.y):
                    valid_moves.append((self.x - 1, self.y + 1))
                if self.x + 1 < 8 and self.game.get_piece_at(self.x + 1, self.y) is not None and isinstance(self.game.get_piece_at(self.x + 1, self.y), Pawn) and self.game.last_move == (self.x + 1, self.y + 2, self.x + 1, self.y):
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
            # En passant
            if self.y == 3:
                if self.x - 1 >= 0 and self.game.get_piece_at(self.x - 1, self.y) is not None and isinstance(self.game.get_piece_at(self.x - 1, self.y), Pawn) and self.game.last_move == (self.x - 1, self.y - 2, self.x - 1, self.y):
                    valid_moves.append((self.x - 1, self.y - 1))
                if self.x + 1 < 8 and self.game.get_piece_at(self.x + 1, self.y) is not None and isinstance(self.game.get_piece_at(self.x + 1, self.y), Pawn) and self.game.last_move == (self.x + 1, self.y - 2, self.x + 1, self.y):
                    valid_moves.append((self.x + 1, self.y - 1))
        return super().get_valid_moves(valid_moves, no_recursion)

class Rook(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265C")
    
    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
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
        return super().get_valid_moves(valid_moves, no_recursion)

class Knight(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265E")

    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
        valid_moves = []
        moves = [(self.x + 2, self.y + 1), (self.x + 2, self.y - 1),
                    (self.x - 2, self.y + 1), (self.x - 2, self.y - 1),
                    (self.x + 1, self.y + 2), (self.x + 1, self.y - 2),
                    (self.x - 1, self.y + 2), (self.x - 1, self.y - 2)]
        for move in moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                valid_moves.append(move)
        return super().get_valid_moves(valid_moves, no_recursion)

class Bishop(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265D")
    
    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
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
        return super().get_valid_moves(valid_moves, no_recursion)

class Queen(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265B")
    
    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
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
        return super().get_valid_moves(valid_moves, no_recursion)

class King(Piece):
    def __init__(self, game: Game, team: str, x: int, y: int) -> NoReturn:
        Piece.__init__(self, game, team, x, y, "\u265A")
    
    def get_valid_moves(self, no_recursion: bool = False) -> List[Tuple[int,int]]:
        valid_moves = []
        moves = [(self.x + 1, self.y), (self.x - 1, self.y),
                    (self.x, self.y + 1), (self.x, self.y - 1),
                    (self.x + 1, self.y + 1), (self.x + 1, self.y - 1),
                    (self.x - 1, self.y + 1), (self.x - 1, self.y - 1)]
        for move in moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                valid_moves.append(move)
        # castling
        if self.team == "white":
            if self.game.white_castling_kingside:
                if self.game.get_piece_at(5, 0) is None and self.game.get_piece_at(6, 0) is None:
                    valid_moves.append((6, 0))
            if self.game.white_castling_queenside:
                if self.game.get_piece_at(1, 0) is None and self.game.get_piece_at(2, 0) is None and self.game.get_piece_at(3, 0) is None:
                    valid_moves.append((2, 0))
        else:
            if self.game.black_castling_kingside:
                if self.game.get_piece_at(5, 7) is None and self.game.get_piece_at(6, 7) is None:
                    valid_moves.append((6, 7))
            if self.game.black_castling_queenside:
                if self.game.get_piece_at(1, 7) is None and self.game.get_piece_at(2, 7) is None and self.game.get_piece_at(3, 7) is None:
                    valid_moves.append((2, 7))
        return super().get_valid_moves(valid_moves, no_recursion)

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

def get_coords(game: Game) -> Tuple[int,int]:
    x = y = None
    while x is None or y is None:
        move_input = get_key_press()
        if re.match(r"^([A-H]|[a-h])$", move_input):
            x = ord(move_input[0].lower()) - 97
        elif re.match(r"^[1-8]$", move_input):
            y = int(move_input) - 1
        elif move_input == "r" and game.moves_since_last_significant >= 100:
            game.game_over = True
            game.result = "remis"
            game.end_message = "Game ended in a remis due to 50 moves rule."
            return (0, 0)

    return (x, y)
    
def game_loop() -> Tuple[Tuple[str, str], str]:
    game = Game()
    game.create_board()
    game.render_board()

    while True:
        # Get the source and target coordinates from the user
        while True:
            source_x, source_y = get_coords(game)
            if game.game_over:
                return ((game.result, None), game.end_message)
            piece = game.get_piece_at(source_x, source_y)
            if piece is not None and piece.team == game.current_player and piece.get_valid_moves() != []:
                break
            else:
                print("Invalid move. Please enter a valid move.")

        game.render_board(game.get_piece_at(source_x, source_y).get_valid_moves())
        print(source_x, source_y)
        while True:
            target_x, target_y = get_coords(game)
            if game.game_over:
                return ((game.result, None), game.end_message)
            if (target_x, target_y) in game.get_piece_at(source_x, source_y).get_valid_moves():
                break
            else:
                print("Invalid move. Please enter a valid move.")

        game.move_piece(source_x, source_y, target_x, target_y)
        game.render_board()
        
        if not game.has_valid_mvoes(game.current_player):
            if game.is_check(game.current_player):
                game.game_over = True
                game.result = "checkmate"
                winner = "white" if game.current_player == "black" else "black"
                game.end_message = f"Checkmate! {winner} wins!"
                return ((game.result, winner), game.end_message)
            else:
                game.game_over = True
                game.result = "remis"
                game.end_message = "Game ended in a remis due to stalemate."
                return ((game.result, None), game.end_message)

        if game.moves_since_last_significant >= 150:
            game.game_over = True
            game.result = "remis"
            game.end_message = "Game ended in a remis due to 75 moves rule."
            return ((game.result, None), game.end_message)

def db_setup(db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS player (id INTEGER PRIMARY KEY, name TEXT, wins INTEGER, loses INTEGER, games INTEGER)")
    db.commit()

def db_check_player(db: sqlite3.Connection, name: str):
    """Check if the player exists in the database and create a new entry if not"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM player WHERE name = ?", (name,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO player (name, wins, loses, games) VALUES (?, 0, 0, 0)", (name,))

def db_update_player(db: sqlite3.Connection, white: str, black: str, result: Tuple[str, str]):
    """Update the player statistics in the database"""
    cursor = db.cursor()
    if result[0] == "checkmate":
        winner = white if result[1] == "white" else black
        loser = white if result[1] == "black" else black
        cursor.execute("UPDATE player SET wins = wins + 1 WHERE name = ?", (winner,))
        cursor.execute("UPDATE player SET loses = loses + 1 WHERE name = ?", (loser,))
    cursor.execute("UPDATE player SET games = games + 1 WHERE name = ? OR name = ?", (white, black))
    db.commit()

def db_get_statistics(db: sqlite3.Connection, name: str):
    """Return the player statistics from the database"""
    cursor = db.cursor()
    cursor.execute("SELECT wins, loses, games FROM player WHERE name = ?", (name,))
    if (row := cursor.fetchone()) is not None:
        print("Statistics for player", name)
        print("Wins: ", row[0])
        print("Loses: ", row[1])
        print("Draws: ", (row[2] - row[0] - row[1]))
    else:
        print("No player with that name found.")
        return

def export_game(game: Game) -> str:
    board = game.board
    str_array = [[None for _ in range(8)] for _ in range(8)]
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece is not None:
                match piece.__class__.__name__:
                    case "Pawn":
                        str_array[y][x] = 'p' if piece.team == "black" else 'P'
                    case "Rook":
                        str_array[y][x] = 'r' if piece.team == "black" else 'R'
                    case "Knight":
                        str_array[y][x] = 'n' if piece.team == "black" else 'N'
                    case "Bishop":
                        str_array[y][x] = 'b' if piece.team == "black" else 'B'
                    case "Queen":
                        str_array[y][x] = 'q' if piece.team == "black" else 'Q'
                    case "King":
                        str_array[y][x] = 'k' if piece.team == "black" else 'K'
            else:
                str_array[y][x] = 'e'
    return str(str_array)

db = sqlite3.connect("chess.db")
db_setup(db)

#os.system("clear")
#print("#############################################")
#print("# Welcome to Chess!                         #")
#print("#############################################")
#while True:
#    print("What do you want to do?")
#    print(" 1. Play a game")
#    print(" 2. Show statistics")
#    print(" q. Quit")
#    match get_key_press():
#        case "1":
#            white = input("Enter the name of the white player: ")
#            black = input("Enter the name of the black player: ")
#            db_check_player(db, white)
#            db_check_player(db, black)
#            result, message = game_loop()
#            print(message)
#            db_update_player(db, white, black, result)
#        case "2":
#            name = input("Enter the name of the player you want to see the statistics for: ")
#            db_get_statistics(db, name)
#            pass
#        case "q":
#            break
#db.close()
#print("Thank you for playing!")

game = Game()
game.create_board()
print(export_game(game))
rook = Rook(game, "white", 0, 0)