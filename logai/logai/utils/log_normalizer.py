#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class NormalizationConfig:
    """Configuration for log normalization."""
    
    # Enable/disable specific normalizations
    normalize_ips: bool = True
    normalize_ports: bool = True
    normalize_timestamps: bool = True
    normalize_uuids: bool = True
    normalize_hashes: bool = True
    normalize_file_paths: bool = True
    normalize_session_ids: bool = True
    normalize_numeric_ids: bool = True
    normalize_hex_values: bool = True
    
    # Custom patterns for specific applications
    custom_patterns: Dict[str, str] = None
    
    # Cache settings
    enable_caching: bool = True
    cache_size: int = 1000
    
    def __post_init__(self):
        if self.custom_patterns is None:
            self.custom_patterns = {}


class LogNormalizer:
    """
    Comprehensive log normalization system that replaces dynamic tokens with placeholders.
    
    This ensures that logs with identical structure but different dynamic values
    (IPs, ports, timestamps, etc.) are treated as the same log type for consistent
    anomaly detection classification.
    """
    
    def __init__(self, config: NormalizationConfig = None):
        self.config = config or NormalizationConfig()
        self._cache = {} if self.config.enable_caching else None
        self._template_cache = {} if self.config.enable_caching else None
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for efficient matching."""
        
        # IP address patterns (IPv4 and IPv6)
        self.ip_patterns = [
            re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),  # IPv4
            re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),  # IPv6
            re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b'),  # IPv6 compressed
        ]
        
        # Port number patterns
        self.port_patterns = [
            re.compile(r':\d{4,5}\b'),  # Standard ports (4-5 digits)
            re.compile(r'port\s+\d+', re.IGNORECASE),  # "port 8080" format
            re.compile(r'listening\s+on\s+port\s+\d+', re.IGNORECASE),  # "listening on port 8080"
        ]
        
        # Timestamp patterns
        self.timestamp_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?'),  # ISO format
            re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}'),  # MM/DD/YYYY format
            re.compile(r'\d{2}:\d{2}:\d{2}(?:\.\d+)?'),  # Time only
            re.compile(r'\d{4}-\d{2}-\d{2}'),  # Date only
        ]
        
        # UUID patterns
        self.uuid_patterns = [
            re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),  # Standard UUID
            re.compile(r'\b[0-9a-fA-F]{32}\b'),  # UUID without hyphens
        ]
        
        # Hash patterns
        self.hash_patterns = [
            re.compile(r'\b[0-9a-fA-F]{32}\b'),  # MD5
            re.compile(r'\b[0-9a-fA-F]{40}\b'),  # SHA1
            re.compile(r'\b[0-9a-fA-F]{64}\b'),  # SHA256
        ]
        
        # File path patterns
        self.file_path_patterns = [
            re.compile(r'/[a-zA-Z0-9/._-]+'),  # Unix paths
            re.compile(r'[A-Za-z]:\\[A-Za-z0-9\\._-]+'),  # Windows paths
            re.compile(r'\\\\[a-zA-Z0-9._-]+\\[a-zA-Z0-9/._-]+'),  # Network paths
        ]
        
        # Session ID patterns
        self.session_patterns = [
            re.compile(r'session[_-]?id[=:]\s*[a-zA-Z0-9_-]+', re.IGNORECASE),
            re.compile(r'sid[=:]\s*[a-zA-Z0-9_-]+', re.IGNORECASE),
        ]
        
        # Numeric ID patterns
        self.numeric_id_patterns = [
            re.compile(r'\bid\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bprocess\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bthread\s+\d+\b', re.IGNORECASE),
            re.compile(r'\bjob\s+\d+\b', re.IGNORECASE),
        ]
        
        # Hex value patterns
        self.hex_patterns = [
            re.compile(r'0x[0-9a-fA-F]+'),  # 0x prefixed
            re.compile(r'#[0-9a-fA-F]{6}'),  # Color codes
        ]
    
    def normalize(self, logline: str) -> str:
        """
        Normalize a single log line by replacing dynamic tokens with placeholders.
        
        Args:
            logline: The raw log line to normalize
            
        Returns:
            Normalized log line with dynamic tokens replaced by placeholders
        """
        if not isinstance(logline, str):
            return logline
        
        # Check cache first
        if self._cache is not None and logline in self._cache:
            return self._cache[logline]
        
        normalized = logline
        
        # Apply normalizations based on configuration
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
        
        # Apply custom patterns
        normalized = self._apply_custom_patterns(normalized)
        
        # Cache the result
        if self._cache is not None:
            if len(self._cache) >= self.config.cache_size:
                # Simple LRU: remove oldest entry
                self._cache.pop(next(iter(self._cache)))
            self._cache[logline] = normalized
        
        return normalized
    
    def normalize_batch(self, loglines: List[str]) -> List[str]:
        """
        Normalize a batch of log lines.
        
        Args:
            loglines: List of raw log lines to normalize
            
        Returns:
            List of normalized log lines
        """
        return [self.normalize(logline) for logline in loglines]
    
    def get_template_hash(self, logline: str) -> str:
        """
        Get a deterministic hash of the normalized log template.
        
        Args:
            logline: The raw log line
            
        Returns:
            Hash of the normalized template
        """
        normalized = self.normalize(logline)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get_template_classification(self, logline: str) -> Optional[Any]:
        """
        Get cached classification for a log template.
        
        Args:
            logline: The raw log line
            
        Returns:
            Cached classification or None if not found
        """
        if self._template_cache is None:
            return None
        
        template_hash = self.get_template_hash(logline)
        return self._template_cache.get(template_hash)
    
    def cache_template_classification(self, logline: str, classification: Any):
        """
        Cache classification for a log template.
        
        Args:
            logline: The raw log line
            classification: The classification result to cache
        """
        if self._template_cache is None:
            return
        
        template_hash = self.get_template_hash(logline)
        if len(self._template_cache) >= self.config.cache_size:
            # Simple LRU: remove oldest entry
            self._template_cache.pop(next(iter(self._template_cache)))
        self._template_cache[template_hash] = classification
    
    def _normalize_ips(self, text: str) -> str:
        """Normalize IP addresses."""
        for pattern in self.ip_patterns:
            text = pattern.sub('<IP>', text)
        return text
    
    def _normalize_ports(self, text: str) -> str:
        """Normalize port numbers."""
        for pattern in self.port_patterns:
            text = pattern.sub('<PORT>', text)
        return text
    
    def _normalize_timestamps(self, text: str) -> str:
        """Normalize timestamps."""
        for pattern in self.timestamp_patterns:
            text = pattern.sub('<TIMESTAMP>', text)
        return text
    
    def _normalize_uuids(self, text: str) -> str:
        """Normalize UUIDs."""
        for pattern in self.uuid_patterns:
            text = pattern.sub('<UUID>', text)
        return text
    
    def _normalize_hashes(self, text: str) -> str:
        """Normalize hash values."""
        for pattern in self.hash_patterns:
            text = pattern.sub('<HASH>', text)
        return text
    
    def _normalize_file_paths(self, text: str) -> str:
        """Normalize file paths."""
        for pattern in self.file_path_patterns:
            text = pattern.sub('<PATH>', text)
        return text
    
    def _normalize_session_ids(self, text: str) -> str:
        """Normalize session IDs."""
        for pattern in self.session_patterns:
            text = pattern.sub('<SESSION>', text)
        return text
    
    def _normalize_numeric_ids(self, text: str) -> str:
        """Normalize numeric IDs."""
        for pattern in self.numeric_id_patterns:
            text = pattern.sub('<ID>', text)
        return text
    
    def _normalize_hex_values(self, text: str) -> str:
        """Normalize hex values."""
        for pattern in self.hex_patterns:
            text = pattern.sub('<HEX>', text)
        return text
    
    def _apply_custom_patterns(self, text: str) -> str:
        """Apply custom normalization patterns."""
        for pattern, replacement in self.config.custom_patterns.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def clear_cache(self):
        """Clear all caches."""
        if self._cache is not None:
            self._cache.clear()
        if self._template_cache is not None:
            self._template_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        stats = {}
        if self._cache is not None:
            stats['normalization_cache_size'] = len(self._cache)
        if self._template_cache is not None:
            stats['template_cache_size'] = len(self._template_cache)
        return stats


# Global normalizer instance for easy access
_global_normalizer = None

def get_normalizer(config: NormalizationConfig = None) -> LogNormalizer:
    """
    Get a global normalizer instance.
    
    Args:
        config: Optional configuration for the normalizer
        
    Returns:
        LogNormalizer instance
    """
    global _global_normalizer
    if _global_normalizer is None or config is not None:
        _global_normalizer = LogNormalizer(config)
    return _global_normalizer


def normalize_log(logline: str, config: NormalizationConfig = None) -> str:
    """
    Convenience function to normalize a single log line.
    
    Args:
        logline: The raw log line to normalize
        config: Optional configuration for the normalizer
        
    Returns:
        Normalized log line
    """
    normalizer = get_normalizer(config)
    return normalizer.normalize(logline)


def normalize_logs(loglines: List[str], config: NormalizationConfig = None) -> List[str]:
    """
    Convenience function to normalize a list of log lines.
    
    Args:
        loglines: List of raw log lines to normalize
        config: Optional configuration for the normalizer
        
    Returns:
        List of normalized log lines
    """
    normalizer = get_normalizer(config)
    return normalizer.normalize_batch(loglines) 