"""
Configuration management system for the web automation framework.

This module provides centralized configuration management with support for:
- Environment-specific configurations (development, staging, production)
- YAML/JSON configuration file loading
- Environment variable overrides
- Configuration validation and default values
- Security configuration management
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import ConfigurationException
from .logging import get_logger

logger = get_logger(__name__)


class Environment(Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class BrowserConfig:
    """Browser-specific configuration."""
    name: str
    driver_path: str = "auto"
    options: list = field(default_factory=list)
    headless: bool = False
    window_size: tuple = (1920, 1080)


@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds."""
    page_load_time: float = 3.0
    dom_content_loaded: float = 2.0
    first_contentful_paint: float = 1.5
    largest_contentful_paint: float = 2.5
    cumulative_layout_shift: float = 0.1


@dataclass
class NotificationConfig:
    """Notification system configuration."""
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#test-results"
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender: str = ""
    recipients: list = field(default_factory=list)


@dataclass
class TestDataConfig:
    """Test data configuration."""
    users: Dict[str, Dict[str, str]] = field(default_factory=dict)
    api_endpoints: Dict[str, str] = field(default_factory=dict)
    database_cleanup: bool = True


class ConfigManager:
    """
    Centralized configuration management system.
    
    Handles loading and managing configurations from multiple sources:
    - YAML/JSON configuration files
    - Environment variables
    - Default values
    
    Supports environment-specific configurations and security settings.
    """
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Directory containing configuration files
            environment: Target environment (development, staging, production)
        """
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv('TEST_ENV', 'development')
        self._config_cache: Dict[str, Any] = {}
        self._load_configurations()
        
        logger.info(f"ConfigManager initialized for environment: {self.environment}")
    
    def _load_configurations(self) -> None:
        """Load all configuration files and environment variables."""
        try:
            # Load main environment configuration
            self._load_environment_config()
            
            # Load browser configurations
            self._load_browser_config()
            
            # Load performance thresholds
            self._load_performance_config()
            
            # Load notification settings
            self._load_notification_config()
            
            # Load test data configuration
            self._load_test_data_config()
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            # Validate configuration after loading
            self.validate_configuration()
            
            logger.info("All configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise ConfigurationException(f"Configuration loading failed: {e}")
    
    def _load_environment_config(self) -> None:
        """Load environment-specific configuration."""
        env_file = self.config_dir / "environments.yml"
        
        if not env_file.exists():
            raise ConfigurationException(f"Environment config file not found: {env_file}")
        
        with open(env_file, 'r', encoding='utf-8') as f:
            env_configs = yaml.safe_load(f)
        
        if self.environment not in env_configs:
            raise ConfigurationException(f"Environment '{self.environment}' not found in config")
        
        self._config_cache['environment'] = env_configs[self.environment]
        logger.debug(f"Loaded environment config for: {self.environment}")
    
    def _load_browser_config(self) -> None:
        """Load browser configurations."""
        env_file = self.config_dir / "environments.yml"
        
        with open(env_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        browsers = config.get('browsers', {})
        self._config_cache['browsers'] = {}
        
        for browser_name, browser_config in browsers.items():
            self._config_cache['browsers'][browser_name] = BrowserConfig(
                name=browser_name,
                driver_path=browser_config.get('driver_path', 'auto'),
                options=browser_config.get('options', []),
                headless=self._config_cache['environment'].get('headless', False),
                window_size=tuple(map(int, browser_config.get('window_size', '1920,1080').split(',')))
                if isinstance(browser_config.get('window_size'), str)
                else (1920, 1080)
            )
        
        logger.debug(f"Loaded browser configs: {list(self._config_cache['browsers'].keys())}")
    
    def _load_performance_config(self) -> None:
        """Load performance monitoring configuration."""
        env_file = self.config_dir / "environments.yml"
        
        with open(env_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        perf_config = config.get('performance', {})
        self._config_cache['performance'] = PerformanceThresholds(
            page_load_time=perf_config.get('page_load_time', 3.0),
            dom_content_loaded=perf_config.get('dom_content_loaded', 2.0),
            first_contentful_paint=perf_config.get('first_contentful_paint', 1.5),
            largest_contentful_paint=perf_config.get('largest_contentful_paint', 2.5),
            cumulative_layout_shift=perf_config.get('cumulative_layout_shift', 0.1)
        )
        
        logger.debug("Loaded performance thresholds")
    
    def _load_notification_config(self) -> None:
        """Load notification system configuration."""
        env_file = self.config_dir / "environments.yml"
        
        with open(env_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        notif_config = config.get('notifications', {})
        slack_config = notif_config.get('slack', {})
        email_config = notif_config.get('email', {})
        
        self._config_cache['notifications'] = NotificationConfig(
            slack_enabled=slack_config.get('enabled', False),
            slack_webhook_url=slack_config.get('webhook_url', ''),
            slack_channel=slack_config.get('channel', '#test-results'),
            email_enabled=email_config.get('enabled', False),
            smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_config.get('smtp_port', 587),
            sender=email_config.get('sender', ''),
            recipients=email_config.get('recipients', [])
        )
        
        logger.debug("Loaded notification configuration")
    
    def _load_test_data_config(self) -> None:
        """Load test data configuration."""
        env_file = self.config_dir / "environments.yml"
        
        with open(env_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        test_data = config.get('test_data', {})
        self._config_cache['test_data'] = TestDataConfig(
            users=test_data.get('users', {}),
            api_endpoints=test_data.get('api_endpoints', {}),
            database_cleanup=test_data.get('database_cleanup', True)
        )
        
        logger.debug("Loaded test data configuration")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_overrides = {
            'TEST_BASE_URL': ('environment', 'base_url'),
            'TEST_HEADLESS': ('environment', 'headless'),
            'TEST_TIMEOUT': ('environment', 'timeout'),
            'TEST_LOG_LEVEL': ('environment', 'log_level'),
            'TEST_PARALLEL_WORKERS': ('environment', 'parallel_workers'),
            'TEST_SCREENSHOT_ON_FAILURE': ('environment', 'screenshot_on_failure'),
            'TEST_PERFORMANCE_MONITORING': ('environment', 'performance_monitoring'),
        }
        
        for env_var, (section, key) in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key in ['headless', 'screenshot_on_failure', 'performance_monitoring']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif key in ['timeout', 'parallel_workers']:
                    value = int(value)
                
                self._config_cache[section][key] = value
                logger.debug(f"Applied environment override: {env_var}={value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'environment.base_url')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self._config_cache
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = getattr(value, k, None)
                
                if value is None:
                    return default
            
            return value
            
        except (KeyError, AttributeError):
            return default
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get current environment configuration."""
        return self._config_cache.get('environment', {})
    
    def get_browser_config(self, browser_name: str) -> Optional[BrowserConfig]:
        """
        Get browser configuration.
        
        Args:
            browser_name: Browser name (chrome, firefox, edge)
            
        Returns:
            BrowserConfig object or None if not found
        """
        return self._config_cache.get('browsers', {}).get(browser_name)
    
    def get_performance_thresholds(self) -> PerformanceThresholds:
        """Get performance monitoring thresholds."""
        return self._config_cache.get('performance', PerformanceThresholds())
    
    def get_notification_config(self) -> NotificationConfig:
        """Get notification system configuration."""
        return self._config_cache.get('notifications', NotificationConfig())
    
    def get_test_data_config(self) -> TestDataConfig:
        """Get test data configuration."""
        return self._config_cache.get('test_data', TestDataConfig())
    
    def get_base_url(self) -> str:
        """Get base URL for current environment."""
        return self.get('environment.base_url', 'http://localhost:3000')
    
    def get_database_url(self) -> str:
        """Get database URL for current environment."""
        return self.get('environment.database_url', 'sqlite:///test.db')
    
    def is_headless(self) -> bool:
        """Check if tests should run in headless mode."""
        return self.get('environment.headless', False)
    
    def get_timeout(self) -> int:
        """Get default timeout value."""
        return self.get('environment.timeout', 10)
    
    def get_log_level(self) -> str:
        """Get logging level."""
        return self.get('environment.log_level', 'INFO')
    
    def get_parallel_workers(self) -> int:
        """Get number of parallel workers."""
        return self.get('environment.parallel_workers', 1)
    
    def should_take_screenshot_on_failure(self) -> bool:
        """Check if screenshots should be taken on test failure."""
        return self.get('environment.screenshot_on_failure', True)
    
    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return self.get('environment.performance_monitoring', False)
    
    def is_read_only(self) -> bool:
        """Check if environment is read-only (production)."""
        return self.get('environment.read_only', False)
    
    def validate_configuration(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationException: If configuration is invalid
        """
        try:
            # Validate required environment settings
            required_keys = ['base_url', 'timeout']
            env_config = self.get_environment_config()
            
            for key in required_keys:
                if key not in env_config:
                    raise ConfigurationException(f"Required configuration key missing: {key}")
            
            # Validate base URL format
            base_url = self.get_base_url()
            if not base_url.startswith(('http://', 'https://')):
                raise ConfigurationException(f"Invalid base URL format: {base_url}")
            
            # Validate timeout value
            timeout = self.get_timeout()
            if not isinstance(timeout, int) or timeout <= 0:
                raise ConfigurationException(f"Invalid timeout value: {timeout}")
            
            # Validate parallel workers
            workers = self.get_parallel_workers()
            if not isinstance(workers, int) or workers <= 0:
                raise ConfigurationException(f"Invalid parallel workers value: {workers}")
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigurationException(f"Configuration validation failed: {e}")
    
    def reload_configuration(self) -> None:
        """Reload configuration from files."""
        logger.info("Reloading configuration...")
        self._config_cache.clear()
        self._load_configurations()
        self.validate_configuration()
        logger.info("Configuration reloaded successfully")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for debugging.
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'environment': self.environment,
            'base_url': self.get_base_url(),
            'headless': self.is_headless(),
            'timeout': self.get_timeout(),
            'log_level': self.get_log_level(),
            'parallel_workers': self.get_parallel_workers(),
            'screenshot_on_failure': self.should_take_screenshot_on_failure(),
            'performance_monitoring': self.is_performance_monitoring_enabled(),
            'read_only': self.is_read_only(),
            'available_browsers': list(self._config_cache.get('browsers', {}).keys()),
            'notification_enabled': {
                'slack': self.get_notification_config().slack_enabled,
                'email': self.get_notification_config().email_enabled
            }
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str = "config", environment: Optional[str] = None) -> ConfigManager:
    """
    Get global ConfigManager instance (singleton pattern).
    
    Args:
        config_dir: Configuration directory path
        environment: Target environment
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir, environment)
    
    return _config_manager


def reset_config_manager() -> None:
    """Reset global ConfigManager instance (mainly for testing)."""
    global _config_manager
    _config_manager = None