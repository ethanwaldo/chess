# gui.py
# Graphical user interface using Pygame

import pygame
import sys
import time
from config import *
from engine import Game, Pawn


class ChessGUI:
    """Manages the graphical user interface using Pygame."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (WINDOW_SIZE, WINDOW_SIZE + UI_HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.font = pygame.font.Font(None, 64)
        self.ui_font = pygame.font.Font(None, UI_FONT_SIZE)
        self.game = Game()
        self.selected_square = None
        self.legal_moves = []
        self.pending_promotion = None
        self.hovered_button = None

    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_input(event)

            self.draw()
            pygame.display.flip()
            clock.tick(60)

    def handle_input(self, event):
        """Handle all user input events."""
        if self.pending_promotion:
            self.handle_promotion_input(event)
            return

        if event.type == pygame.MOUSEMOTION:
            self.hovered_button = self._get_button_at(pygame.mouse.get_pos())

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            button = self._get_button_at(pos)
            if button:
                self.handle_button_click(button['name'])
            else:
                self.handle_square_click(pos)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u: self._undo_move()
            if event.key == pygame.K_r: self._reset_game_state()

    def handle_square_click(self, pos):
        """Handle clicking on a board square."""
        coords = (pos[1] // SQUARE_SIZE, pos[0] // SQUARE_SIZE)
        if coords[0] >= BOARD_DIMENSION: return  # Click was in UI panel

        if self.selected_square:
            moving_piece = self.game.get_piece_at(self.selected_square)
            is_promotion = isinstance(moving_piece,
                                      Pawn) and coords[0] in (0, 7)

            if coords in self.legal_moves:
                if is_promotion:
                    self.pending_promotion = (self.selected_square, coords)
                else:
                    if self.game.make_move(self.selected_square, coords):
                        self._reset_ui_state()
            else:
                self._reset_ui_state()

        piece = self.game.get_piece_at(coords)
        if piece and piece.is_player1 == self.game.get_current_player(
        ).is_player1:
            self.selected_square = coords
            self.legal_moves = self.game.get_legal_moves_for_piece(coords)
        else:
            self._reset_ui_state()

    def handle_button_click(self, button_name):
        """Handle clicking on a UI button."""
        if button_name == 'New Game': self._reset_game_state()
        elif button_name == 'Resign': self.game.resign()
        elif button_name == 'Offer Draw': self.game.offer_draw()
        elif button_name == 'Undo': self._undo_move()

    def handle_promotion_input(self, event):
        """Handle keyboard input for pawn promotion."""
        if event.type != pygame.KEYDOWN: return

        key_map = {
            pygame.K_q: 'Q',
            pygame.K_r: 'R',
            pygame.K_b: 'B',
            pygame.K_n: 'N'
        }
        if event.key in key_map:
            start_coords, end_coords = self.pending_promotion
            if self.game.make_move(start_coords, end_coords,
                                   key_map[event.key]):
                self._reset_ui_state()
            self.pending_promotion = None

    def draw(self):
        """Draw the complete game state."""
        self.screen.fill(COLOR_WHITE)
        self.draw_board()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_ui()

    def draw_board(self):
        for r in range(BOARD_DIMENSION):
            for c in range(BOARD_DIMENSION):
                color = COLOR_LIGHT_SQUARE if (
                    r + c) % 2 == 0 else COLOR_DARK_SQUARE
                pygame.draw.rect(self.screen, color,
                                 (c * SQUARE_SIZE, r * SQUARE_SIZE,
                                  SQUARE_SIZE, SQUARE_SIZE))

    def draw_highlights(self):
        if not self.selected_square: return
        # Highlight selected square
        r, c = self.selected_square
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(COLOR_HIGHLIGHT)
        self.screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))
        # Highlight legal moves
        s.fill(COLOR_LEGAL_MOVE)
        for r_m, c_m in self.legal_moves:
            self.screen.blit(s, (c_m * SQUARE_SIZE, r_m * SQUARE_SIZE))

    def draw_pieces(self):
        for r in range(BOARD_DIMENSION):
            for c in range(BOARD_DIMENSION):
                piece = self.game.board[r][c]
                if piece:
                    symbol = PIECE_SYMBOLS[piece.color][piece.name]
                    color = COLOR_WHITE if symbol.isupper() else COLOR_BLACK
                    text_surf = self.font.render(symbol, True, color)
                    text_rect = text_surf.get_rect(
                        center=(c * SQUARE_SIZE + SQUARE_SIZE // 2,
                                r * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text_surf, text_rect)

    def draw_ui(self):
        """Draws the entire UI panel using constants from config."""
        # Captured pieces
        white_cap_str = "".join(PIECE_SYMBOLS['black'][p.name]
                                for p in self.game.white_captured)
        black_cap_str = "".join(PIECE_SYMBOLS['white'][p.name]
                                for p in self.game.black_captured)
        self.screen.blit(
            self.ui_font.render(f"White captured: {white_cap_str}", True,
                                COLOR_BLACK), (10, CAPTURED_ROW_Y))
        self.screen.blit(
            self.ui_font.render(f"Black captured: {black_cap_str}", True,
                                COLOR_BLACK),
            (10, CAPTURED_ROW_Y + UI_LINE_HEIGHT))

        # Last move
        last_move_str = f"Last Move: {self.game.move_history[-1].to_notation()}" if self.game.move_history else "Last Move: None"
        self.screen.blit(self.ui_font.render(last_move_str, True, COLOR_BLACK),
                         (10, LAST_MOVE_ROW_Y))

        # Timers
        white_time, black_time = self._get_display_times()
        self.screen.blit(
            self.ui_font.render(f"White: {white_time}", True, COLOR_BLACK),
            (10, TIMER_ROW_Y))
        self.screen.blit(
            self.ui_font.render(f"Black: {black_time}", True, COLOR_BLACK),
            (200, TIMER_ROW_Y))

        # Game status
        player_color = self.game.get_current_player().color.title()
        status_text = f"{player_color}'s Turn | {self.game.game_state.title()}"
        if self.pending_promotion:
            status_text = "Promote pawn: Press Q, R, B, or N"
        self.screen.blit(self.ui_font.render(status_text, True, COLOR_BLACK),
                         (10, STATUS_ROW_Y))

        # Buttons
        for button in BUTTONS:
            rect = pygame.Rect(button['x'], BUTTON_ROW_Y, BUTTON_WIDTH,
                               BUTTON_HEIGHT)
            color = COLOR_BUTTON_HOVER if self.hovered_button == button[
                'name'] else COLOR_BUTTON
            pygame.draw.rect(self.screen, color, rect)
            text_surf = self.ui_font.render(button['name'], True, COLOR_BLACK)
            self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def _get_button_at(self, pos):
        """Return the button name if the position is over a button, otherwise None."""
        for button in BUTTONS:
            rect = pygame.Rect(button['x'], BUTTON_ROW_Y, BUTTON_WIDTH,
                               BUTTON_HEIGHT)
            if rect.collidepoint(pos):
                return button
        return None

    def _get_display_times(self):
        """Calculate and format timers for display."""
        w_time = self.game.white_turn_time
        b_time = self.game.black_turn_time
        elapsed = time.time() - self.game.turn_start_time
        if self.game.get_current_player().is_player1: w_time += elapsed
        else: b_time += elapsed

        format_time = lambda t: f"{int(t // 60):02d}:{int(t % 60):02d}"
        return format_time(w_time), format_time(b_time)

    def _reset_ui_state(self):
        """Resets selections and moves after an action."""
        self.selected_square = None
        self.legal_moves = []

    def _reset_game_state(self):
        """Resets the entire game to a new state."""
        self.game = Game()
        self._reset_ui_state()

    def _undo_move(self):
        """Undoes the last move and resets the UI."""
        self.game.undo_last_move()
        self._reset_ui_state()
