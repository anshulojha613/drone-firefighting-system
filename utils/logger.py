"""
Centralized logging utility for DFS
Provides consistent logging across all modules with configurable levels
"""
import logging
import sys
import threading
from pathlib import Path
from typing import Optional


class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    def filter(self, record):
        # Get context from thread-local storage
        context = getattr(_context, 'data', {})
        record.task_id = context.get('task_id', '')
        record.drone_id = context.get('drone_id', '')
        record.module = context.get('module', '')
        return True


# Thread-local storage for context
_context = threading.local()


class DFSLogger:
    """Centralized logger for Drone Firefighting System"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DFSLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('DFS')
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False
            
            if not self.logger.handlers:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                
                # Add context filter
                context_filter = ContextFilter()
                console_handler.addFilter(context_filter)
                
                # Format with context
                formatter = logging.Formatter(
                    '[%(levelname)s]%(task_id)s%(drone_id)s%(module)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
            
            DFSLogger._initialized = True
    
    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
    
    def add_file_handler(self, log_file: str, level: str = 'INFO'):
        """Add file handler for logging to file"""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        file_handler.setLevel(level_map.get(level.upper(), logging.INFO))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def set_context(self, task_id: str = None, drone_id: str = None, module: str = None):
        """Set logging context for current thread"""
        if not hasattr(_context, 'data'):
            _context.data = {}
        
        if task_id is not None:
            _context.data['task_id'] = f"[{task_id}]" if task_id else ''
        if drone_id is not None:
            _context.data['drone_id'] = f"[{drone_id}]" if drone_id else ''
        if module is not None:
            _context.data['module'] = f"[{module}]" if module else ''
    
    def clear_context(self):
        """Clear logging context for current thread"""
        if hasattr(_context, 'data'):
            _context.data = {}
    
    def debug(self, msg: str, task_id: str = None, drone_id: str = None, module: str = None):
        """Log debug message"""
        if task_id or drone_id or module:
            self.set_context(task_id, drone_id, module)
        self.logger.debug(msg)
    
    def info(self, msg: str, task_id: str = None, drone_id: str = None, module: str = None):
        """Log info message"""
        if task_id or drone_id or module:
            self.set_context(task_id, drone_id, module)
        self.logger.info(msg)
    
    def warning(self, msg: str, task_id: str = None, drone_id: str = None, module: str = None):
        """Log warning message"""
        if task_id or drone_id or module:
            self.set_context(task_id, drone_id, module)
        self.logger.warning(msg)
    
    def error(self, msg: str, task_id: str = None, drone_id: str = None, module: str = None):
        """Log error message"""
        if task_id or drone_id or module:
            self.set_context(task_id, drone_id, module)
        self.logger.error(msg)
    
    def critical(self, msg: str, task_id: str = None, drone_id: str = None, module: str = None):
        """Log critical message"""
        if task_id or drone_id or module:
            self.set_context(task_id, drone_id, module)
        self.logger.critical(msg)


def get_logger() -> DFSLogger:
    """Get singleton logger instance"""
    return DFSLogger()


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """
    Setup logging config
    """
    logger = get_logger()
    logger.set_level(level)
    
    if log_file:
        logger.add_file_handler(log_file, level)
    
    return logger
