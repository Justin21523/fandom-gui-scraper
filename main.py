#!/usr/bin/env python3
# main.py
"""
Main entry point for Fandom Scraper GUI application.

This script initializes and starts the PyQt5 application with proper
error handling, logging setup, and resource management.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from gui.main_window import MainWindow
from utils.logger import setup_logging, get_logger


def setup_application() -> QApplication:
    """
    Set up and configure the QApplication.

    Returns:
        Configured QApplication instance
    """
    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Fandom Scraper")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Fandom Scraper Team")
    app.setOrganizationDomain("fandom-scraper.local")

    # Set application icon (if available)
    icon_path = project_root / "gui" / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Configure application-wide font
    font = QFont("Arial", 9)
    app.setFont(font)

    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    return app


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for unhandled exceptions.

    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to exit
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = get_logger("ExceptionHandler")
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    # Show error dialog to user
    QMessageBox.critical(
        None,
        "Critical Error",
        f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
        "Please check the log files for more details.",
    )


def main():
    """Main application entry point."""
    try:
        # Set up logging
        setup_logging()
        logger = get_logger(__name__)

        logger.info("Starting Fandom Scraper GUI application")

        # Set up global exception handler
        sys.excepthook = handle_exception

        # Create and configure application
        app = setup_application()

        # Create main window
        main_window = MainWindow()
        main_window.show()

        # Center window on screen
        screen = app.desktop().screenGeometry()
        window = main_window.geometry()
        main_window.move(
            (screen.width() - window.width()) // 2,
            (screen.height() - window.height()) // 2,
        )

        logger.info("Main window displayed, starting event loop")

        # Start application event loop
        exit_code = app.exec_()

        logger.info(f"Application exiting with code {exit_code}")
        return exit_code

    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    main()
