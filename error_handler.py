#!/usr/bin/python3
"""
Error Handling Utilities for Crew Manager
=========================================

Comprehensive error handling, logging, and recovery utilities.

Author: Enhanced Crew Manager
Date: May 2025
Version: 1.0
"""

import functools
import logging
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


class CrewManagerError(Exception):
    """Base exception class for Crew Manager specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "CREW_ERROR"
        self.details = details or {}
        self.timestamp = time.time()


class DataProcessingError(CrewManagerError):
    """Raised when data processing operations fail."""

    pass


class FileOperationError(CrewManagerError):
    """Raised when file operations fail."""

    pass


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    Safely execute a function with comprehensive error handling.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            error_prefix = error_message or f"Error executing {func.__name__}"
            logger.error(f"{error_prefix}: {str(e)}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
        return default_return


def handle_errors(
    default_return: Any = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
    error_types: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator for automatic error handling with logging.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_types and not isinstance(e, error_types):
                    raise

                logger.log(log_level, f"Error in {func.__name__}: {str(e)}")
                logger.debug(
                    f"Full traceback for {func.__name__}: {traceback.format_exc()}"
                )

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


@contextmanager
def safe_file_operation(file_path: Union[str, Path], operation: str = "operation"):
    """
    Context manager for safe file operations with proper error handling.
    """
    try:
        path_obj = Path(file_path)
        logger.debug(f"Starting {operation} on {path_obj}")
        yield path_obj
        logger.debug(f"Completed {operation} on {path_obj}")
    except OSError as e:
        error_msg = f"File {operation} failed for {file_path}: {str(e)}"
        logger.error(error_msg)
        raise FileOperationError(
            error_msg,
            error_code="FILE_OP_ERROR",
            details={"file_path": str(file_path), "operation": operation},
        )


def validate_data(
    data: Any,
    validators: List[Callable[[Any], bool]],
    error_message: str = "Data validation failed",
) -> bool:
    """
    Validate data using a list of validator functions.
    """
    for i, validator in enumerate(validators):
        try:
            if not validator(data):
                logger.error(f"{error_message} (validator {i + 1} failed)")
                return False
        except Exception as e:
            logger.error(
                f"{error_message} (validator {i + 1} raised exception: {str(e)})"
            )
            return False

    return True


# Common validator functions
def is_not_none(value: Any) -> bool:
    """Check if value is not None."""
    return value is not None


def is_file_exists(path: Union[str, Path]) -> bool:
    """Check if file exists."""
    return Path(path).exists()


def is_csv_file(path: Union[str, Path]) -> bool:
    """Check if file has CSV extension."""
    return Path(path).suffix.lower() == ".csv"


def is_excel_file(path: Union[str, Path]) -> bool:
    """Check if file has Excel extension."""
    return Path(path).suffix.lower() in [".xlsx", ".xls"]


# Pre-defined validator sets
BASIC_FILE_VALIDATORS = [is_not_none, is_file_exists]
CSV_FILE_VALIDATORS = BASIC_FILE_VALIDATORS + [is_csv_file]
EXCEL_FILE_VALIDATORS = BASIC_FILE_VALIDATORS + [is_excel_file]
