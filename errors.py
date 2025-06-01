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

import logging
import traceback
import functools
from typing import Any, Callable, Dict, Optional, Type, Union, List

# Setup logger for this module (assuming a global logger or pass one in)
# If you have a central logging config, this might not be needed here.
# For now, let's create a logger for this module.
logger = logging.getLogger(__name__)

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

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


class DatabaseError(CrewManagerError):
    """Raised for database-related errors."""
    pass # Inherits __init__ and __str__ from CrewManagerError


class ConfigError(CrewManagerError):
    """Raised for configuration-related errors."""
    pass


class CacheError(CrewManagerError):
    """Raised for cache-related errors."""
    pass


class ScraperError(CrewManagerError):
    """Raised for web scraping errors."""
    pass


class FileOperationError(CrewManagerError):
    """Raised for file input/output errors."""
    pass


class GUIError(CrewManagerError):
    """Raised for GUI-related errors."""
    pass


class ValidationError(CrewManagerError):
    """Raised for data validation errors."""
    pass


class TravellerDataNotFoundError(ScraperError):
    """Raised when specific Traveller data is not found during scraping."""
    pass


# Error handling utilities


def format_error_message(error: Exception, include_traceback: bool = False) -> str:
    """Formats an error message, optionally including the traceback."""
    msg = f"{type(error).__name__}: {str(error)}"
    if include_traceback:
        tb_str = traceback.format_exc()
        msg += f"\nTraceback:\n{tb_str}"
    return msg


def handle_errors(
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True,
    # logger: Optional[logging.Logger] = None, # Use the module logger by default
    reraise: bool = False,
    custom_message: Optional[str] = None,
):
    """A decorator to handle exceptions in a function.
    
    Args:
        default_return: Value to return if an exception occurs.
        exceptions: A tuple of exception types to catch.
        log_errors: Whether to log the caught error.
        # logger: Specific logger instance to use. Defaults to module logger.
        reraise: Whether to re-raise the exception after handling.
        custom_message: A custom message to log or include in a new exception.
    """
    # local_logger = logger or module_logger # Use passed logger or default module logger

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    error_msg = custom_message or f"Error in {func.__name__}: {format_error_message(e)}"
                    # local_logger.error(error_msg, exc_info=True) # exc_info=True adds traceback to log
                    logger.error(error_msg, exc_info=True) # Use module logger
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


@handle_errors(default_return=None, log_errors=True)
def safe_execute(
    func: Callable,
    *args,
    # default_return: Any = None, # Handled by decorator
    # exceptions: tuple = (Exception,), # Handled by decorator
    # log_errors: bool = True, # Handled by decorator
    # logger: Optional[logging.Logger] = None, # Handled by decorator
    **kwargs,
) -> Any:
    """Safely executes a function, catching specified exceptions.
       The handle_errors decorator now manages the try-except block.
    """
    # The actual call is now directly here, decorator handles try/except
    return func(*args, **kwargs)


def create_error_context(**kwargs) -> Dict[str, Any]:
    """Creates a dictionary to be used as context for errors."""
    return kwargs


def convert_exception(
    source_exception: Exception,
    target_exception_class: Type[CrewManagerError],
    message: Optional[str] = None,
    **context,
) -> CrewManagerError:
    """Converts a given exception to a CrewManagerError (or subclass).

    Args:
        source_exception: The original exception.
        target_exception_class: The custom exception class to raise.
        message: Optional new message. If None, uses original exception's message.
        **context: Additional context for the new exception.

    Returns:
        An instance of target_exception_class.
    """
    new_message = message or str(source_exception)
    # Add original exception type and message to context for clarity
    error_context = create_error_context(
        original_exception_type=type(source_exception).__name__,
        original_message=str(source_exception),
        **context
    )
    # Log the conversion
    logger.debug(f"Converting {type(source_exception).__name__} to {target_exception_class.__name__} with message: '{new_message}'")
    return target_exception_class(new_message, context=error_context)


# Error reporting utilities


class ErrorReporter:
    """A simple error reporter class (can be expanded for integrations like Sentry)."""
    def __init__(self):
        self.error_log: List[Dict[str, Any]] = []
        # self.logger = logger or logging.getLogger(__name__ + ".ErrorReporter") # Use passed or new logger
        self.logger = logging.getLogger(__name__ + ".ErrorReporter")

    def report(self, error: Exception, context: Optional[Dict[str, Any]] = None, severity: str = "ERROR"):
        """Reports an error, e.g., logs it and could send to an external service."""
        report_details = {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context or (error.context if isinstance(error, CrewManagerError) else {}),
            "severity": severity,
            "traceback": traceback.format_exc() # Capture traceback string
        }
        self.error_log.append(report_details)
        log_message = f"Reported Error ({severity}): {report_details['message']} | Context: {report_details['context']}"
        
        if severity.upper() == "CRITICAL":
            self.logger.critical(log_message, exc_info=True)
        elif severity.upper() == "ERROR":
            self.logger.error(log_message, exc_info=True)
        elif severity.upper() == "WARNING":
            self.logger.warning(log_message, exc_info=True)
        else:
            self.logger.info(log_message) # Default to info for other severities

    def get_summary(self) -> Dict[str, Any]:
        """Returns a summary of reported errors."""
        summary = {
            "total_errors": len(self.error_log),
            "errors_by_type": {},
            "recent_errors": self.error_log[-5:] # Last 5 errors for quick view
        }
        for err_report in self.error_log:
            err_type = err_report["error_type"]
            summary["errors_by_type"][err_type] = summary["errors_by_type"].get(err_type, 0) + 1
        return summary


# Global error reporter instance
_global_error_reporter = ErrorReporter()


def report_error(
    error: Exception, context: Optional[Dict[str, Any]] = None, severity: str = "ERROR"
) -> None:
    """Global function to report an error using the global reporter."""
    _global_error_reporter.report(error, context, severity)


def get_error_summary() -> Dict[str, Any]:
    """Global function to get an error summary from the global reporter."""
    return _global_error_reporter.get_summary()


# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    # Configure basic logging for the example
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @handle_errors(default_return="Handled!", reraise=False, custom_message="Something went wrong in test_func")
    def test_func(x, y):
        if y == 0:
            raise ValueError("Division by zero in test_func")
        return x / y

    print(f"Test func (10, 2): {test_func(10, 2)}")
    print(f"Test func (10, 0): {test_func(10, 0)}") # Will be handled

    try:
        # Example of converting an exception
        num = int("abc")
    except ValueError as ve:
        app_error = convert_exception(ve, ValidationError, "Invalid number format provided.", input_value="abc")
        # logger.error(f"Converted error: {app_error}")
        report_error(app_error, severity="WARNING")
    
    try:
        # Example of a custom error
        raise DatabaseError("Failed to connect to the database.", context=create_error_context(db_host="localhost"))
    except DatabaseError as de:
        # logger.error(f"Caught DB error: {format_error_message(de, include_traceback=True)}")
        report_error(de, severity="CRITICAL")

    print("\nError Summary:")
    summary = get_error_summary()
    import json
    print(json.dumps(summary, indent=2))

    # Test safe_execute
    def risky_operation(value):
        if not isinstance(value, int):
            raise TypeError("Value must be an integer for risky_operation")
        return value * 2
    
    result_ok = safe_execute(risky_operation, 5)
    print(f"Safe execute OK: {result_ok}")
    result_fail = safe_execute(risky_operation, "text") # Will log error and return None
    print(f"Safe execute FAIL: {result_fail}")
