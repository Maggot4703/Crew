#!/usr/bin/env python3
"""
Error Handling Module for Crew Manager

This module provides comprehensive error handling functionality including:
- Custom exception classes for different error types
- Error formatting utilities
- Decorators for automatic error handling
- Integration with GUI error display

Classes:
    AppError: Base exception class for application errors
    DatabaseError: Database operation specific errors
    FileOperationError: File I/O related errors
    ValidationError: Data validation errors
    ConfigError: Configuration management errors

Functions:
    format_error_message: Format error messages with optional details
    handle_errors: Decorator for automatic error handling

Author: Crew Manager Development Team
Version: 1.0.0
Date: 2024
"""

"""
Defines custom exception classes for the application.

This module centralizes all custom exceptions, making error handling
more specific and manageable throughout the application.
"""


class CrewManagerError(Exception):
    """Base class for exceptions in the Crew Manager application."""

    pass


class DatabaseError(CrewManagerError):
    """Raised for errors related to database operations."""

    pass


class ConfigError(CrewManagerError):
    """Raised for errors related to application configuration."""

    pass


class CacheError(CrewManagerError):
    """Raised for errors related to caching operations."""

    pass


class ScraperError(CrewManagerError):
    """Raised for errors encountered during web scraping."""

    pass


class FileOperationError(CrewManagerError):
    """Raised for errors related to file operations (read, write, etc.)."""

    pass


class GUIError(CrewManagerError):
    """Raised for errors specific to the GUI components or operations."""

    pass


# Example of a more specific error:
class TravellerDataNotFoundError(ScraperError):
    """Raised when specific Traveller data cannot be found by the scraper."""

    def __init__(self, message="Traveller data not found", item_searched=None):
        """
        Initialize the TravellerDataNotFoundError exception.

        Args:
            message (str): The error message.
            item_searched (str, optional): The specific item that was being searched for.
        """
        super().__init__(message)
        self.item_searched = item_searched

    def __str__(self):
        """Return a string representation of the exception."""
        if self.item_searched:
            return f"{super().__str__()} (Item: {self.item_searched})"
        return super().__str__()
