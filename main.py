# main.py
# Main entry point of the application

from gui import ChessGUI


def main():
    """Main entry point of the application."""
    game = ChessGUI()
    game.run()


if __name__ == "__main__":
    main()
