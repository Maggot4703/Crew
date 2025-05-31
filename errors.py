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

import functools
import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type, Union

"""
Defines custom exception classes for the application.

This module centralizes all custom exceptions, making error handling
more specific and manageable throughout the application.
"""


class CrewManagerError(Exception):
    """Base class for exceptions in the Crew Manager application.

    This base class provides common functionality for all application-specific
    exceptions including error context tracking and consistent formatting.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the base error.

        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            context: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = None

        # Capture the timestamp when error is created
        try:
            from datetime import datetime

            self.timestamp = datetime.now()
        except ImportError:
            pass

    def get_context(self) -> Dict[str, Any]:
        """Get error context information.

        Returns:
            dict: Context information about the error
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "context": self.context,
        }

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DatabaseError(CrewManagerError):
    """Raised for errors related to database operations.

    This exception is used for database connection issues, query failures,
    data corruption, and other database-related problems.
    """

    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        """Initialize database error.

        Args:
            message: Error message
            query: Optional SQL query that caused the error
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="DB_ERROR", **kwargs)
        if query:
            self.context["query"] = query


class ConfigError(CrewManagerError):
    """Raised for errors related to application configuration.

    This exception is used for configuration file issues, invalid settings,
    missing configuration values, and validation failures.
    """

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Optional configuration key that caused the error
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        if config_key:
            self.context["config_key"] = config_key


class CacheError(CrewManagerError):
    """Raised for errors related to caching operations.

    This exception is used for cache corruption, cache miss handling,
    serialization issues, and cache storage problems.
    """

    def __init__(self, message: str, cache_key: Optional[str] = None, **kwargs):
        """Initialize cache error.

        Args:
            message: Error message
            cache_key: Optional cache key that caused the error
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)
        if cache_key:
            self.context["cache_key"] = cache_key


class ScraperError(CrewManagerError):
    """Raised for errors encountered during web scraping.

    This exception is used for network issues, parsing failures,
    rate limiting, and authentication problems during scraping.
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        """Initialize scraper error.

        Args:
            message: Error message
            url: Optional URL that caused the error
            status_code: Optional HTTP status code
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="SCRAPER_ERROR", **kwargs)
        if url:
            self.context["url"] = url
        if status_code:
            self.context["status_code"] = status_code


class FileOperationError(CrewManagerError):
    """Raised for errors related to file operations (read, write, etc.).

    This exception is used for file permission issues, disk space problems,
    format errors, and general I/O failures.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """Initialize file operation error.

        Args:
            message: Error message
            file_path: Optional file path that caused the error
            operation: Optional operation type (read, write, delete, etc.)
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="FILE_ERROR", **kwargs)
        if file_path:
            self.context["file_path"] = file_path
        if operation:
            self.context["operation"] = operation


class GUIError(CrewManagerError):
    """Raised for errors specific to the GUI components or operations.

    This exception is used for widget initialization failures, layout problems,
    event handling issues, and GUI-specific validation errors.
    """

    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        """Initialize GUI error.

        Args:
            message: Error message
            component: Optional GUI component that caused the error
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="GUI_ERROR", **kwargs)
        if component:
            self.context["component"] = component


class ValidationError(CrewManagerError):
    """Raised for data validation errors.

    This exception is used for input validation failures, data format errors,
    constraint violations, and schema validation problems.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
            value: Optional value that failed validation
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        if field:
            self.context["field"] = field
        if value is not None:
            self.context["value"] = str(value)


class TravellerDataNotFoundError(ScraperError):
    """Raised when specific Traveller data cannot be found by the scraper.

    This is a specialized scraper error for Traveller RPG data retrieval.
    """

    def __init__(
        self, message="Traveller data not found", item_searched=None, **kwargs
    ):
        """
        Initialize the TravellerDataNotFoundError exception.

        Args:
            message (str): The error message.
            item_searched (str, optional): The specific item that was being searched for.
            **kwargs: Additional context passed to base class
        """
        super().__init__(message, error_code="TRAVELLER_NOT_FOUND", **kwargs)
        if item_searched:
            self.context["item_searched"] = item_searched

    def __str__(self):
        """Return a string representation of the exception."""
        if "item_searched" in self.context:
            return f"{self.message} (Item: {self.context['item_searched']})"
        return self.message


# Error handling utilities


def format_error_message(error: Exception, include_traceback: bool = False) -> str:
    """Format an error message for display or logging.

    Args:
        error: The exception to format
        include_traceback: Whether to include full traceback

    Returns:
        str: Formatted error message
    """
    if isinstance(error, CrewManagerError):
        message = f"Error [{error.error_code or 'UNKNOWN'}]: {error.message}"
        if error.context:
            context_str = ", ".join(
                f"{k}={v}" for k, v in error.context.items() if v is not None
            )
            if context_str:
                message += f" (Context: {context_str})"
    else:
        message = f"Error [{type(error).__name__}]: {str(error)}"

    if include_traceback:
        message += f"\n\nTraceback:\n{traceback.format_exc()}"

    return message


def handle_errors(
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    logger: Optional[logging.Logger] = None,
    reraise: bool = False,
):
    """Decorator for automatic error handling.

    Args:
        default_return: Default value to return on error
        exceptions: Tuple of exception types to catch
        log_errors: Whether to log caught errors
        logger: Logger instance to use (creates one if None)
        reraise: Whether to reraise the exception after handling

    Returns:
        Decorated function
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    error_msg = format_error_message(e, include_traceback=True)
                    logger.error(f"Error in {func.__name__}: {error_msg}")

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    logger: Optional[logging.Logger] = None,
    **kwargs,
) -> Any:
    """Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Default value to return on error
        exceptions: Tuple of exception types to catch
        log_errors: Whether to log caught errors
        logger: Logger instance to use
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default_return on error
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        return func(*args, **kwargs)
    except exceptions as e:
        if log_errors:
            error_msg = format_error_message(e)
            logger.error(f"Error executing {func.__name__}: {error_msg}")
        return default_return


def create_error_context(**kwargs) -> Dict[str, Any]:
    """Create an error context dictionary.

    Args:
        **kwargs: Key-value pairs for the context

    Returns:
        dict: Error context dictionary
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def convert_exception(
    source_exception: Exception,
    target_exception_class: Type[CrewManagerError],
    message: Optional[str] = None,
    **context,
) -> CrewManagerError:
    """Convert a standard exception to a CrewManager exception.

    Args:
        source_exception: Original exception
        target_exception_class: Target exception class
        message: Optional custom message (uses original if None)
        **context: Additional context for the new exception

    Returns:
        CrewManagerError: Converted exception
    """
    if message is None:
        message = str(source_exception)

    # Add original exception info to context
    context.update(
        {
            "original_exception": type(source_exception).__name__,
            "original_message": str(source_exception),
        }
    )

    return target_exception_class(message, context=context)


# Error reporting utilities


class ErrorReporter:
    """Centralized error reporting and logging."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error reporter.

        Args:
            logger: Logger instance to use
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_count = 0
        self.error_history = []
        self.max_history = 100

    def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR",
    ) -> None:
        """Report an error with context.

        Args:
            error: Exception to report
            context: Additional context information
            severity: Error severity level
        """
        self.error_count += 1

        # Create error record
        error_record = {
            "error": error,
            "context": context or {},
            "severity": severity,
            "count": self.error_count,
        }

        # Add to history
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

        # Log the error
        error_msg = format_error_message(error)
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            error_msg += f" | Context: {context_str}"

        if severity == "CRITICAL":
            self.logger.critical(error_msg)
        elif severity == "ERROR":
            self.logger.error(error_msg)
        elif severity == "WARNING":
            self.logger.warning(error_msg)
        else:
            self.logger.info(error_msg)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of reported errors.

        Returns:
            dict: Error summary with counts and recent errors
        """
        recent_errors = self.error_history[-10:]  # Last 10 errors

        return {
            "total_errors": self.error_count,
            "history_length": len(self.error_history),
            "recent_errors": [
                {
                    "type": type(record["error"]).__name__,
                    "message": str(record["error"]),
                    "severity": record["severity"],
                }
                for record in recent_errors
            ],
        }


# Global error reporter instance
_global_error_reporter = ErrorReporter()


def report_error(
    error: Exception, context: Optional[Dict[str, Any]] = None, severity: str = "ERROR"
) -> None:
    """Report an error using the global error reporter.

    Args:
        error: Exception to report
        context: Additional context information
        severity: Error severity level
    """
    _global_error_reporter.report_error(error, context, severity)


def get_error_summary() -> Dict[str, Any]:
    """Get error summary from global error reporter.

    Returns:
        dict: Error summary
    """
    return _global_error_reporter.get_error_summary()
