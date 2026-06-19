# from config import settings
# import os
# import logging
# from concurrent_log_handler import ConcurrentRotatingFileHandler
# from contextvars import ContextVar
#
# os.makedirs(settings.SERVER_LOG_DIR,exist_ok=True)
#
# SERVER_LOG_FILE = os.path.join(settings.SERVER_LOG_DIR, "server.log")
#
#
# # Module-level context variable — holds current request's logger
# _request_logger_var: ContextVar[logging.Logger] = ContextVar('request_logger', default=None)
#
# def set_request_logger(logger: logging.Logger):
#     """Call this at the start of each request thread."""
#     _request_logger_var.set(logger)
#
# def get_server_logger():
#
#     logger = logging.getLogger("server_logger")
#     logger.setLevel(logging.INFO)
#
#     logger.propagate = False
#
#     # Prevent duplicate handlers
#     if logger.handlers:
#         return logger
#
#     formatter = logging.Formatter(
#         "%(asctime)s - %(levelname)s - %(name)s - line:%(lineno)d - %(message)s"
#     )
#
#     # SAFE handler (replace this line)
#     file_handler = ConcurrentRotatingFileHandler(
#         SERVER_LOG_FILE,
#         maxBytes=5 * 1024 * 1024,
#         backupCount=5
#     )
#     file_handler.setFormatter(formatter)
#
#     console_handler = logging.StreamHandler()
#     console_handler.setFormatter(formatter)
#
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
#
#     return logger
#
# # Add this to logging_config.py
#
# def get_request_logger(ref_id: str):
#     """
#     Creates a per-request log file: DWG_PROCESS_LOG_DIR/<ref_id>.log
#     Each request gets its own isolated logger and file.
#     """
#     os.makedirs(settings.DWG_PROCESS_LOG_DIR, exist_ok=True)
#
#     log_path = os.path.join(settings.DWG_PROCESS_LOG_DIR, f"{ref_id}.log")
#
#     # Use ref_id as logger name so each request gets its own instance
#     logger = logging.getLogger(f"request.{ref_id}")
#     logger.setLevel(logging.INFO)
#     logger.propagate = False  # don't bubble up to root/server logger
#
#     if logger.handlers:
#         return logger
#
#     formatter = logging.Formatter(
#         "%(asctime)s - %(levelname)s - line:%(lineno)d - %(message)s"
#     )
#
#     file_handler = logging.FileHandler(log_path, encoding="utf-8")
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
#
#     return logger
#
#
# def close_request_logger(ref_id: str):
#     """
#     Call this after request processing is done to release the file handle.
#     """
#     logger = logging.getLogger(f"request.{ref_id}")
#     for handler in logger.handlers[:]:
#         handler.close()
#         logger.removeHandler(handler)

from contextvars import ContextVar
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os
from config import settings
# Module-level context variable — holds current request's logger
_request_logger_var: ContextVar[logging.Logger] = ContextVar('request_logger', default=None)

os.makedirs(settings.SERVER_LOG_DIR,exist_ok=True)

SERVER_LOG_FILE = os.path.join(settings.SERVER_LOG_DIR, "server.log")

def set_request_logger(logger: logging.Logger):
    """Call this at the start of each request thread."""
    _request_logger_var.set(logger)

def get_server_logger():
    """
    Returns per-request logger if inside a request context,
    otherwise falls back to the global server logger.
    """
    req_logger = _request_logger_var.get()
    if req_logger is not None:
        return req_logger

    # fallback to global server logger (existing code below unchanged)
    logger = logging.getLogger("server_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - line:%(lineno)d - %(message)s"
    )
    file_handler = ConcurrentRotatingFileHandler(
        SERVER_LOG_FILE, maxBytes=3 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# def get_request_logger(ref_id: str):
#     os.makedirs(settings.DWG_PROCESS_LOG_DIR, exist_ok=True)
#     log_path = os.path.join(settings.DWG_PROCESS_LOG_DIR, f"{ref_id}.log")
#
#     logger = logging.getLogger(f"request.{ref_id}")
#     logger.setLevel(logging.INFO)
#     logger.propagate = False
#
#     if logger.handlers:
#         return logger
#
#     formatter = logging.Formatter(
#         "%(asctime)s - %(levelname)s - line:%(lineno)d - %(message)s"
#     )
#     file_handler = logging.FileHandler(log_path, encoding="utf-8")
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
#
#     return logger

def get_request_logger(ref_id: str):
    os.makedirs(settings.DWG_PROCESS_LOG_DIR, exist_ok=True)
    log_path = os.path.join(settings.DWG_PROCESS_LOG_DIR, f"{ref_id}.log")

    logger = logging.getLogger(f"request.{ref_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    # ref_id added to every log line
    formatter = logging.Formatter(
        f"%(asctime)s - %(levelname)s - [{ref_id}] - %(filename)s:%(lineno)d - %(message)s"
    )

    # File handler — writes to ref_id.log
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Console handler — shows in terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def close_request_logger(ref_id: str):
    logger = logging.getLogger(f"request.{ref_id}")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def get_current_logger():
    """
    Returns the current request logger if inside a request context,
    otherwise falls back to the global server logger.
    Use this anywhere in the codebase to write to the active request's log file.
    """
    req = _request_logger_var.get()
    return req if req is not None else get_server_logger()