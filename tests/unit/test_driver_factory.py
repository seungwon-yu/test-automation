"""
DriverFactory 클래스 단위 테스트

이 모듈은 DriverFactory 클래스와 관련 기능들의 단위 테스트를 제공합니다.
Mock을 활용하여 실제 브라우저 드라이버를 생성하지 않고 테스트합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from src.core.driver_factory import (
    DriverFactory, 
    DriverConfig, 
    BrowserType,
    create_chrome_driver,
    create_firefox_driver,
    create_driver_from_config
)
from src.core.exceptions import DriverInitializationException, ConfigurationException


class TestBrowserType:
    """BrowserType Enum 테스트"""
    
    def test_browser_type_values(self):
        """브라우저 타입 값 확인"""
        assert BrowserType.CHROME.value == "chrome"
        assert BrowserType.FIREFOX.value == "firefox"
        assert BrowserType.SAFARI.value == "safari"
        assert BrowserType.EDGE.value == "edge"
    
    def test_browser_type_from_string(self):
        """문자열로부터 브라우저 타입 생성"""
        assert BrowserType("chrome") == BrowserType.CHROME
        assert BrowserType("firefox") == BrowserType.FIREFOX
        assert BrowserType("safari") == BrowserType.SAFARI
        assert BrowserType("edge") == BrowserType.EDGE


class TestDriverConfig:
    """DriverConfig 데이터클래스 테스트"""
    
    def test_driver_config_default_values(self):
        """기본값 확인"""
        config = DriverConfig(browser=BrowserType.CHROME)
        
        assert config.browser == BrowserType.CHROME
        assert config.headless is False
        assert config.window_size == (1920, 1080)
        assert config.timeout == 30
        assert config.proxy is None
        assert config.user_agent is None
        assert config.download_dir is None
        assert config.disable_images is False
        assert config.disable_javascript is False
        assert config.incognito is False
        assert config.remote_url is None
        assert config.capabilities is None
    
    def test_driver_config_custom_values(self):
        """사용자 정의 값 설정"""
        config = DriverConfig(
            browser=BrowserType.FIREFOX,
            headless=True,
            window_size=(1366, 768),
            timeout=60,
            proxy="http://proxy:8080",
            user_agent="Custom User Agent",
            download_dir="/tmp/downloads",
            disable_images=True,
            disable_javascript=True,
            incognito=True,
            remote_url="http://selenium-grid:4444/wd/hub",
            capabilities={"version": "latest"}
        )
        
        assert config.browser == BrowserType.FIREFOX
        assert config.headless is True
        assert config.window_size == (1366, 768)
        assert config.timeout == 60
        assert config.proxy == "http://proxy:8080"
        assert config.user_agent == "Custom User Agent"
        assert config.download_dir == "/tmp/downloads"
        assert config.disable_images is True
        assert config.disable_javascript is True
        assert config.incognito is True
        assert config.remote_url == "http://selenium-grid:4444/wd/hub"
        assert config.capabilities == {"version": "latest"}


class TestDriverFactory:
    """DriverFactory 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.factory = DriverFactory()
    
    def test_factory_initialization(self):
        """팩토리 초기화 테스트"""
        assert self.factory is not None
        assert hasattr(self.factory, 'logger')
        assert hasattr(self.factory, '_driver_cache')
    
    @patch('src.core.driver_factory.webdriver.Chrome')
    @patch('src.core.driver_factory.ChromeDriverManager')
    def test_create_chrome_driver_basic(self, mock_chrome_manager, mock_chrome):
        """기본 Chrome 드라이버 생성 테스트"""
        # Mock 설정
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        config = DriverConfig(browser=BrowserType.CHROME)
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_chrome.assert_called_once()
    
    @patch('src.core.driver_factory.webdriver.Chrome')
    @patch('src.core.driver_factory.ChromeDriverManager')
    def test_create_chrome_driver_headless(self, mock_chrome_manager, mock_chrome):
        """헤드리스 Chrome 드라이버 생성 테스트"""
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        config = DriverConfig(browser=BrowserType.CHROME, headless=True)
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        # 헤드리스 옵션이 설정되었는지 확인
        args, kwargs = mock_chrome.call_args
        options = kwargs['options']
        assert '--headless' in options.arguments
    
    @patch('src.core.driver_factory.webdriver.Firefox')
    @patch('src.core.driver_factory.GeckoDriverManager')
    def test_create_firefox_driver_basic(self, mock_gecko_manager, mock_firefox):
        """기본 Firefox 드라이버 생성 테스트"""
        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"
        mock_driver = Mock()
        mock_firefox.return_value = mock_driver
        
        config = DriverConfig(browser=BrowserType.FIREFOX)
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_firefox.assert_called_once()
    
    @patch('src.core.driver_factory.webdriver.Firefox')
    @patch('src.core.driver_factory.GeckoDriverManager')
    def test_create_firefox_driver_with_options(self, mock_gecko_manager, mock_firefox):
        """옵션이 설정된 Firefox 드라이버 생성 테스트"""
        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"
        mock_driver = Mock()
        mock_firefox.return_value = mock_driver
        
        config = DriverConfig(
            browser=BrowserType.FIREFOX,
            headless=True,
            proxy="http://proxy:8080",
            user_agent="Test Agent"
        )
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_firefox.assert_called_once()
    
    @patch('src.core.driver_factory.webdriver.Safari')
    @patch('src.core.driver_factory.os.name', 'posix')
    def test_create_safari_driver_on_macos(self, mock_safari):
        """macOS에서 Safari 드라이버 생성 테스트"""
        mock_driver = Mock()
        mock_safari.return_value = mock_driver
        
        config = DriverConfig(browser=BrowserType.SAFARI)
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_safari.assert_called_once()
    
    @patch('src.core.driver_factory.os.name', 'nt')
    def test_create_safari_driver_on_windows_fails(self):
        """Windows에서 Safari 드라이버 생성 실패 테스트"""
        config = DriverConfig(browser=BrowserType.SAFARI)
        
        with pytest.raises(DriverInitializationException) as exc_info:
            self.factory.create_driver(config)
        
        assert "Safari driver is only supported on macOS" in str(exc_info.value)
    
    @patch('src.core.driver_factory.webdriver.Edge')
    @patch('src.core.driver_factory.EdgeChromiumDriverManager')
    def test_create_edge_driver_basic(self, mock_edge_manager, mock_edge):
        """기본 Edge 드라이버 생성 테스트"""
        mock_edge_manager.return_value.install.return_value = "/path/to/edgedriver"
        mock_driver = Mock()
        mock_edge.return_value = mock_driver
        
        config = DriverConfig(browser=BrowserType.EDGE)
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_edge.assert_called_once()
    
    @patch('src.core.driver_factory.webdriver.Remote')
    def test_create_remote_driver(self, mock_remote):
        """원격 드라이버 생성 테스트"""
        mock_driver = Mock()
        mock_remote.return_value = mock_driver
        
        config = DriverConfig(
            browser=BrowserType.CHROME,
            remote_url="http://selenium-grid:4444/wd/hub"
        )
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        mock_remote.assert_called_once()
        
        # 호출 인자 확인
        args, kwargs = mock_remote.call_args
        assert kwargs['command_executor'] == "http://selenium-grid:4444/wd/hub"
        assert 'desired_capabilities' in kwargs
    
    @patch('src.core.driver_factory.webdriver.Remote')
    def test_create_remote_driver_with_capabilities(self, mock_remote):
        """사용자 정의 capabilities를 가진 원격 드라이버 생성 테스트"""
        mock_driver = Mock()
        mock_remote.return_value = mock_driver
        
        custom_capabilities = {"version": "latest", "platform": "LINUX"}
        config = DriverConfig(
            browser=BrowserType.FIREFOX,
            remote_url="http://selenium-grid:4444/wd/hub",
            capabilities=custom_capabilities
        )
        driver = self.factory.create_driver(config)
        
        assert driver == mock_driver
        
        # capabilities가 병합되었는지 확인
        args, kwargs = mock_remote.call_args
        capabilities = kwargs['desired_capabilities']
        assert capabilities['version'] == "latest"
        assert capabilities['platform'] == "LINUX"
    
    def test_unsupported_browser_raises_exception(self):
        """지원하지 않는 브라우저 타입 예외 테스트"""
        # 잘못된 브라우저 타입을 직접 생성할 수 없으므로 Mock 사용
        with patch.object(BrowserType, '__new__') as mock_browser:
            mock_browser.return_value = Mock()
            mock_browser.return_value.value = "unsupported"
            
            config = DriverConfig(browser=mock_browser.return_value)
            
            with pytest.raises(ConfigurationException):
                self.factory.create_driver(config)
    
    @patch('src.core.driver_factory.webdriver.Chrome')
    @patch('src.core.driver_factory.ChromeDriverManager')
    def test_driver_creation_failure_raises_exception(self, mock_chrome_manager, mock_chrome):
        """드라이버 생성 실패 시 예외 발생 테스트"""
        mock_chrome_manager.return_value.install.side_effect = Exception("Driver download failed")
        
        config = DriverConfig(browser=BrowserType.CHROME)
        
        with pytest.raises(DriverInitializationException) as exc_info:
            self.factory.create_driver(config)
        
        assert "Failed to create chrome driver" in str(exc_info.value)
    
    def test_create_config_from_string(self):
        """문자열로부터 DriverConfig 생성 테스트"""
        config = DriverFactory.create_config("chrome", headless=True, timeout=60)
        
        assert config.browser == BrowserType.CHROME
        assert config.headless is True
        assert config.timeout == 60
    
    def test_create_config_invalid_browser(self):
        """잘못된 브라우저 이름으로 config 생성 시 예외 테스트"""
        with pytest.raises(ConfigurationException) as exc_info:
            DriverFactory.create_config("invalid_browser")
        
        assert "Unsupported browser: invalid_browser" in str(exc_info.value)
    
    def test_quit_driver_success(self):
        """드라이버 정상 종료 테스트"""
        mock_driver = Mock()
        
        self.factory.quit_driver(mock_driver)
        
        mock_driver.quit.assert_called_once()
    
    def test_quit_driver_with_exception(self):
        """드라이버 종료 시 예외 발생 테스트"""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Quit failed")
        
        # 예외가 발생해도 메서드가 정상 완료되어야 함
        self.factory.quit_driver(mock_driver)
        
        mock_driver.quit.assert_called_once()
    
    def test_quit_driver_with_none(self):
        """None 드라이버 종료 테스트"""
        # None을 전달해도 예외가 발생하지 않아야 함
        self.factory.quit_driver(None)


class TestConvenienceFunctions:
    """편의 함수들 테스트"""
    
    @patch('src.core.driver_factory.DriverFactory.create_driver')
    def test_create_chrome_driver_function(self, mock_create_driver):
        """create_chrome_driver 편의 함수 테스트"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver
        
        driver = create_chrome_driver(headless=True, window_size=(1366, 768))
        
        assert driver == mock_driver
        mock_create_driver.assert_called_once()
        
        # 전달된 config 확인
        args, kwargs = mock_create_driver.call_args
        config = args[0]
        assert config.browser == BrowserType.CHROME
        assert config.headless is True
        assert config.window_size == (1366, 768)
    
    @patch('src.core.driver_factory.DriverFactory.create_driver')
    def test_create_firefox_driver_function(self, mock_create_driver):
        """create_firefox_driver 편의 함수 테스트"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver
        
        driver = create_firefox_driver(headless=False, window_size=(1920, 1080))
        
        assert driver == mock_driver
        mock_create_driver.assert_called_once()
        
        # 전달된 config 확인
        args, kwargs = mock_create_driver.call_args
        config = args[0]
        assert config.browser == BrowserType.FIREFOX
        assert config.headless is False
        assert config.window_size == (1920, 1080)
    
    @patch('src.core.driver_factory.DriverFactory.create_driver')
    def test_create_driver_from_config_dict(self, mock_create_driver):
        """create_driver_from_config 함수 테스트"""
        mock_driver = Mock()
        mock_create_driver.return_value = mock_driver
        
        config_dict = {
            'browser': 'firefox',
            'headless': True,
            'timeout': 45,
            'proxy': 'http://proxy:8080'
        }
        
        driver = create_driver_from_config(config_dict)
        
        assert driver == mock_driver
        mock_create_driver.assert_called_once()
        
        # 전달된 config 확인
        args, kwargs = mock_create_driver.call_args
        config = args[0]
        assert config.browser == BrowserType.FIREFOX
        assert config.headless is True
        assert config.timeout == 45
        assert config.proxy == 'http://proxy:8080'


class TestDriverFactoryIntegration:
    """DriverFactory 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.factory = DriverFactory()
    
    @patch('src.core.driver_factory.webdriver.Chrome')
    @patch('src.core.driver_factory.ChromeDriverManager')
    def test_full_chrome_driver_creation_flow(self, mock_chrome_manager, mock_chrome):
        """Chrome 드라이버 생성 전체 플로우 테스트"""
        # Mock 설정
        mock_chrome_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # 복잡한 설정으로 드라이버 생성
        config = DriverConfig(
            browser=BrowserType.CHROME,
            headless=True,
            window_size=(1366, 768),
            timeout=45,
            proxy="http://proxy:8080",
            user_agent="Test User Agent",
            download_dir="/tmp/test_downloads",
            disable_images=True,
            incognito=True
        )
        
        driver = self.factory.create_driver(config)
        
        # 결과 검증
        assert driver == mock_driver
        mock_chrome.assert_called_once()
        
        # 옵션 검증
        args, kwargs = mock_chrome.call_args
        options = kwargs['options']
        
        # 주요 옵션들이 설정되었는지 확인
        assert '--headless' in options.arguments
        assert '--window-size=1366,768' in options.arguments
        assert '--proxy-server=http://proxy:8080' in options.arguments
        assert '--user-agent=Test User Agent' in options.arguments
        assert '--incognito' in options.arguments
    
    def test_config_validation_and_error_handling(self):
        """설정 검증 및 오류 처리 테스트"""
        # 잘못된 브라우저 타입으로 config 생성 시도
        with pytest.raises(ConfigurationException):
            DriverFactory.create_config("invalid_browser")
        
        # 정상적인 config 생성
        config = DriverFactory.create_config("chrome", headless=True)
        assert config.browser == BrowserType.CHROME
        assert config.headless is True