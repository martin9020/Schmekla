"""
Schmekla - Main Entry Point

This is the main entry point for the Schmekla application.
Run with: python -m src.main
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from loguru import logger

from src.utils.logger import setup_logging
from src.utils.config import Config


def main():
    """Main entry point for Schmekla application."""

    # Setup logging
    setup_logging()
    logger.info("Starting Schmekla v0.1.0")

    # Load configuration
    config = Config.load()
    logger.debug(f"Configuration loaded: {config}")

    try:
        # Import Qt after logging is set up
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt

        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Schmekla")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("Your Company")

        # Import and create main window
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        logger.info("Application window created successfully")

        # Run event loop
        exit_code = app.exec()

        logger.info(f"Application exiting with code {exit_code}")
        return exit_code

    except ImportError as e:
        logger.error(f"Failed to import required module: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
