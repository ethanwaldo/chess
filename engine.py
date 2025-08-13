# engine.py
# Game logic and state management

import time
from config import BOARD_DIMENSION, PIECE_SYMBOLS
from pieces import Pawn, Rook, Knight, Bishop, Queen, King


class Player:
    """Represents a chess player."""

    def __init__(self, name, is_player1):
        self.name = name
        self.is_player1 = is_player1
        self.color = 'white' if is_player1 else 'black'


class Move:
    """Represents a single chess move, including its duration and special flags."""

    def __init__(self,
                 piece_moved,
                 start_coords,
                 end_coords,
                 piece_captured=None,
                 is_promotion=False,
                 promoted_piece=None,
                 piece_had_moved=False,
                 turn_duration=0.0,
                 is_castling=False,
                 is_en_passant=False):
        self.piece_moved = piece_moved
        self.start_coords = start_coords
        self.end_coords = end_coords
        self.piece_captured = piece_captured
        self.is_promotion = is_promotion
        self.promoted_piece = promoted_piece
        self.piece_had_moved = piece_had_moved
        self.turn_duration = turn_duration
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant

    def to_notation(self):
        """Generates simple algebraic notation for the move."""
        if self.is_castling:
            return "O-O" if self.end_coords[1] > self.start_coords[
                1] else "O-O-O"

        piece_symbol = self.piece_moved.name if self.piece_moved.name != 'P' else ''
        start = f"{chr(ord('a') + self.start_coords[1])}{8 - self.start_coords[0]}"
        end = f"{chr(ord('a') + self.end_coords[1])}{8 - self.end_coords[0]}"
        capture_symbol = 'x' if self.piece_captured else '-'
        notation = f"{piece_symbol}{start}{capture_symbol}{end}"
        if self.is_promotion:
            notation += f"={self.promoted_piece.name}"
        return notation


class Game:
    """The main game engine that manages chess logic and state."""

    def __init__(self):
        self.board = [[None for _ in range(BOARD_DIMENSION)]
                      for _ in range(BOARD_DIMENSION)]
        self.players = [Player("White", True), Player("Black", False)]
        self.current_player_index = 0
        self.game_state = 'active'
        self.move_history = []
        self.white_captured = []
        self.black_captured = []
        self.turn_start_time = time.time()
        self.white_turn_time = 0
        self.black_turn_time = 0
        self.halfmove_clock = 0
        self.position_history = {}
        self._place_pieces()
        self._update_position_history()

    def make_move(self, start_coords, end_coords, promotion_choice=None):
        """Executes a move, assuming it has been pre-validated by the GUI."""
        piece_to_move = self.get_piece_at(start_coords)

        if not piece_to_move or piece_to_move.is_player1 != self.get_current_player(
        ).is_player1:
            return False

        elapsed_time = time.time() - self.turn_start_time
        move_details = self._execute_board_move(start_coords, end_coords,
                                                promotion_choice, elapsed_time)
        self._update_game_after_move(move_details)
        return True

    def undo_last_move(self):
        if not self.move_history: return
        move = self.move_history.pop()

        self.set_piece_at(move.start_coords, move.piece_moved)
        move.piece_moved.has_moved = move.piece_had_moved

        if move.is_castling:
            rook_start_col = 7 if move.end_coords[1] > move.start_coords[
                1] else 0
            rook_end_col = 5 if rook_start_col == 7 else 3
            rook = self.get_piece_at((move.start_coords[0], rook_end_col))
            self.set_piece_at((move.start_coords[0], rook_start_col), rook)
            self.set_piece_at((move.start_coords[0], rook_end_col), None)
            if rook: rook.has_moved = False
            self.set_piece_at(move.end_coords, None)
        elif move.is_en_passant:
            captured_pawn_row = move.start_coords[0]
            self.set_piece_at((captured_pawn_row, move.end_coords[1]),
                              move.piece_captured)
            self.set_piece_at(move.end_coords, None)
        else:
            self.set_piece_at(move.end_coords, move.piece_captured)

        if move.piece_captured:
            if move.piece_moved.is_player1: self.black_captured.pop()
            else: self.white_captured.pop()

        if move.piece_moved.is_player1:
            self.white_turn_time -= move.turn_duration
        else:
            self.black_turn_time -= move.turn_duration

        self.current_player_index = 1 - self.current_player_index
        self.turn_start_time = time.time()
        self._update_game_status()

    def get_legal_moves_for_piece(self, coords):
        piece = self.get_piece_at(coords)
        if not piece: return []

        pseudo_legal_moves = piece.get_moves(self.board, coords,
                                             self.move_history)
        if isinstance(piece, King):
            pseudo_legal_moves.extend(self._get_castling_moves(coords))

        legal_moves = []
        for move_coords in pseudo_legal_moves:
            if not self._move_results_in_check(coords, move_coords):
                legal_moves.append(move_coords)
        return legal_moves

    def is_in_check(self, player):
        king_pos = self._find_piece_by_type(King, player)
        return self._is_square_attacked(
            king_pos, not player.is_player1) if king_pos else False

    def get_piece_at(self, coords):
        return self.board[coords[0]][coords[1]]

    def set_piece_at(self, coords, piece):
        self.board[coords[0]][coords[1]] = piece

    def get_current_player(self):
        return self.players[self.current_player_index]

    def resign(self):
        self.game_state = f'resignation - {"Black" if self.current_player_index == 0 else "White"} wins'

    def offer_draw(self):
        self.game_state = 'draw by agreement'

    def to_fen(self):
        """Generates the Forsyth-Edwards Notation (FEN) string for the current game state."""
        fen_board = ""
        for r in range(BOARD_DIMENSION):
            empty_squares = 0
            for c in range(BOARD_DIMENSION):
                piece = self.board[r][c]
                if piece:
                    if empty_squares > 0:
                        fen_board += str(empty_squares)
                        empty_squares = 0
                    symbol = PIECE_SYMBOLS[piece.color][piece.name]
                    fen_board += symbol
                else:
                    empty_squares += 1
            if empty_squares > 0:
                fen_board += str(empty_squares)
            if r < BOARD_DIMENSION - 1:
                fen_board += '/'

        active_color = 'w' if self.current_player_index == 0 else 'b'

        castling_rights = ""
        king_w = self.get_piece_at((7, 4))
        rook_wk = self.get_piece_at((7, 7))
        if isinstance(king_w, King) and not king_w.has_moved and isinstance(
                rook_wk, Rook) and not rook_wk.has_moved:
            castling_rights += "K"
        rook_wq = self.get_piece_at((7, 0))
        if isinstance(king_w, King) and not king_w.has_moved and isinstance(
                rook_wq, Rook) and not rook_wq.has_moved:
            castling_rights += "Q"
        king_b = self.get_piece_at((0, 4))
        rook_bk = self.get_piece_at((0, 7))
        if isinstance(king_b, King) and not king_b.has_moved and isinstance(
                rook_bk, Rook) and not rook_bk.has_moved:
            castling_rights += "k"
        rook_bq = self.get_piece_at((0, 0))
        if isinstance(king_b, King) and not king_b.has_moved and isinstance(
                rook_bq, Rook) and not rook_bq.has_moved:
            castling_rights += "q"
        if not castling_rights: castling_rights = "-"

        en_passant_target = "-"
        if self.move_history:
            last_move = self.move_history[-1]
            if isinstance(last_move.piece_moved,
                          Pawn) and abs(last_move.start_coords[0] -
                                        last_move.end_coords[0]) == 2:
                target_row = (last_move.start_coords[0] +
                              last_move.end_coords[0]) // 2
                target_col = last_move.start_coords[1]
                en_passant_target = f"{chr(ord('a') + target_col)}{8 - target_row}"

        halfmove_clock = str(self.halfmove_clock)
        fullmove_number = str(len(self.move_history) // 2 + 1)
        return " ".join([
            fen_board, active_color, castling_rights, en_passant_target,
            halfmove_clock, fullmove_number
        ])

    # --- Helper Methods ---
    def _place_pieces(self):
        for col in range(BOARD_DIMENSION):
            self.board[1][col], self.board[6][col] = Pawn(False), Pawn(True)
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece in enumerate(piece_order):
            self.board[0][col], self.board[7][col] = piece(False), piece(True)

    def _execute_board_move(self, start_coords, end_coords, promotion_choice,
                            elapsed_time):
        piece = self.get_piece_at(start_coords)
        captured_piece = self.get_piece_at(end_coords)

        if isinstance(piece, Pawn) or captured_piece is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        piece_had_moved, is_castling, is_en_passant = piece.has_moved, False, False

        if isinstance(piece,
                      King) and abs(start_coords[1] - end_coords[1]) == 2:
            is_castling = True
            rook_start_col = 7 if end_coords[1] > start_coords[1] else 0
            rook_end_col = 5 if rook_start_col == 7 else 3
            rook = self.get_piece_at((start_coords[0], rook_start_col))
            self.set_piece_at((start_coords[0], rook_end_col), rook)
            self.set_piece_at((start_coords[0], rook_start_col), None)
            if rook: rook.has_moved = True
        elif isinstance(
                piece, Pawn
        ) and start_coords[1] != end_coords[1] and captured_piece is None:
            is_en_passant = True
            captured_pawn_row = start_coords[0]
            captured_pawn_col = end_coords[1]
            captured_piece = self.get_piece_at(
                (captured_pawn_row, captured_pawn_col))
            self.set_piece_at((captured_pawn_row, captured_pawn_col), None)

        if captured_piece:
            if piece.is_player1: self.black_captured.append(captured_piece)
            else: self.white_captured.append(captured_piece)

        promoted_piece = None
        is_promotion = isinstance(piece, Pawn) and end_coords[0] in (0, 7)
        if is_promotion:
            piece_map = {'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
            promoted_class = piece_map.get(promotion_choice, Queen)
            promoted_piece = promoted_class(piece.is_player1)
            self.set_piece_at(end_coords, promoted_piece)
        else:
            self.set_piece_at(end_coords, piece)

        self.set_piece_at(start_coords, None)
        piece.has_moved = True
        return Move(piece, start_coords, end_coords, captured_piece,
                    is_promotion, promoted_piece, piece_had_moved,
                    elapsed_time, is_castling, is_en_passant)

    def _update_game_after_move(self, move):
        self.move_history.append(move)
        if self.current_player_index == 0:
            self.white_turn_time += move.turn_duration
        else:
            self.black_turn_time += move.turn_duration
        self.turn_start_time = time.time()
        self.current_player_index = 1 - self.current_player_index
        self._update_position_history()
        self._update_game_status()

    def _update_game_status(self):
        if self.halfmove_clock >= 100:
            self.game_state = 'draw by 50-move rule'
            return
        if self.position_history.get(self._get_position_hash(), 0) >= 3:
            self.game_state = 'draw by threefold repetition'
            return
        if self._check_insufficient_material():
            self.game_state = 'draw by insufficient material'
            return

        player = self.get_current_player()
        has_legal_move = any(
            self.get_legal_moves_for_piece((r, c))
            for r, c in self._iterate_squares()
            if self.get_piece_at((r, c)) and self.get_piece_at((
                r, c)).is_player1 == player.is_player1)

        if not has_legal_move:
            self.game_state = 'checkmate' if self.is_in_check(
                player) else 'stalemate'
        else:
            self.game_state = 'check' if self.is_in_check(player) else 'active'

    def _get_position_hash(self):
        board_str = "".join(p.name + p.color[0] if p else ' '
                            for r in self.board for p in r)
        return board_str + str(self.current_player_index)

    def _update_position_history(self):
        pos_hash = self._get_position_hash()
        self.position_history[pos_hash] = self.position_history.get(
            pos_hash, 0) + 1

    def _check_insufficient_material(self):
        pieces = [
            p for r, c in self._iterate_squares()
            if (p := self.get_piece_at((r, c)))
        ]
        if len(pieces) <= 3:
            if len(pieces) == 2: return True
            if len(pieces) == 3:
                piece_names = {p.name for p in pieces}
                if 'B' in piece_names or 'N' in piece_names:
                    return True
        return False

    def _get_castling_moves(self, king_coords):
        moves = []
        if self.is_in_check(self.get_current_player()): return moves
        row, col = king_coords
        player_is_white = self.get_current_player().is_player1
        # Kingside
        rook_kingside = self.get_piece_at((row, 7))
        if isinstance(rook_kingside, Rook) and not rook_kingside.has_moved:
            if self.get_piece_at((row, 5)) is None and self.get_piece_at(
                (row, 6)) is None:
                if not self._is_square_attacked((row, 5), not player_is_white) and \
                   not self._is_square_attacked((row, 6), not player_is_white):
                    moves.append((row, 6))
        # Queenside
        rook_queenside = self.get_piece_at((row, 0))
        if isinstance(rook_queenside, Rook) and not rook_queenside.has_moved:
            if self.get_piece_at((row, 1)) is None and self.get_piece_at(
                (row, 2)) is None and self.get_piece_at((row, 3)) is None:
                if not self._is_square_attacked((row, 2), not player_is_white) and \
                   not self._is_square_attacked((row, 3), not player_is_white):
                    moves.append((row, 2))
        return moves

    def _is_square_attacked(self, coords, by_player_is_white):
        for r, c in self._iterate_squares():
            piece = self.get_piece_at((r, c))
            if piece and piece.is_player1 == by_player_is_white:
                if coords in piece.get_moves(self.board, (r, c),
                                             self.move_history):
                    return True
        return False

    def _move_results_in_check(self, start_coords, end_coords):
        piece = self.get_piece_at(start_coords)
        captured_piece = self.get_piece_at(end_coords)
        self.set_piece_at(end_coords, piece)
        self.set_piece_at(start_coords, None)
        in_check = self.is_in_check(self.get_current_player())
        self.set_piece_at(start_coords, piece)
        self.set_piece_at(end_coords, captured_piece)
        return in_check

    def _iterate_squares(self):
        for r in range(BOARD_DIMENSION):
            for c in range(BOARD_DIMENSION):
                yield r, c

    def _find_piece_by_type(self, piece_type, player):
        for r, c in self._iterate_squares():
            piece = self.board[r][c]
            if isinstance(
                    piece,
                    piece_type) and piece.is_player1 == player.is_player1:
                return (r, c)
        return None
