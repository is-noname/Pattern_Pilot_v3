# utils/logger.py
import logging
import os
import sys
from datetime import datetime

class PatternPilotLogger:
    _instance = None  # Singleton-Pattern
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PatternPilotLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Logger einrichten mit File- und Console-Handler"""
        self.logger = logging.getLogger("PatternPilot")
        self.logger.setLevel(logging.DEBUG)
        
        # Formatierung festlegen
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Log-Verzeichnis erstellen falls nicht vorhanden
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # File Handler (tägliche Logs)
        log_file = os.path.join(log_dir, f"pattern_pilot_{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console zeigt nur INFO aufwärts
        console_handler.setFormatter(formatter)
        
        # Handler hinzufügen
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    # Convenience-Methoden
    def debug(self, message): self.logger.debug(message)
    def info(self, message): self.logger.info(message) 
    def warning(self, message): self.logger.warning(message)
    def error(self, message): self.logger.error(message)
    def critical(self, message): self.logger.critical(message)

    # Loglevel je nach Umgebung
    def set_log_level(self, level):
        """Log-Level für alle Handler anpassen"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    # Kontext-Info für API/Cache Logs
    def api_debug(self, api_name, message): 
        self.logger.debug(f"[API:{api_name}] {message}")
    
    def api_error(self, api_name, message):
        self.logger.error(f"[API:{api_name}] {message}")
    
    def cache_info(self, message):
        self.logger.info(f"[CACHE] {message}")

# Global instance für einfachen Import
logger = PatternPilotLogger()