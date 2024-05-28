from typing import List, Tuple, NoReturn
import os
import sys
import tty
import termios
import re

class Game:
    __board = None
    current_player = None
    black_castling_kingside = black_castling_queenside = white_castling_kingside = white_castling_queenside = True
    last_move = None
    moves_since_last_significant = 0
    game_over = False
    result = None
    end_message = None

    def __init__(self):
        # Initialize the chess game
        self.__board = self.create_board()
        self.current_player = "white"

    def get_piece_at(self, x: int, y: int) -> 'Piece | None':
        """Return the piece at the specified x and y coordinates"""
        return self.__board[y][x]
    
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
        self.__board[y][x] = None
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
            self.__board[y][target_x] = None
        # add support for castling
        if isinstance(piece, King):
            if piece.team == "white":
                if not sim:
                    self.white_castling_queenside = self.white_castling_kingside = False
                if target_x == 6 and x == 4:
                    rook = self.get_piece_at(7, 0)
                    self.__board[0][7] = None
                    self.__board[0][5] = rook
                    rook.x = 5
                    rook.y = 0
                elif target_x == 2 and x == 4:
                    rook = self.get_piece_at(0, 0)
                    self.__board[0][0] = None
                    self.__board[0][3] = rook
                    rook.x = 3
                    rook.y = 0
            elif piece.team == "black":
                if not sim:
                    self.black_castling_queenside = self.black_castling_kingside = False
                if target_x == 6 and x == 4:
                    rook = self.get_piece_at(7, 7)
                    self.__board[7][7] = None
                    self.__board[7][5] = rook
                    rook.x = 5
                    rook.y = 7
                elif target_x == 2 and x == 4:
                    rook = self.get_piece_at(0, 7)
                    self.__board[7][0] = None
                    self.__board[7][3] = rook
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

        self.__board[target_y][target_x] = piece
        piece.x = target_x
        piece.y = target_y
        if not sim:
            self.current_player = "black" if self.current_player == "white" else "white"
            self.render_board()
            self.last_move = (x, y, target_x, target_y)
            self.moves_since_last_significant += 1

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

    def is_check_after_move(self, x: int, y: int, target_x: int, target_y: int) -> bool:
        """Check if the current player is in check after a move"""
        piece = self.get_piece_at(x, y)
        target_piece = self.get_piece_at(target_x, target_y)
        self.__board[y][x] = None
        self.__board[target_y][target_x] = piece
        piece.x = target_x
        piece.y = target_y
        is_check = self.is_check(self.current_player)
        self.__board[y][x] = piece
        self.__board[target_y][target_x] = target_piece
        piece.x = x
        piece.y = y
        return is_check

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
        #self.__board = [[Rook(self, "white", 0, 0), None, None, None, King(self, "white", 4, 0), None, None, Rook(self, "white", 7, 0)],
        #     [None, Pawn(self, "white", 1, 1), None, None, None, None, None, None],
        #     [None, None, None, None, None, None, None, None],
        #     [None, None, None, None, None, None, None, None],
        #     [None, None, None, None, None, None, King(self, "black", 5, 4), None],
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
    
    def get_valid_moves(self, moves) -> List[Tuple[int,int]]:
        """Return a List of Tuples with valid Moves"""
        # remove self taking moves
        valid_moves = []
        for move in moves:
            piece = self.game.get_piece_at(move[0], move[1])
            if piece is not None and piece.team == self.team:
                continue
            valid_moves.append(move)
        #cache = valid_moves
        #valid_moves = []
        #for move in cache:
        #    if self.game.is_check_after_move(self.x, self.y, move[0], move[1]):
        #        valid_moves.append(move)
        return valid_moves

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
        return super().get_valid_moves(valid_moves)

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
        return super().get_valid_moves(valid_moves)

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
        return super().get_valid_moves(valid_moves)

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
        return super().get_valid_moves(valid_moves)

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
        return super().get_valid_moves(valid_moves)

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
        return super().get_valid_moves(valid_moves)

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
    
def game_loop() -> Tuple[str, str]:
    game = Game()
    game.create_board()
    game.render_board()

    while True:
        # Get the source and target coordinates from the user
        while True:
            source_x, source_y = get_coords(game)
            if game.game_over:
                return (game.result, game.end_message)
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
                return (game.result, game.end_message)
            if (target_x, target_y) in game.get_piece_at(source_x, source_y).get_valid_moves():
                break
            else:
                print("Invalid move. Please enter a valid move.")

        game.move_piece(source_x, source_y, target_x, target_y)
        game.render_board()
        if game.moves_since_last_significant >= 150:
            game.game_over = True
            game.result = "remis"
            game.end_message = "Game ended in a remis due to 75 moves rule."
            return (game.result, game.end_message)

result, message = game_loop()
print("game ended", result, message)