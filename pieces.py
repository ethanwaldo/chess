# pieces.py
# Chess piece classes

from config import BOARD_DIMENSION


class Piece:
    """Base class for all chess pieces."""

    def __init__(self, name, is_player1):
        self.name = name
        self.is_player1 = is_player1
        self.color = 'white' if is_player1 else 'black'
        self.has_moved = False

    def get_moves(self, board, start_coords, move_history=None):
        """Base method to be overridden by subclasses."""
        return []

    def is_enemy(self, other_piece):
        """Check if another piece is an enemy."""
        return other_piece is not None and other_piece.is_player1 != self.is_player1

    def _get_sliding_moves(self, board, start_coords, directions):
        """Helper method to get moves for sliding pieces (Rook, Bishop, Queen)."""
        moves = []
        row, col = start_coords
        for dr, dc in directions:
            for i in range(1, BOARD_DIMENSION):
                new_row, new_col = row + i * dr, col + i * dc
                if not (0 <= new_row < BOARD_DIMENSION
                        and 0 <= new_col < BOARD_DIMENSION):
                    break

                target = board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif self.is_enemy(target):
                    moves.append((new_row, new_col))
                    break
                else:  # Friendly piece
                    break
        return moves


class Pawn(Piece):

    def __init__(self, is_player1):
        super().__init__('P', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        moves = []
        row, col = start_coords
        direction = -1 if self.is_player1 else 1

        # Standard forward moves
        one_step_row = row + direction
        if 0 <= one_step_row < BOARD_DIMENSION and board[one_step_row][
                col] is None:
            moves.append((one_step_row, col))
            if not self.has_moved:
                two_step_row = row + 2 * direction
                if 0 <= two_step_row < BOARD_DIMENSION and board[two_step_row][
                        col] is None:
                    moves.append((two_step_row, col))

        # Standard captures
        for dc in [-1, 1]:
            new_row, new_col = row + direction, col + dc
            if 0 <= new_row < BOARD_DIMENSION and 0 <= new_col < BOARD_DIMENSION:
                if self.is_enemy(board[new_row][new_col]):
                    moves.append((new_row, new_col))

        # En Passant
        if move_history:
            last_move = move_history[-1]
            if (isinstance(last_move.piece_moved, Pawn)
                    and abs(last_move.start_coords[0] -
                            last_move.end_coords[0]) == 2
                    and last_move.end_coords[0] == row
                    and abs(last_move.end_coords[1] - col) == 1):
                moves.append((row + direction, last_move.end_coords[1]))

        return moves


class Rook(Piece):

    def __init__(self, is_player1):
        super().__init__('R', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return self._get_sliding_moves(board, start_coords, directions)


class Knight(Piece):

    def __init__(self, is_player1):
        super().__init__('N', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        moves = []
        row, col = start_coords
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2),
                        (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < BOARD_DIMENSION and 0 <= new_col < BOARD_DIMENSION:
                target = board[new_row][new_col]
                if target is None or self.is_enemy(target):
                    moves.append((new_row, new_col))
        return moves


class Bishop(Piece):

    def __init__(self, is_player1):
        super().__init__('B', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self._get_sliding_moves(board, start_coords, directions)


class Queen(Piece):

    def __init__(self, is_player1):
        super().__init__('Q', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1),
                      (-1, 1), (-1, -1)]
        return self._get_sliding_moves(board, start_coords, directions)


class King(Piece):

    def __init__(self, is_player1):
        super().__init__('K', is_player1)

    def get_moves(self, board, start_coords, move_history=None):
        moves = []
        row, col = start_coords
        # Standard 1-square moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < BOARD_DIMENSION and 0 <= new_col < BOARD_DIMENSION:
                    target = board[new_row][new_col]
                    if target is None or self.is_enemy(target):
                        moves.append((new_row, new_col))

        # Propose castling moves (validation happens in engine)
        if not self.has_moved:
            moves.append((row, col + 2))  # Kingside
            moves.append((row, col - 2))  # Queenside

        return moves
