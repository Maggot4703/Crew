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

from typing import Type, Callable, Any, Optional
import functools
import logging
from tkinter import messagebox

class AppError(Exception):
    """
    Base exception class for application errors.
    
    This is the parent class for all custom exceptions in the Crew Manager
    application. It provides consistent error handling with optional details.
    
    Attributes:
        message (str): The main error message
        details (str, optional): Additional error details or context
        
    Example:
        raise AppError("Operation failed", "Database connection timeout")
    """
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)

class DatabaseError(AppError):
    """
    Database operation errors.
    
    Raised when database operations fail, including connection issues,
    query execution errors, and data integrity problems.
    
    Example:
        raise DatabaseError("Failed to save data", "Foreign key constraint violation")
    """
    pass

class FileOperationError(AppError):
    """
    File operation errors.
    
    Raised when file I/O operations fail, including reading, writing,
    file not found, and permission errors.
    
    Example:
        raise FileOperationError("Cannot read file", "Permission denied")
    """
    pass

class ValidationError(AppError):
    """
    Data validation errors.
    
    Raised when data validation fails, including format validation,
    required field checks, and business rule violations.
    
    Example:
        raise ValidationError("Invalid email format", "Email must contain @ symbol")
    """
    pass

class ConfigError(AppError):
    """
    Configuration errors.
    
    Raised when configuration loading or validation fails, including
    missing config files, invalid settings, and environment issues.
    
    Example:
        raise ConfigError("Missing config file", "config.json not found")
    """
    pass

def format_error_message(error: AppError) -> str:
    """Format error message with details if available"""
    if error.details:
        return f"{error.message}\nDetails: {error.details}"
    return error.message

def handle_errors(error_types: tuple[Type[Exception], ...] = (Exception,),
                 show_message: bool = True):
    """Decorator for error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                logging.error(f"Error in {func.__name__}: {e}")
                if show_message:
                    messagebox.showerror("Error", str(e))
                raise
        return wrapper
    return decorator