
import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class NormalizationConfig:
    
    normalize_ips: bool = True
    normalize_ports: bool = True
    normalize_timestamps: bool = True
    normalize_uuids: bool = True
    normalize_hashes: bool = True
    normalize_file_paths: bool = True
    normalize_session_ids: bool = True
    normalize_numeric_ids: bool = True
    normalize_hex_values: bool = True
    
    custom_patterns: Dict[str, str] = None
    
    enable_caching: bool = True
    cache_size: int = 1000
    
    def __post_init__(self):
        if self.custom_patterns is None:
            self.custom_patterns = {}

class LogNormalizer:
    
    def __init__(self, config: NormalizationConfig = None):
        self.config = config or NormalizationConfig()
        self._cache = {} if self.config.enable_caching else None
        self._template_cache = {} if self.config.enable_caching else None
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        
        self.ip_patterns = [
            re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
            re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
            re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b'),
        ]
        
        self.port_patterns = [
            re.compile(r':\d{4,5}\b'),
            re.compile(r'port\s+\d+', re.IGNORECASE),
            re.compile(r'listening\s+on\s+port\s+\d+', re.IGNORECASE),
        ]
        
        self.timestamp_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?'),
            re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}'),
            re.compile(r'\d{2}:\d{2}:\d{2}(?:\.\d+)?'),
            re.compile(r'\d{4}-\d{2}-\d{2}'),
        ]
        
        self.uuid_patterns = [
            re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
            re.compile(r'\b[0-9a-fA-F]{32}\b'),
        ]
        
        self.hash_patterns = [
            re.compile(r'\b[0-9a-fA-F]{32}\b'),
            re.compile(r'\b[0-9a-fA-F]{40}\b'),
            re.compile(r'\b[0-9a-fA-F]{64}\b'),
        ]
        
        self.file_path_patterns = [
            re.compile(r'/[a-zA-Z0-9/._-]+'),
            re.compile(r'[A-Za-z]:\\[A-Za-z0-9\\._-]+'),
            re.compile(r'\\\\[a-zA-Z0-9._-]+\\[a-zA-Z0-9/._-]+'),
        ]
        
        self.session_patterns = [
            re.compile(r'session[_-]?id[=:]\s*[a-zA-Z0-9_-]+', re.IGNORECASE),
            re.compile(r'sid[=:]\s*[a-zA-Z0-9_-]+', re.IGNORECASE),
        ]
        
        self.numeric_id_patterns = [
            re.compile(r'\bid\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bprocess\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bthread\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bjob\s+\d+\b', re.IGNORECASE),
        ]
        
        self.hex_patterns = [
            re.compile(r'0x[0-9a-fA-F]+'),
            re.compile(r'#[0-9a-fA-F]{6}'),
        ]
    
    def normalize(self, logline: str) -> str:
        
        if not isinstance(logline, str):
            return logline
        
        if self._cache is not None and logline in self._cache:
            return self._cache[logline]
        
        normalized = logline
        
        if self.config.normalize_ips:
            normalized = self._normalize_ips(normalized)
        
        if self.config.normalize_ports:
            normalized = self._normalize_ports(normalized)
        
        if self.config.normalize_timestamps:
            normalized = self._normalize_timestamps(normalized)
        
        if self.config.normalize_uuids:
            normalized = self._normalize_uuids(normalized)
        
        if self.config.normalize_hashes:
            normalized = self._normalize_hashes(normalized)
        
        if self.config.normalize_file_paths:
            normalized = self._normalize_file_paths(normalized)
        
        if self.config.normalize_session_ids:
            normalized = self._normalize_session_ids(normalized)
        
        if self.config.normalize_numeric_ids:
            normalized = self._normalize_numeric_ids(normalized)
        
        if self.config.normalize_hex_values:
            normalized = self._normalize_hex_values(normalized)
        
        normalized = self._apply_custom_patterns(normalized)
        
        if self._cache is not None:
            if len(self._cache) >= self.config.cache_size:

                self._cache.pop(next(iter(self._cache)))
            self._cache[logline] = normalized
        
        return normalized
    
    def normalize_batch(self, loglines: List[str]) -> List[str]:
        
        return [self.normalize(logline) for logline in loglines]
    
    def get_template_hash(self, logline: str) -> str:
        
        normalized = self.normalize(logline)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get_template_classification(self, logline: str) -> Optional[Any]:
        
        if self._template_cache is None:
            return None
        
        template_hash = self.get_template_hash(logline)
        return self._template_cache.get(template_hash)
    
    def cache_template_classification(self, logline: str, classification: Any):
        
        if self._template_cache is None:
            return
        
        template_hash = self.get_template_hash(logline)
        if len(self._template_cache) >= self.config.cache_size:

            self._template_cache.pop(next(iter(self._template_cache)))
        self._template_cache[template_hash] = classification
    
    def _normalize_ips(self, text: str) -> str:
        
        for pattern in self.ip_patterns:
            text = pattern.sub('<IP>', text)
        return text
    
    def _normalize_ports(self, text: str) -> str:
        
        for pattern in self.port_patterns:
            text = pattern.sub('<PORT>', text)
        return text
    
    def _normalize_timestamps(self, text: str) -> str:
        
        for pattern in self.timestamp_patterns:
            text = pattern.sub('<TIMESTAMP>', text)
        return text
    
    def _normalize_uuids(self, text: str) -> str:
        
        for pattern in self.uuid_patterns:
            text = pattern.sub('<UUID>', text)
        return text
    
    def _normalize_hashes(self, text: str) -> str:
        
        for pattern in self.hash_patterns:
            text = pattern.sub('<HASH>', text)
        return text
    
    def _normalize_file_paths(self, text: str) -> str:
        
        for pattern in self.file_path_patterns:
            text = pattern.sub('<PATH>', text)
        return text
    
    def _normalize_session_ids(self, text: str) -> str:
        
        for pattern in self.session_patterns:
            text = pattern.sub('<SESSION>', text)
        return text
    
    def _normalize_numeric_ids(self, text: str) -> str:
        
        for pattern in self.numeric_id_patterns:
            text = pattern.sub('<ID>', text)
        return text
    
    def _normalize_hex_values(self, text: str) -> str:
        
        for pattern in self.hex_patterns:
            text = pattern.sub('<HEX>', text)
        return text
    
    def _apply_custom_patterns(self, text: str) -> str:
        
        for pattern, replacement in self.config.custom_patterns.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def clear_cache(self):
        
        if self._cache is not None:
            self._cache.clear()
        if self._template_cache is not None:
            self._template_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        
        stats = {}
        if self._cache is not None:
            stats['normalization_cache_size'] = len(self._cache)
        if self._template_cache is not None:
            stats['template_cache_size'] = len(self._template_cache)
        return stats

_global_normalizer = None

def get_normalizer(config: NormalizationConfig = None) -> LogNormalizer:
    
    global _global_normalizer
    if _global_normalizer is None or config is not None:
        _global_normalizer = LogNormalizer(config)
    return _global_normalizer

def normalize_log(logline: str, config: NormalizationConfig = None) -> str:
    
    normalizer = get_normalizer(config)
    return normalizer.normalize(logline)

def normalize_logs(loglines: List[str], config: NormalizationConfig = None) -> List[str]:
    
    normalizer = get_normalizer(config)
    return normalizer.normalize_batch(loglines) 