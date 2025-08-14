# stockfish_player.py
# This file contains the logic for the Stockfish AI player.

import chess
import chess.engine
import os
import time

# --- IMPORTANT ---
# You must download the Stockfish engine and provide the correct path to the executable below.
#
# - For Windows: "C:/path/to/stockfish/stockfish.exe"
# - For Linux/macOS: "/path/to/stockfish"
#
# Download from: https://stockfishchess.org/download/
STOCKFISH_PATH = "stockfish/stockfish-ubuntu-x86-64-avx2"

class StockfishPlayer:
    """
    An AI player that uses the Stockfish chess engine to decide on a move.
    """
    def __init__(self, skill_level=5, time_limit=0.1):
        """
        Initializes the Stockfish player.
        Args:
            skill_level (int): UCI skill level (0-20). Lower is easier.
            time_limit (float): Time in seconds for the engine to think.
        """
        self.engine = None
        self.time_limit = time_limit
        try:
            # This will work if stockfish is in your system's PATH.
            # If not, it will fail, and you must set the STOCKFISH_PATH manually.
            self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            # Configure the engine's difficulty
            self.engine.configure({"Skill Level": skill_level})
            print("Stockfish engine loaded successfully.")
        except FileNotFoundError:
            print(f"ERROR: Stockfish executable not found at '{STOCKFISH_PATH}'.")
            print("Please download Stockfish, place it in your project folder, or update the STOCKFISH_PATH in stockfish_player.py.")
        except Exception as e:
            print(f"ERROR: Could not load Stockfish engine: {e}")

    def get_best_move(self, fen_string):
        """
        Given the current board state in FEN, asks Stockfish for the best move.
        """
        if not self.engine:
            print("ERROR: Stockfish engine is not available.")
            return None

        try:
            board = chess.Board(fen_string)
            print(f"LOG (Stockfish Thread @ {time.strftime('%H:%M:%S')}): Analyzing position...")
            
            # Ask the engine to analyze the position for a fixed amount of time
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            move = result.move.uci() # The move is returned in UCI format (e.g., 'e2e4')
            
            print(f"LOG (Stockfish Thread @ {time.strftime('%H:%M:%S')}): Stockfish suggests move: {move}")
            return move
        except Exception as e:
            print(f"An error occurred during Stockfish analysis: {e}")
            return None

    def quit(self):
        """Closes the Stockfish engine process to free up resources."""
        if self.engine:
            self.engine.quit()
            print("Stockfish engine shut down.")

