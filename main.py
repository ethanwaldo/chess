# main.py

# Import sys for exiting the game
import sys

# Helper to convert input like "e2" to board indices
def pos_to_coords(pos):
    col = ord(pos[0].lower()) - ord('a')
    row = 8 - int(pos[1])
    return row, col

# Base Piece class
class Piece:
    def __init__(self, name, is_player1):
        self.name = name
        self.is_player1 = is_player1  # True for Player 1, False for Player 2

    def is_valid_move(self, board, start, end):
        return False

# Pawn class
class Pawn(Piece):
    def is_valid_move(self, board, start, end):
        dir = -1 if self.is_player1 else 1
        start_row, start_col = start
        end_row, end_col = end
        if start_col == end_col:
            if board[end_row][end_col] is None:
                if end_row - start_row == dir:
                    return True
                # Allow two-step from starting row
                if (self.is_player1 and start_row == 6 and end_row - start_row == -2 and
                        board[start_row - 1][start_col] is None):
                    return True
                if (not self.is_player1 and start_row == 1 and end_row - start_row == 2 and
                        board[start_row + 1][start_col] is None):
                    return True
        # Capturing
        if abs(end_col - start_col) == 1 and end_row - start_row == dir:
            target = board[end_row][end_col]
            if target is not None and target.is_player1 != self.is_player1:
                return True
        return False

# Knight class
class Knight(Piece):
    def is_valid_move(self, board, start, end):
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        if (dx, dy) in [(2, 1), (1, 2)]:
            target = board[end[0]][end[1]]
            return target is None or target.is_player1 != self.is_player1
        return False

# Bishop class
class Bishop(Piece):
    def is_valid_move(self, board, start, end):
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        if dx != dy:
            return False
        step_x = (end[0] - start[0]) // dx
        step_y = (end[1] - start[1]) // dy
        for i in range(1, dx):
            if board[start[0] + step_x * i][start[1] + step_y * i] is not None:
                return False
        target = board[end[0]][end[1]]
        return target is None or target.is_player1 != self.is_player1

# Rook class
class Rook(Piece):
    def is_valid_move(self, board, start, end):
        if start[0] != end[0] and start[1] != end[1]:
            return False
        if start[0] == end[0]:
            step = 1 if end[1] > start[1] else -1
            for y in range(start[1] + step, end[1], step):
                if board[start[0]][y] is not None:
                    return False
        else:
            step = 1 if end[0] > start[0] else -1
            for x in range(start[0] + step, end[0], step):
                if board[x][start[1]] is not None:
                    return False
        target = board[end[0]][end[1]]
        return target is None or target.is_player1 != self.is_player1

# Queen class (combines rook and bishop)
class Queen(Piece):
    def is_valid_move(self, board, start, end):
        return Rook(self.name, self.is_player1).is_valid_move(board, start, end) or \
               Bishop(self.name, self.is_player1).is_valid_move(board, start, end)

# King class (one-square in any direction)
class King(Piece):
    def is_valid_move(self, board, start, end):
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        if dx <= 1 and dy <= 1:
            target = board[end[0]][end[1]]
            return target is None or target.is_player1 != self.is_player1
        return False

# Function to create the initial board
def create_board():
    board = [[None for _ in range(8)] for _ in range(8)]

    # Helper for back row
    def setup_back_row(row, is_player1):
        board[row][0] = Rook('R' if is_player1 else 'r', is_player1)
        board[row][1] = Knight('N' if is_player1 else 'n', is_player1)
        board[row][2] = Bishop('B' if is_player1 else 'b', is_player1)
        board[row][3] = Queen('Q' if is_player1 else 'q', is_player1)
        board[row][4] = King('K' if is_player1 else 'k', is_player1)
        board[row][5] = Bishop('B' if is_player1 else 'b', is_player1)
        board[row][6] = Knight('N' if is_player1 else 'n', is_player1)
        board[row][7] = Rook('R' if is_player1 else 'r', is_player1)

    # Place pieces
    setup_back_row(0, False)  # Player 2
    setup_back_row(7, True)   # Player 1

    for i in range(8):
        board[1][i] = Pawn('p', False)  # Player 2 pawns
        board[6][i] = Pawn('P', True)   # Player 1 pawns

    return board

# Function to print the board
def print_board(board):
    print("  a b c d e f g h")
    for i, row in enumerate(board):
        print(8 - i, end=' ')
        for piece in row:
            print(piece.name if piece else '.', end=' ')
        print(8 - i)
    print("  a b c d e f g h")

# Main game loop
def main():
    board = create_board()
    is_player1_turn = True

    while True:
        print_board(board)
        player = "Player 1 (UPPERCASE)" if is_player1_turn else "Player 2 (lowercase)"
        move = input(f"{player} move (e.g. e2 e4): ").strip()

        if move.lower() == "exit":
            sys.exit()

        try:
            src, dst = move.split()
            start = pos_to_coords(src)
            end = pos_to_coords(dst)

            piece = board[start[0]][start[1]]
            if piece is None:
                print("No piece at source position.")
                continue
            if piece.is_player1 != is_player1_turn:
                print("Not your piece.")
                continue
            if not piece.is_valid_move(board, start, end):
                print("Invalid move.")
                continue

            board[end[0]][end[1]] = piece
            board[start[0]][start[1]] = None
            is_player1_turn = not is_player1_turn

        except Exception as e:
            print("Invalid input. Use format like 'e2 e4'.")

if __name__ == "__main__":
    main()
