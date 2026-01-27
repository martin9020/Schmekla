"""
Launcher for Domino Printing Canopy Project

This script builds the Domino Printing canopy model and launches
the Schmekla viewer to visualize it.

Run with: python launch_domino_printing.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger


def main():
    """Build the model and launch the viewer."""

    # Setup logging
    from src.utils.logger import setup_logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("Domino Printing Canopy - Model Builder & Viewer")
    logger.info("Job Number: 704216")
    logger.info("=" * 60)

    # Build the model
    logger.info("\nBuilding structural model...")
    from examples.domino_printing_canopy import build_domino_printing_canopy
    model = build_domino_printing_canopy()

    # Launch the UI
    logger.info("\nLaunching viewer...")

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt

        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Schmekla - Domino Printing Canopy")
        app.setApplicationVersion("0.1.0")

        # Create main window with our model
        from src.ui.main_window import MainWindow

        window = MainWindow()

        # Replace the default model with our built model
        window.model = model

        # Connect the model signals to UI
        window._connect_signals()

        # Connect the model to viewport
        if window.viewport:
            window.viewport.model = model
            window.viewport._connect_model_signals()

        # Update the window title
        window.setWindowTitle(f"Schmekla - {model.name}")

        # Rebuild the model tree with all elements
        window._rebuild_tree()

        # Update display with all elements
        if window.viewport:
            window.viewport.update_display()

        # Show the window
        window.show()

        logger.info("Application ready - displaying model")
        logger.info(f"Total elements: {model.element_count}")

        # Run event loop
        exit_code = app.exec()

        logger.info(f"Application exiting with code {exit_code}")
        return exit_code

    except ImportError as e:
        logger.error(f"Failed to import required module: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
