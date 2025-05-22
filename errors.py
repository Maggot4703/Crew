from typing import Type, Callable, Any, Optional
import functools
import logging
from tkinter import messagebox

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)

class DatabaseError(AppError):
    """Database operation errors"""
    pass

class FileOperationError(AppError):
    """File operation errors"""
    pass

class ValidationError(AppError):
    """Data validation errors"""
    pass

class ConfigError(AppError):
    """Configuration errors"""
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