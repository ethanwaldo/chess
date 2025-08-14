# gui.py
# Graphical user interface using Pygame

import pygame
import sys
import time
import threading
from config import *
from engine import Game, Pawn
from ai import AIPlayer
from stockfish import StockfishPlayer

class ChessGUI:
    """Manages the graphical user interface using Pygame."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + UI_HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.font = pygame.font.Font(None, 64)
        self.ui_font = pygame.font.Font(None, UI_FONT_SIZE)
        self.game = Game()
        
        self.selected_square = None
        self.legal_moves = []
        self.pending_promotion = None
        self.hovered_button = None
        
        # --- NEW: Player Configuration ---
        # Set each player's type. Options: "human", "stockfish", "gemini"
        self.white_player_type = "gemini"
        self.black_player_type = "stockfish"

        # --- Create player objects based on the types selected ---
        self.white_player = self._create_player(self.white_player_type)
        self.black_player = self._create_player(self.black_player_type)
        
        self.ai_is_thinking = False
        self.ai_move_result = None
        self.ai_lock = threading.Lock()

    def _create_player(self, player_type):
        """Helper function to create and return an AI player object."""
        if player_type == "stockfish":
            return StockfishPlayer()
        elif player_type == "gemini":
            return AIPlayer()
        return None # Player is human

    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        while True:
            self._handle_ai_turn_start()
            self._process_ai_result()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Cleanly quit any active AI engines
                    if self.white_player and hasattr(self.white_player, 'quit'): self.white_player.quit()
                    if self.black_player and hasattr(self.black_player, 'quit'): self.black_player.quit()
                    pygame.quit()
                    sys.exit()
                
                # Block input if an AI is thinking OR if it's an AI's turn in an AI vs AI game
                is_human_turn = (self.game.get_current_player().color == 'white' and self.white_player is None) or \
                                (self.game.get_current_player().color == 'black' and self.black_player is None)

                if not self.ai_is_thinking and is_human_turn:
                    self.handle_input(event)

            self.draw()
            pygame.display.flip()
            clock.tick(60)

    def _handle_ai_turn_start(self):
        """Checks if the current player is an AI and starts its thinking process."""
        current_player_object = self.white_player if self.game.get_current_player().color == 'white' else self.black_player
        
        is_ai_turn = (current_player_object is not None and 
                      not self.ai_is_thinking and 
                      self.game.game_state == 'active')

        if is_ai_turn:
            self.ai_is_thinking = True
            thread = threading.Thread(target=self._get_ai_move_threaded, args=(current_player_object,))
            thread.start()

    def _get_ai_move_threaded(self, ai_player):
        """This function runs in a separate thread to get the AI's move."""
        fen = self.game.to_fen()
        move = ai_player.get_best_move(fen)
        with self.ai_lock:
            self.ai_move_result = move

    def _process_ai_result(self):
        """Checks if the AI thread has finished and, if so, processes the resulting move."""
        move_to_make = None
        with self.ai_lock:
            if self.ai_move_result is not None:
                move_to_make = self.ai_move_result
                self.ai_move_result = None
        
        if move_to_make:
            start_coords, end_coords = self._parse_ai_move(move_to_make)
            if start_coords and end_coords:
                piece = self.game.get_piece_at(start_coords)
                if piece and end_coords in self.game.get_legal_moves_for_piece(start_coords):
                    self.game.make_move(start_coords, end_coords)
                else:
                    print(f"ERROR: AI suggested an illegal move: {move_to_make}")
            else:
                print(f"ERROR: AI response '{move_to_make}' could not be parsed.")
            
            self.ai_is_thinking = False

    def handle_input(self, event):
        if self.pending_promotion: self.handle_promotion_input(event); return
        if event.type == pygame.MOUSEMOTION: self.hovered_button = self._get_button_at(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            button = self._get_button_at(pos)
            if button: self.handle_button_click(button['name'])
            else: self.handle_square_click(pos)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u: self._undo_move()
            if event.key == pygame.K_r: self._reset_game_state()

    def handle_square_click(self, pos):
        coords = (pos[1] // SQUARE_SIZE, pos[0] // SQUARE_SIZE)
        if coords[0] >= BOARD_DIMENSION: return
        if self.selected_square:
            moving_piece = self.game.get_piece_at(self.selected_square)
            is_promotion = isinstance(moving_piece, Pawn) and coords[0] in (0, 7)
            if coords in self.legal_moves:
                if is_promotion: self.pending_promotion = (self.selected_square, coords)
                else:
                    if self.game.make_move(self.selected_square, coords): self._reset_ui_state()
            else: self._reset_ui_state()
        piece = self.game.get_piece_at(coords)
        if piece and piece.is_player1 == self.game.get_current_player().is_player1:
            self.selected_square = coords
            self.legal_moves = self.game.get_legal_moves_for_piece(coords)
        else: self._reset_ui_state()

    def handle_button_click(self, button_name):
        if button_name == 'New Game': self._reset_game_state()
        elif button_name == 'Resign': self.game.resign()
        elif button_name == 'Offer Draw': self.game.offer_draw()
        elif button_name == 'Undo': self._undo_move()

    def handle_promotion_input(self, event):
        if event.type != pygame.KEYDOWN: return
        key_map = {pygame.K_q: 'Q', pygame.K_r: 'R', pygame.K_b: 'B', pygame.K_n: 'N'}
        if event.key in key_map:
            start_coords, end_coords = self.pending_promotion
            if self.game.make_move(start_coords, end_coords, key_map[event.key]):
                self._reset_ui_state()
            self.pending_promotion = None

    def draw(self):
        self.screen.fill(COLOR_WHITE)
        self.draw_board(); self.draw_highlights(); self.draw_pieces(); self.draw_ui()

    def draw_board(self):
        for r in range(BOARD_DIMENSION):
            for c in range(BOARD_DIMENSION):
                color = COLOR_LIGHT_SQUARE if (r + c) % 2 == 0 else COLOR_DARK_SQUARE
                pygame.draw.rect(self.screen, color, (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        if not self.selected_square: return
        r, c = self.selected_square
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(COLOR_HIGHLIGHT); self.screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))
        s.fill(COLOR_LEGAL_MOVE)
        for r_m, c_m in self.legal_moves: self.screen.blit(s, (c_m * SQUARE_SIZE, r_m * SQUARE_SIZE))

    def draw_pieces(self):
        for r in range(BOARD_DIMENSION):
            for c in range(BOARD_DIMENSION):
                piece = self.game.board[r][c]
                if piece:
                    symbol = PIECE_SYMBOLS[piece.color][piece.name]
                    color = COLOR_WHITE if symbol.isupper() else COLOR_BLACK
                    text_surf = self.font.render(symbol, True, color)
                    text_rect = text_surf.get_rect(center=(c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text_surf, text_rect)

    def draw_ui(self):
        white_cap_str = "".join(PIECE_SYMBOLS['black'][p.name] for p in self.game.white_captured)
        black_cap_str = "".join(PIECE_SYMBOLS['white'][p.name] for p in self.game.black_captured)
        self.screen.blit(self.ui_font.render(f"White captured: {white_cap_str}", True, COLOR_BLACK), (10, CAPTURED_ROW_Y))
        self.screen.blit(self.ui_font.render(f"Black captured: {black_cap_str}", True, COLOR_BLACK), (10, CAPTURED_ROW_Y + UI_LINE_HEIGHT))
        last_move_str = f"Last Move: {self.game.move_history[-1].to_notation()}" if self.game.move_history else "Last Move: None"
        self.screen.blit(self.ui_font.render(last_move_str, True, COLOR_BLACK), (10, LAST_MOVE_ROW_Y))
        white_time, black_time = self._get_display_times()
        self.screen.blit(self.ui_font.render(f"White: {white_time}", True, COLOR_BLACK), (10, TIMER_ROW_Y))
        self.screen.blit(self.ui_font.render(f"Black: {black_time}", True, COLOR_BLACK), (200, TIMER_ROW_Y))
        player_color = self.game.get_current_player().color.title()
        status_text = f"{player_color}'s Turn | {self.game.game_state.title()}"
        if self.pending_promotion: status_text = "Promote pawn: Press Q, R, B, or N"
        if self.ai_is_thinking: 
            current_ai_type = self.white_player_type if self.game.get_current_player().color == 'white' else self.black_player_type
            status_text = f"{current_ai_type.title()} is thinking..."
        self.screen.blit(self.ui_font.render(status_text, True, COLOR_BLACK), (10, STATUS_ROW_Y))
        for button in BUTTONS:
            rect = pygame.Rect(button['x'], BUTTON_ROW_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
            color = COLOR_BUTTON_HOVER if self.hovered_button == button['name'] else COLOR_BUTTON
            pygame.draw.rect(self.screen, color, rect)
            text_surf = self.ui_font.render(button['name'], True, COLOR_BLACK)
            self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def _parse_ai_move(self, move_str):
        try:
            if len(move_str) >= 4:
                start_col = ord(move_str[0]) - ord('a'); start_row = 8 - int(move_str[1])
                end_col = ord(move_str[2]) - ord('a'); end_row = 8 - int(move_str[3])
                return ((start_row, start_col), (end_row, end_col))
        except (ValueError, IndexError): pass
        print(f"ERROR: Could not parse AI move string: '{move_str}'")
        return None, None

    def _get_button_at(self, pos):
        for button in BUTTONS:
            rect = pygame.Rect(button['x'], BUTTON_ROW_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
            if rect.collidepoint(pos): return button
        return None

    def _get_display_times(self):
        w_time = self.game.white_turn_time; b_time = self.game.black_turn_time
        elapsed = time.time() - self.game.turn_start_time
        if self.game.get_current_player().is_player1: w_time += elapsed
        else: b_time += elapsed
        format_time = lambda t: f"{int(t // 60):02d}:{int(t % 60):02d}"
        return format_time(w_time), format_time(b_time)

    def _reset_ui_state(self): self.selected_square = None; self.legal_moves = []
    def _reset_game_state(self): self.game = Game(); self._reset_ui_state()
    def _undo_move(self):
        # If it's human vs AI, undo two moves (one for each player)
        is_h_vs_ai = (self.white_player is None and self.black_player is not None) or \
                     (self.white_player is not None and self.black_player is None)
        
        self.game.undo_last_move()
        if is_h_vs_ai:
            self.game.undo_last_move()
        self._reset_ui_state()
