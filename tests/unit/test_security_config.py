"""
Unit tests for the security configuration management system.

Tests cover:
- SecurityConfig class functionality
- Environment variable loading
- Security validation
- Sensitive data masking
- Integration with ConfigManager
"""

import os
import pytest
import tempfile
from unittest.mock import patch

from src.core.config import SecurityConfig, ConfigManager, reset_config_manager
from src.core.exceptions import ConfigurationException


class TestSecurityConfig:
    """Test cases for SecurityConfig class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing environment variables
        self.original_env = {}
        self.security_env_vars = [
            'TEST_USERNAME', 'TEST_PASSWORD', 'API_KEY', 'DATABASE_URL',
            'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'JWT_SECRET', 'ENCRYPTION_KEY',
            'SSL_VERIFY', 'HTTPS_ONLY', 'MASK_SENSITIVE_DATA', 'AUTO_CLEANUP_DATA'
        ]
        
        for var in self.security_env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear all security environment variables first
        for var in self.security_env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_security_config_default_values(self):
        """Test SecurityConfig with default values."""
        config = SecurityConfig()
        
        assert config.test_username is None
        assert config.test_password is None
        assert config.api_key is None
        assert config.database_url is None
        assert config.admin_username is None
        assert config.admin_password is None
        assert config.jwt_secret is None
        assert config.encryption_key is None
        assert config.ssl_verify is True
        assert config.https_only is True
        assert config.mask_sensitive_data is True
        assert config.auto_cleanup_data is True
    
    def test_security_config_from_environment_variables(self):
        """Test loading security configuration from environment variables."""
        # Set environment variables
        os.environ['TEST_USERNAME'] = 'test_user'
        os.environ['TEST_PASSWORD'] = 'test_pass'
        os.environ['API_KEY'] = 'api_key_123'
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/test'
        os.environ['SSL_VERIFY'] = 'false'
        os.environ['HTTPS_ONLY'] = 'false'
        
        config = SecurityConfig()
        
        assert config.test_username == 'test_user'
        assert config.test_password == 'test_pass'
        assert config.api_key == 'api_key_123'
        assert config.database_url == 'postgresql://user:pass@localhost/test'
        assert config.ssl_verify is False
        assert config.https_only is False
    
    def test_boolean_environment_variable_parsing(self):
        """Test parsing of boolean environment variables."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False),
            ('invalid', False)
        ]
        
        for env_value, expected in test_cases:
            os.environ['SSL_VERIFY'] = env_value
            config = SecurityConfig()
            assert config.ssl_verify == expected, f"Failed for value: {env_value}"
            del os.environ['SSL_VERIFY']
    
    def test_has_credentials_methods(self):
        """Test credential availability check methods."""
        config = SecurityConfig()
        
        # Initially no credentials
        assert not config.has_credentials()
        assert not config.has_admin_credentials()
        assert not config.has_api_key()
        
        # Set test credentials
        config.test_username = 'test_user'
        config.test_password = 'test_pass'
        assert config.has_credentials()
        
        # Set admin credentials
        config.admin_username = 'admin_user'
        config.admin_password = 'admin_pass'
        assert config.has_admin_credentials()
        
        # Set API key
        config.api_key = 'api_key_123'
        assert config.has_api_key()
    
    def test_get_masked_config(self):
        """Test sensitive data masking in configuration."""
        config = SecurityConfig()
        config.test_username = 'test_user'
        config.test_password = 'secret_password'
        config.api_key = 'secret_api_key'
        config.ssl_verify = True
        
        masked_config = config.get_masked_config()
        
        assert masked_config['test_username'] == 'test_user'
        assert masked_config['test_password'] == '***MASKED***'
        assert masked_config['api_key'] == '***MASKED***'
        assert masked_config['ssl_verify'] is True
    
    def test_database_url_validation_valid(self):
        """Test valid database URL validation."""
        valid_urls = [
            'sqlite:///test.db',
            'postgresql://user:pass@localhost/db',
            'mysql://user:pass@localhost/db',
            'oracle://user:pass@localhost/db',
            'mssql://user:pass@localhost/db'
        ]
        
        for url in valid_urls:
            config = SecurityConfig()
            config.database_url = url
            config._validate_security_settings()  # Should not raise
    
    def test_database_url_validation_invalid(self):
        """Test invalid database URL validation."""
        config = SecurityConfig()
        config.database_url = 'invalid_url'
        
        with pytest.raises(ConfigurationException, match="Invalid database URL format"):
            config._validate_security_settings()
    
    def test_get_database_config(self):
        """Test database configuration extraction."""
        config = SecurityConfig()
        
        # No database URL
        assert config.get_database_config() is None
        
        # With database URL
        config.database_url = 'postgresql://user:pass@localhost/test'
        db_config = config.get_database_config()
        
        assert db_config is not None
        assert db_config['scheme'] == 'postgresql'
        assert db_config['url'] == 'postgresql://user:pass@localhost/test'
        assert 'masked_url' in db_config
    
    def test_database_url_masking(self):
        """Test database URL masking functionality."""
        config = SecurityConfig()
        config.mask_sensitive_data = True
        
        # URL with credentials
        original_url = 'postgresql://user:password@localhost/test'
        masked_url = config._mask_database_url(original_url)
        assert masked_url == 'postgresql://***:***@localhost/test'
        
        # URL without credentials
        simple_url = 'sqlite:///test.db'
        masked_simple = config._mask_database_url(simple_url)
        assert masked_simple == simple_url
        
        # Masking disabled
        config.mask_sensitive_data = False
        unmasked_url = config._mask_database_url(original_url)
        assert unmasked_url == original_url
    
    @patch.dict(os.environ, {'TEST_ENV': 'production'})
    def test_production_validation_missing_credentials(self):
        """Test production environment validation with missing credentials."""
        with pytest.raises(ConfigurationException, match="Required security settings missing"):
            SecurityConfig()
    
    @patch.dict(os.environ, {
        'TEST_ENV': 'production',
        'TEST_USERNAME': 'prod_user',
        'TEST_PASSWORD': 'prod_pass'
    })
    def test_production_validation_with_credentials(self):
        """Test production environment validation with required credentials."""
        config = SecurityConfig()  # Should not raise
        assert config.test_username == 'prod_user'
        assert config.test_password == 'prod_pass'


class TestSecurityConfigIntegration:
    """Test cases for SecurityConfig integration with ConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_config_manager()
        
        # Clear any existing environment variables
        self.original_env = {}
        self.security_env_vars = [
            'TEST_USERNAME', 'TEST_PASSWORD', 'API_KEY', 'DATABASE_URL',
            'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'JWT_SECRET', 'ENCRYPTION_KEY',
            'SSL_VERIFY', 'HTTPS_ONLY', 'MASK_SENSITIVE_DATA', 'AUTO_CLEANUP_DATA'
        ]
        
        for var in self.security_env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
        
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create minimal config file
        import yaml
        from pathlib import Path
        
        config_data = {
            'development': {
                'base_url': 'http://localhost:3000',
                'timeout': 10
            }
        }
        
        config_file = Path(self.temp_dir) / 'environments.yml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        reset_config_manager()
        
        # Clear all security environment variables first
        for var in self.security_env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_config_manager_security_integration(self):
        """Test ConfigManager integration with SecurityConfig."""
        config_manager = ConfigManager(self.temp_dir, 'development')
        
        security_config = config_manager.get_security_config()
        assert isinstance(security_config, SecurityConfig)
    
    @patch.dict(os.environ, {
        'TEST_USERNAME': 'integration_user',
        'TEST_PASSWORD': 'integration_pass',
        'API_KEY': 'integration_api_key'
    })
    def test_config_manager_security_methods(self):
        """Test ConfigManager security convenience methods."""
        config_manager = ConfigManager(self.temp_dir, 'development')
        
        # Test credential methods
        test_creds = config_manager.get_test_credentials()
        assert test_creds is not None
        assert test_creds['username'] == 'integration_user'
        assert test_creds['password'] == 'integration_pass'
        
        # Test API key method
        api_key = config_manager.get_api_key()
        assert api_key == 'integration_api_key'
        
        # Test boolean methods
        assert config_manager.is_ssl_verification_enabled() is True
        assert config_manager.is_https_only() is True
        assert config_manager.should_mask_sensitive_data() is True
        assert config_manager.should_auto_cleanup_data() is True
    
    def test_config_manager_no_credentials(self):
        """Test ConfigManager behavior when no credentials are available."""
        config_manager = ConfigManager(self.temp_dir, 'development')
        
        assert config_manager.get_test_credentials() is None
        assert config_manager.get_admin_credentials() is None
        assert config_manager.get_api_key() is None
    
    @patch.dict(os.environ, {
        'TEST_USERNAME': 'summary_user',
        'API_KEY': 'summary_api_key',
        'SSL_VERIFY': 'false'
    })
    def test_config_summary_includes_security(self):
        """Test that configuration summary includes security settings."""
        config_manager = ConfigManager(self.temp_dir, 'development')
        
        summary = config_manager.get_config_summary()
        
        assert 'security_settings' in summary
        security_settings = summary['security_settings']
        
        assert security_settings['has_test_credentials'] is False  # Missing password
        assert security_settings['has_admin_credentials'] is False
        assert security_settings['has_api_key'] is True
        assert security_settings['ssl_verify'] is False
        assert security_settings['https_only'] is True
        assert security_settings['mask_sensitive_data'] is True
        assert security_settings['auto_cleanup_data'] is True


class TestSecurityConfigEdgeCases:
    """Test cases for SecurityConfig edge cases and error conditions."""
    
    def test_partial_credentials(self):
        """Test behavior with partial credentials."""
        config = SecurityConfig()
        
        # Only username, no password
        config.test_username = 'user_only'
        assert not config.has_credentials()
        
        # Only password, no username
        config.test_username = None
        config.test_password = 'pass_only'
        assert not config.has_credentials()
        
        # Both username and password
        config.test_username = 'complete_user'
        config.test_password = 'complete_pass'
        assert config.has_credentials()
    
    def test_empty_environment_variables(self):
        """Test behavior with empty environment variables."""
        os.environ['TEST_USERNAME'] = ''
        os.environ['API_KEY'] = ''
        
        config = SecurityConfig()
        
        # Empty strings should be treated as None
        assert config.test_username == ''
        assert config.api_key == ''
        assert not config.has_credentials()  # Empty username
        assert not config.has_api_key()  # Empty API key
    
    def test_database_url_edge_cases(self):
        """Test database URL parsing edge cases."""
        config = SecurityConfig()
        
        # URL without credentials
        config.database_url = 'sqlite:///simple.db'
        db_config = config.get_database_config()
        assert db_config['scheme'] == 'sqlite'
        
        # URL with special characters
        config.database_url = 'postgresql://user%40domain:p%40ss@localhost/db'
        masked = config._mask_database_url(config.database_url)
        assert 'postgresql://***:***@localhost/db' == masked
    
    def test_security_config_reload(self):
        """Test SecurityConfig behavior on reload."""
        # Initial config
        os.environ['TEST_USERNAME'] = 'initial_user'
        config = SecurityConfig()
        assert config.test_username == 'initial_user'
        
        # Change environment and create new config
        os.environ['TEST_USERNAME'] = 'updated_user'
        new_config = SecurityConfig()
        assert new_config.test_username == 'updated_user'
        
        # Original config should remain unchanged
        assert config.test_username == 'initial_user'