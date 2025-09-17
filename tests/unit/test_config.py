"""
Unit tests for the configuration management system.

Tests cover:
- Configuration loading from YAML files
- Environment-specific configurations
- Environment variable overrides
- Configuration validation
- Browser configuration management
- Performance thresholds
- Notification settings
- Test data configuration
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.config import (
    ConfigManager, 
    Environment, 
    BrowserConfig, 
    PerformanceThresholds,
    NotificationConfig,
    TestDataConfig,
    get_config_manager,
    reset_config_manager
)
from src.core.exceptions import ConfigurationException


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset global config manager
        reset_config_manager()
        
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Sample configuration data
        self.sample_config = {
            'development': {
                'base_url': 'http://localhost:3000',
                'database_url': 'sqlite:///test.db',
                'headless': False,
                'timeout': 10,
                'log_level': 'DEBUG',
                'parallel_workers': 1,
                'screenshot_on_failure': True,
                'performance_monitoring': False
            },
            'staging': {
                'base_url': 'https://staging.example.com',
                'database_url': 'postgresql://staging_db',
                'headless': True,
                'timeout': 15,
                'log_level': 'INFO',
                'parallel_workers': 2,
                'screenshot_on_failure': True,
                'performance_monitoring': True
            },
            'production': {
                'base_url': 'https://example.com',
                'database_url': 'postgresql://prod_db',
                'headless': True,
                'timeout': 20,
                'log_level': 'WARNING',
                'parallel_workers': 4,
                'screenshot_on_failure': True,
                'performance_monitoring': True,
                'read_only': True
            },
            'browsers': {
                'chrome': {
                    'driver_path': 'auto',
                    'options': ['--no-sandbox', '--disable-dev-shm-usage']
                },
                'firefox': {
                    'driver_path': 'auto',
                    'options': ['--width=1920', '--height=1080']
                }
            },
            'performance': {
                'page_load_time': 3.0,
                'dom_content_loaded': 2.0,
                'first_contentful_paint': 1.5,
                'largest_contentful_paint': 2.5,
                'cumulative_layout_shift': 0.1
            },
            'notifications': {
                'slack': {
                    'enabled': False,
                    'webhook_url': 'https://hooks.slack.com/test',
                    'channel': '#test-results'
                },
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'sender': 'test@example.com',
                    'recipients': ['dev@example.com']
                }
            },
            'test_data': {
                'users': {
                    'admin': {
                        'username': 'admin@example.com',
                        'password': 'admin123'
                    }
                },
                'database_cleanup': True
            }
        }
        
        # Write sample config to temporary file
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(self.sample_config, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_config_manager()
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        assert config.environment == 'development'
        assert config.config_dir == Path(self.config_dir)
        assert config._config_cache is not None
    
    def test_load_environment_config(self):
        """Test loading environment-specific configuration."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        env_config = config.get_environment_config()
        assert env_config['base_url'] == 'http://localhost:3000'
        assert env_config['headless'] is False
        assert env_config['timeout'] == 10
    
    def test_load_different_environments(self):
        """Test loading different environment configurations."""
        # Test development
        dev_config = ConfigManager(str(self.config_dir), 'development')
        assert dev_config.get_base_url() == 'http://localhost:3000'
        assert dev_config.is_headless() is False
        
        # Test staging
        staging_config = ConfigManager(str(self.config_dir), 'staging')
        assert staging_config.get_base_url() == 'https://staging.example.com'
        assert staging_config.is_headless() is True
        
        # Test production
        prod_config = ConfigManager(str(self.config_dir), 'production')
        assert prod_config.get_base_url() == 'https://example.com'
        assert prod_config.is_read_only() is True
    
    def test_browser_config_loading(self):
        """Test browser configuration loading."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        chrome_config = config.get_browser_config('chrome')
        assert chrome_config is not None
        assert chrome_config.name == 'chrome'
        assert chrome_config.driver_path == 'auto'
        assert '--no-sandbox' in chrome_config.options
        
        firefox_config = config.get_browser_config('firefox')
        assert firefox_config is not None
        assert firefox_config.name == 'firefox'
        assert '--width=1920' in firefox_config.options
    
    def test_performance_thresholds_loading(self):
        """Test performance thresholds loading."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        perf_thresholds = config.get_performance_thresholds()
        assert perf_thresholds.page_load_time == 3.0
        assert perf_thresholds.dom_content_loaded == 2.0
        assert perf_thresholds.first_contentful_paint == 1.5
        assert perf_thresholds.largest_contentful_paint == 2.5
        assert perf_thresholds.cumulative_layout_shift == 0.1
    
    def test_notification_config_loading(self):
        """Test notification configuration loading."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        notif_config = config.get_notification_config()
        assert notif_config.slack_enabled is False
        assert notif_config.slack_webhook_url == 'https://hooks.slack.com/test'
        assert notif_config.slack_channel == '#test-results'
        assert notif_config.email_enabled is False
        assert notif_config.smtp_server == 'smtp.gmail.com'
        assert notif_config.smtp_port == 587
    
    def test_test_data_config_loading(self):
        """Test test data configuration loading."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        test_data_config = config.get_test_data_config()
        assert 'admin' in test_data_config.users
        assert test_data_config.users['admin']['username'] == 'admin@example.com'
        assert test_data_config.database_cleanup is True
    
    @patch.dict(os.environ, {
        'TEST_BASE_URL': 'http://override.com',
        'TEST_HEADLESS': 'true',
        'TEST_TIMEOUT': '30',
        'TEST_LOG_LEVEL': 'ERROR'
    })
    def test_environment_variable_overrides(self):
        """Test environment variable overrides."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        assert config.get_base_url() == 'http://override.com'
        assert config.is_headless() is True
        assert config.get_timeout() == 30
        assert config.get_log_level() == 'ERROR'
    
    def test_get_method_with_dot_notation(self):
        """Test get method with dot notation."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        assert config.get('environment.base_url') == 'http://localhost:3000'
        assert config.get('environment.headless') is False
        assert config.get('environment.nonexistent', 'default') == 'default'
    
    def test_configuration_validation_success(self):
        """Test successful configuration validation."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        assert config.validate_configuration() is True
    
    def test_configuration_validation_missing_required_key(self):
        """Test configuration validation with missing required key."""
        # Create config without required key
        invalid_config = {
            'development': {
                'headless': False
                # Missing 'base_url' and 'timeout'
            }
        }
        
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationException, match="Required configuration key missing"):
            ConfigManager(str(self.config_dir), 'development')
    
    def test_configuration_validation_invalid_base_url(self):
        """Test configuration validation with invalid base URL."""
        invalid_config = {
            'development': {
                'base_url': 'invalid-url',
                'timeout': 10
            }
        }
        
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationException, match="Invalid base URL format"):
            ConfigManager(str(self.config_dir), 'development')
    
    def test_configuration_validation_invalid_timeout(self):
        """Test configuration validation with invalid timeout."""
        invalid_config = {
            'development': {
                'base_url': 'http://localhost:3000',
                'timeout': -1
            }
        }
        
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationException, match="Invalid timeout value"):
            ConfigManager(str(self.config_dir), 'development')
    
    def test_nonexistent_environment(self):
        """Test loading nonexistent environment."""
        with pytest.raises(ConfigurationException, match="Environment 'nonexistent' not found"):
            ConfigManager(str(self.config_dir), 'nonexistent')
    
    def test_missing_config_file(self):
        """Test handling missing configuration file."""
        empty_dir = tempfile.mkdtemp()
        
        with pytest.raises(ConfigurationException, match="Environment config file not found"):
            ConfigManager(empty_dir, 'development')
        
        import shutil
        shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_reload_configuration(self):
        """Test configuration reloading."""
        config = ConfigManager(str(self.config_dir), 'development')
        original_url = config.get_base_url()
        
        # Modify config file
        modified_config = self.sample_config.copy()
        modified_config['development']['base_url'] = 'http://modified.com'
        
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(modified_config, f)
        
        # Reload configuration
        config.reload_configuration()
        
        assert config.get_base_url() == 'http://modified.com'
        assert config.get_base_url() != original_url
    
    def test_get_config_summary(self):
        """Test configuration summary generation."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        summary = config.get_config_summary()
        
        assert summary['environment'] == 'development'
        assert summary['base_url'] == 'http://localhost:3000'
        assert summary['headless'] is False
        assert summary['timeout'] == 10
        assert 'chrome' in summary['available_browsers']
        assert 'firefox' in summary['available_browsers']
    
    def test_convenience_methods(self):
        """Test convenience methods for common configuration values."""
        config = ConfigManager(str(self.config_dir), 'development')
        
        assert config.get_base_url() == 'http://localhost:3000'
        assert config.get_database_url() == 'sqlite:///test.db'
        assert config.is_headless() is False
        assert config.get_timeout() == 10
        assert config.get_log_level() == 'DEBUG'
        assert config.get_parallel_workers() == 1
        assert config.should_take_screenshot_on_failure() is True
        assert config.is_performance_monitoring_enabled() is False
        assert config.is_read_only() is False
    
    def test_production_read_only_flag(self):
        """Test production environment read-only flag."""
        config = ConfigManager(str(self.config_dir), 'production')
        
        assert config.is_read_only() is True
    
    @patch.dict(os.environ, {'TEST_ENV': 'staging'})
    def test_default_environment_from_env_var(self):
        """Test default environment from environment variable."""
        config = ConfigManager(str(self.config_dir))
        
        assert config.environment == 'staging'
        assert config.get_base_url() == 'https://staging.example.com'


class TestGlobalConfigManager:
    """Test cases for global ConfigManager functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_config_manager()
        
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Sample minimal configuration
        sample_config = {
            'development': {
                'base_url': 'http://localhost:3000',
                'timeout': 10
            }
        }
        
        config_file = self.config_dir / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_config_manager()
    
    def test_get_config_manager_singleton(self):
        """Test global ConfigManager singleton pattern."""
        config1 = get_config_manager(str(self.config_dir), 'development')
        config2 = get_config_manager(str(self.config_dir), 'development')
        
        assert config1 is config2
    
    def test_reset_config_manager(self):
        """Test resetting global ConfigManager."""
        config1 = get_config_manager(str(self.config_dir), 'development')
        reset_config_manager()
        config2 = get_config_manager(str(self.config_dir), 'development')
        
        assert config1 is not config2


class TestDataClasses:
    """Test cases for configuration data classes."""
    
    def test_browser_config_creation(self):
        """Test BrowserConfig creation."""
        config = BrowserConfig(
            name='chrome',
            driver_path='/path/to/driver',
            options=['--headless', '--no-sandbox'],
            headless=True,
            window_size=(1920, 1080)
        )
        
        assert config.name == 'chrome'
        assert config.driver_path == '/path/to/driver'
        assert '--headless' in config.options
        assert config.headless is True
        assert config.window_size == (1920, 1080)
    
    def test_performance_thresholds_creation(self):
        """Test PerformanceThresholds creation."""
        thresholds = PerformanceThresholds(
            page_load_time=5.0,
            dom_content_loaded=3.0,
            first_contentful_paint=2.0,
            largest_contentful_paint=4.0,
            cumulative_layout_shift=0.2
        )
        
        assert thresholds.page_load_time == 5.0
        assert thresholds.dom_content_loaded == 3.0
        assert thresholds.first_contentful_paint == 2.0
        assert thresholds.largest_contentful_paint == 4.0
        assert thresholds.cumulative_layout_shift == 0.2
    
    def test_notification_config_creation(self):
        """Test NotificationConfig creation."""
        config = NotificationConfig(
            slack_enabled=True,
            slack_webhook_url='https://hooks.slack.com/test',
            slack_channel='#alerts',
            email_enabled=True,
            smtp_server='smtp.test.com',
            smtp_port=465,
            sender='test@example.com',
            recipients=['dev1@example.com', 'dev2@example.com']
        )
        
        assert config.slack_enabled is True
        assert config.slack_webhook_url == 'https://hooks.slack.com/test'
        assert config.slack_channel == '#alerts'
        assert config.email_enabled is True
        assert config.smtp_server == 'smtp.test.com'
        assert config.smtp_port == 465
        assert config.sender == 'test@example.com'
        assert len(config.recipients) == 2
    
    def test_test_data_config_creation(self):
        """Test TestDataConfig creation."""
        config = TestDataConfig(
            users={'admin': {'username': 'admin', 'password': 'pass'}},
            api_endpoints={'login': '/api/login', 'users': '/api/users'},
            database_cleanup=False
        )
        
        assert 'admin' in config.users
        assert config.users['admin']['username'] == 'admin'
        assert 'login' in config.api_endpoints
        assert config.database_cleanup is False


class TestEnvironmentEnum:
    """Test cases for Environment enum."""
    
    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.DEVELOPMENT.value == 'development'
        assert Environment.STAGING.value == 'staging'
        assert Environment.PRODUCTION.value == 'production'
    
    def test_environment_comparison(self):
        """Test Environment enum comparison."""
        assert Environment.DEVELOPMENT == Environment.DEVELOPMENT
        assert Environment.DEVELOPMENT != Environment.STAGING