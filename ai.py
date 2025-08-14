# ai.py
# This file contains the logic for an AI player using the Google Gemini API.

import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from a .env file
load_dotenv()

# The API key is now passed directly to the client
API_KEY = os.getenv("GEMINI_API_KEY")

class AIPlayer:
    """
    An AI player that uses a Google Gemini model to decide on a chess move.
    """
    def __init__(self):
        """Initializes the Gemini client."""
        try:
            if not API_KEY:
                raise ValueError("GEMINI_API_KEY not found in .env file.")
            # Use the newer genai.Client interface
            self.client = genai.Client(api_key=API_KEY)
            self.model = "gemini-2.5-flash"
            print("Gemini AI Player initialized successfully.")
        except Exception as e:
            print(f"ERROR: Could not initialize Gemini client: {e}")
            self.client = None

    def get_best_move(self, fen_string):
        """
        Given the current board state in FEN, asks the AI for the best move via the Gemini API.
        """
        if not self.client:
            print(f"ERROR: Gemini client not initialized.")
            return None

        # Prompt with legality requirement
        prompt = (
            "You are a helpful chess assistant. Your goal is to identify the best possible move. "
            "You must respond ONLY with the move in 4-character long algebraic notation (e.g., 'e2e4' or 'e4d5' for a capture). "
            "Do not use 'x' for captures. Before responding, double-check that your chosen move is a legal move for the current player according to the provided FEN string. "
            "Do not add any commentary or explanation.\n\n"
            "Example:\n"
            "User: Given the FEN string 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', what is the best move for the current player?\n"
            "Model: e2e4\n\n"
            f"User: Given the FEN string '{fen_string}', what is the best move for the current player?\n"
            "Model:"
        )

        generation_config = types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,  # Disables thinking
            ),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generation_config
            )

            # In google-genai, .text returns the combined output
            if not response.candidates:
                finish_reason = response.candidates[0].finish_reason if response.candidates else 'UNKNOWN'
                print(f"ERROR: Gemini response was blocked or empty. Finish Reason: {finish_reason}")
                return None

            response_text = response.text.strip()
            match = re.search(r'[a-h][1-8][a-h][1-8]', response_text)

            if match:
                return match.group(0)
            else:
                print(f"ERROR: Could not find a valid move in AI response: '{response_text}'")
                return None

        except Exception as e:
            print(f"ERROR: An API request error occurred: {e}")
            return None
