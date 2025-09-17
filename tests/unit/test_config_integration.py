"""
Integration tests for ConfigManager with actual configuration files.

Tests the ConfigManager with the real environments.yml file to ensure
it works correctly with the actual project configuration.
"""

import pytest
from pathlib import Path

from src.core.config import ConfigManager, get_config_manager, reset_config_manager
from src.core.exceptions import ConfigurationException


class TestConfigManagerIntegration:
    """Integration tests with actual configuration files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_config_manager()
        self.config_dir = "config"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        reset_config_manager()
    
    def test_load_actual_development_config(self):
        """Test loading actual development configuration."""
        config = ConfigManager(self.config_dir, 'development')
        
        # Test basic configuration values
        assert config.get_base_url() == 'http://localhost:3000'
        assert config.is_headless() is False
        assert config.get_timeout() == 10
        assert config.get_log_level() == 'DEBUG'
        assert config.get_parallel_workers() == 1
        assert config.should_take_screenshot_on_failure() is True
        assert config.is_performance_monitoring_enabled() is False
        assert config.is_read_only() is False
    
    def test_load_actual_staging_config(self):
        """Test loading actual staging configuration."""
        config = ConfigManager(self.config_dir, 'staging')
        
        # Test staging-specific values
        assert config.get_base_url() == 'https://staging.example.com'
        assert config.is_headless() is True
        assert config.get_timeout() == 15
        assert config.get_log_level() == 'INFO'
        assert config.get_parallel_workers() == 2
        assert config.is_performance_monitoring_enabled() is True
    
    def test_load_actual_production_config(self):
        """Test loading actual production configuration."""
        config = ConfigManager(self.config_dir, 'production')
        
        # Test production-specific values
        assert config.get_base_url() == 'https://example.com'
        assert config.is_headless() is True
        assert config.get_timeout() == 20
        assert config.get_log_level() == 'WARNING'
        assert config.get_parallel_workers() == 4
        assert config.is_performance_monitoring_enabled() is True
        assert config.is_read_only() is True
    
    def test_browser_configurations(self):
        """Test browser configurations from actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        # Test Chrome configuration
        chrome_config = config.get_browser_config('chrome')
        assert chrome_config is not None
        assert chrome_config.name == 'chrome'
        assert chrome_config.driver_path == 'auto'
        assert '--no-sandbox' in chrome_config.options
        assert '--disable-dev-shm-usage' in chrome_config.options
        
        # Test Firefox configuration
        firefox_config = config.get_browser_config('firefox')
        assert firefox_config is not None
        assert firefox_config.name == 'firefox'
        assert '--width=1920' in firefox_config.options
        assert '--height=1080' in firefox_config.options
        
        # Test Edge configuration
        edge_config = config.get_browser_config('edge')
        assert edge_config is not None
        assert edge_config.name == 'edge'
    
    def test_performance_thresholds(self):
        """Test performance thresholds from actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        perf_thresholds = config.get_performance_thresholds()
        assert perf_thresholds.page_load_time == 3.0
        assert perf_thresholds.dom_content_loaded == 2.0
        assert perf_thresholds.first_contentful_paint == 1.5
        assert perf_thresholds.largest_contentful_paint == 2.5
        assert perf_thresholds.cumulative_layout_shift == 0.1
    
    def test_notification_configuration(self):
        """Test notification configuration from actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        notif_config = config.get_notification_config()
        assert notif_config.slack_enabled is False
        assert notif_config.slack_channel == '#test-results'
        assert notif_config.email_enabled is False
        assert notif_config.smtp_server == 'smtp.gmail.com'
        assert notif_config.smtp_port == 587
    
    def test_test_data_configuration(self):
        """Test test data configuration from actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        test_data_config = config.get_test_data_config()
        assert 'admin' in test_data_config.users
        assert 'regular' in test_data_config.users
        assert test_data_config.users['admin']['username'] == 'admin@example.com'
        assert test_data_config.users['regular']['username'] == 'user@example.com'
        assert test_data_config.database_cleanup is True
    
    def test_configuration_validation_with_actual_file(self):
        """Test configuration validation with actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        # Should not raise any exceptions
        assert config.validate_configuration() is True
    
    def test_config_summary_with_actual_file(self):
        """Test configuration summary with actual file."""
        config = ConfigManager(self.config_dir, 'development')
        
        summary = config.get_config_summary()
        
        assert summary['environment'] == 'development'
        assert summary['base_url'] == 'http://localhost:3000'
        assert summary['headless'] is False
        assert summary['timeout'] == 10
        assert summary['log_level'] == 'DEBUG'
        assert summary['parallel_workers'] == 1
        assert summary['screenshot_on_failure'] is True
        assert summary['performance_monitoring'] is False
        assert summary['read_only'] is False
        
        # Check available browsers
        expected_browsers = ['chrome', 'firefox', 'edge']
        for browser in expected_browsers:
            assert browser in summary['available_browsers']
        
        # Check notification settings
        assert summary['notification_enabled']['slack'] is False
        assert summary['notification_enabled']['email'] is False
    
    def test_global_config_manager_with_actual_file(self):
        """Test global ConfigManager with actual file."""
        config1 = get_config_manager(self.config_dir, 'development')
        config2 = get_config_manager(self.config_dir, 'development')
        
        # Should be the same instance (singleton)
        assert config1 is config2
        
        # Should work with actual configuration
        assert config1.get_base_url() == 'http://localhost:3000'
        assert config2.get_base_url() == 'http://localhost:3000'
    
    def test_dot_notation_access_with_actual_file(self):
        """Test dot notation access with actual configuration."""
        config = ConfigManager(self.config_dir, 'development')
        
        # Test nested access
        assert config.get('environment.base_url') == 'http://localhost:3000'
        assert config.get('environment.headless') is False
        assert config.get('environment.timeout') == 10
        assert config.get('environment.log_level') == 'DEBUG'
        
        # Test with default values
        assert config.get('environment.nonexistent', 'default') == 'default'
        assert config.get('nonexistent.key', 42) == 42
    
    def test_all_environments_load_successfully(self):
        """Test that all defined environments load successfully."""
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            config = ConfigManager(self.config_dir, env)
            
            # Basic validation that config loaded
            assert config.environment == env
            assert config.get_base_url() is not None
            assert config.get_timeout() > 0
            assert config.get_log_level() in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
            assert config.get_parallel_workers() > 0
            
            # Validate configuration
            assert config.validate_configuration() is True