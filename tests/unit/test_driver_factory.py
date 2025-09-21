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
    RemoteDriverConfig,
    RemoteDriverManager,
    DriverPool,
    DriverPoolConfig,
    create_chrome_driver,
    create_firefox_driver,
    create_driver_from_config,
    create_remote_driver,
    create_docker_driver,
    create_grid_driver
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


class TestRemoteDriverConfig:
    """RemoteDriverConfig 데이터클래스 테스트"""
    
    def test_remote_driver_config_default_values(self):
        """기본값 확인"""
        config = RemoteDriverConfig(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser=BrowserType.CHROME
        )
        
        assert config.hub_url == "http://selenium-grid:4444/wd/hub"
        assert config.browser == BrowserType.CHROME
        assert config.browser_version == "latest"
        assert config.platform == "ANY"
        assert config.max_sessions == 5
        assert config.session_timeout == 300
        assert config.connection_timeout == 60
        assert config.retry_attempts == 3
        assert config.retry_delay == 2
        assert config.capabilities == {}
        assert config.docker_config == {}
    
    def test_remote_driver_config_custom_values(self):
        """사용자 정의 값 설정"""
        config = RemoteDriverConfig(
            hub_url="http://custom-grid:4444/wd/hub",
            browser=BrowserType.FIREFOX,
            browser_version="91.0",
            platform="LINUX",
            max_sessions=10,
            session_timeout=600,
            connection_timeout=120,
            retry_attempts=5,
            retry_delay=3,
            capabilities={"version": "91.0"},
            docker_config={"network": "selenium"}
        )
        
        assert config.hub_url == "http://custom-grid:4444/wd/hub"
        assert config.browser == BrowserType.FIREFOX
        assert config.browser_version == "91.0"
        assert config.platform == "LINUX"
        assert config.max_sessions == 10
        assert config.session_timeout == 600
        assert config.connection_timeout == 120
        assert config.retry_attempts == 5
        assert config.retry_delay == 3
        assert config.capabilities == {"version": "91.0"}
        assert config.docker_config == {"network": "selenium"}


class TestDriverPoolConfig:
    """DriverPoolConfig 데이터클래스 테스트"""
    
    def test_driver_pool_config_default_values(self):
        """기본값 확인"""
        config = DriverPoolConfig()
        
        assert config.max_pool_size == 10
        assert config.min_pool_size == 2
        assert config.idle_timeout == 300
        assert config.max_wait_time == 60
        assert config.health_check_interval == 30
        assert config.auto_cleanup is True
    
    def test_driver_pool_config_custom_values(self):
        """사용자 정의 값 설정"""
        config = DriverPoolConfig(
            max_pool_size=20,
            min_pool_size=5,
            idle_timeout=600,
            max_wait_time=120,
            health_check_interval=60,
            auto_cleanup=False
        )
        
        assert config.max_pool_size == 20
        assert config.min_pool_size == 5
        assert config.idle_timeout == 600
        assert config.max_wait_time == 120
        assert config.health_check_interval == 60
        assert config.auto_cleanup is False


class TestRemoteDriverManager:
    """RemoteDriverManager 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.remote_config = RemoteDriverConfig(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser=BrowserType.CHROME
        )
        self.manager = RemoteDriverManager(self.remote_config)
    
    def test_manager_initialization(self):
        """매니저 초기화 테스트"""
        assert self.manager.config == self.remote_config
        assert hasattr(self.manager, 'logger')
        assert hasattr(self.manager, '_active_sessions')
        assert hasattr(self.manager, '_session_lock')
    
    @patch('src.core.driver_factory.webdriver.Remote')
    def test_create_remote_driver_success(self, mock_remote):
        """원격 드라이버 생성 성공 테스트"""
        mock_driver = Mock()
        mock_driver.session_id = "test_session_123"
        mock_remote.return_value = mock_driver
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        driver = self.manager.create_remote_driver(driver_config)
        
        assert driver == mock_driver
        mock_remote.assert_called_once()
        
        # 세션이 관리되는지 확인
        assert "test_session_123" in self.manager._active_sessions
    
    @patch('src.core.driver_factory.webdriver.Remote')
    def test_create_remote_driver_with_retry(self, mock_remote):
        """재시도 로직 테스트"""
        mock_driver = Mock()
        mock_driver.session_id = "test_session_123"
        
        # 첫 번째 시도는 실패, 두 번째 시도는 성공
        mock_remote.side_effect = [Exception("Connection failed"), mock_driver]
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        driver = self.manager.create_remote_driver(driver_config)
        
        assert driver == mock_driver
        assert mock_remote.call_count == 2
    
    @patch('src.core.driver_factory.webdriver.Remote')
    def test_create_remote_driver_all_retries_fail(self, mock_remote):
        """모든 재시도 실패 테스트"""
        mock_remote.side_effect = Exception("Connection failed")
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        
        with pytest.raises(DriverInitializationException):
            self.manager.create_remote_driver(driver_config)
        
        assert mock_remote.call_count == self.remote_config.retry_attempts
    
    def test_build_capabilities_chrome(self):
        """Chrome capabilities 구성 테스트"""
        driver_config = DriverConfig(
            browser=BrowserType.CHROME,
            headless=True,
            window_size=(1366, 768)
        )
        
        capabilities = self.manager._build_capabilities(driver_config)
        
        assert capabilities['browserName'] == 'chrome'
        assert capabilities['browserVersion'] == 'latest'
        assert capabilities['platformName'] == 'ANY'
        assert 'goog:chromeOptions' in capabilities
        
        chrome_options = capabilities['goog:chromeOptions']
        assert '--headless' in chrome_options['args']
        assert '--window-size=1366,768' in chrome_options['args']
    
    def test_build_capabilities_firefox(self):
        """Firefox capabilities 구성 테스트"""
        self.manager.config.browser = BrowserType.FIREFOX
        driver_config = DriverConfig(
            browser=BrowserType.FIREFOX,
            headless=True,
            proxy="http://proxy:8080"
        )
        
        capabilities = self.manager._build_capabilities(driver_config)
        
        assert capabilities['browserName'] == 'firefox'
        assert 'moz:firefoxOptions' in capabilities
        
        firefox_options = capabilities['moz:firefoxOptions']
        assert '--headless' in firefox_options['args']
        assert 'prefs' in firefox_options
    
    def test_build_docker_capabilities(self):
        """Docker capabilities 구성 테스트"""
        self.manager.config.docker_config = {
            'network': 'selenium-network',
            'volumes': {'/tmp': '/tmp'},
            'environment': {'DISPLAY': ':99'},
            'image': 'selenium/standalone-chrome:latest'
        }
        
        docker_caps = self.manager._build_docker_capabilities()
        
        assert docker_caps['se:dockerNetwork'] == 'selenium-network'
        assert docker_caps['se:dockerVolumes'] == {'/tmp': '/tmp'}
        assert docker_caps['se:dockerEnvironment'] == {'DISPLAY': ':99'}
        assert docker_caps['se:dockerImage'] == 'selenium/standalone-chrome:latest'
    
    def test_quit_session(self):
        """세션 종료 테스트"""
        mock_driver = Mock()
        session_id = "test_session_123"
        
        # 세션 추가
        self.manager._active_sessions[session_id] = mock_driver
        
        # 세션 종료
        self.manager.quit_session(session_id)
        
        mock_driver.quit.assert_called_once()
        assert session_id not in self.manager._active_sessions
    
    def test_quit_all_sessions(self):
        """모든 세션 종료 테스트"""
        mock_driver1 = Mock()
        mock_driver2 = Mock()
        
        self.manager._active_sessions["session1"] = mock_driver1
        self.manager._active_sessions["session2"] = mock_driver2
        
        self.manager.quit_all_sessions()
        
        mock_driver1.quit.assert_called_once()
        mock_driver2.quit.assert_called_once()
        assert len(self.manager._active_sessions) == 0
    
    def test_get_active_sessions(self):
        """활성 세션 목록 반환 테스트"""
        self.manager._active_sessions["session1"] = Mock()
        self.manager._active_sessions["session2"] = Mock()
        
        active_sessions = self.manager.get_active_sessions()
        
        assert len(active_sessions) == 2
        assert "session1" in active_sessions
        assert "session2" in active_sessions


class TestDriverPool:
    """DriverPool 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.factory = Mock(spec=DriverFactory)
        self.pool_config = DriverPoolConfig(
            max_pool_size=5,
            min_pool_size=1,
            auto_cleanup=False  # 테스트에서는 자동 정리 비활성화
        )
        self.pool = DriverPool(self.factory, self.pool_config)
    
    def test_pool_initialization(self):
        """풀 초기화 테스트"""
        assert self.pool.factory == self.factory
        assert self.pool.config == self.pool_config
        assert hasattr(self.pool, '_pool')
        assert hasattr(self.pool, '_active_drivers')
        assert hasattr(self.pool, '_pool_stats')
    
    @patch('src.core.driver_factory.DriverPool._is_driver_healthy')
    def test_acquire_driver_from_empty_pool(self, mock_healthy):
        """빈 풀에서 드라이버 획득 테스트"""
        mock_driver = Mock()
        self.factory.create_driver.return_value = mock_driver
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        driver, driver_id = self.pool._acquire_driver(driver_config)
        
        assert driver == mock_driver
        assert driver_id is not None
        self.factory.create_driver.assert_called_once_with(driver_config)
        assert self.pool._pool_stats['created'] == 1
        assert self.pool._pool_stats['active'] == 1
    
    @patch('src.core.driver_factory.DriverPool._is_driver_healthy')
    def test_acquire_driver_from_pool(self, mock_healthy):
        """풀에서 드라이버 재사용 테스트"""
        mock_driver = Mock()
        mock_healthy.return_value = True
        
        # 풀에 드라이버 추가
        self.pool._pool.put(mock_driver)
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        driver, driver_id = self.pool._acquire_driver(driver_config)
        
        assert driver == mock_driver
        mock_healthy.assert_called_once_with(mock_driver)
        assert self.pool._pool_stats['reused'] == 1
        assert self.pool._pool_stats['active'] == 1
    
    @patch('src.core.driver_factory.DriverPool._is_driver_healthy')
    @patch('src.core.driver_factory.DriverPool._destroy_driver')
    def test_acquire_unhealthy_driver_from_pool(self, mock_destroy, mock_healthy):
        """비정상 드라이버 처리 테스트"""
        mock_unhealthy_driver = Mock()
        mock_new_driver = Mock()
        mock_healthy.return_value = False
        self.factory.create_driver.return_value = mock_new_driver
        
        # 풀에 비정상 드라이버 추가
        self.pool._pool.put(mock_unhealthy_driver)
        
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        driver, driver_id = self.pool._acquire_driver(driver_config)
        
        assert driver == mock_new_driver
        mock_destroy.assert_called_once_with(mock_unhealthy_driver)
        self.factory.create_driver.assert_called_once_with(driver_config)
    
    def test_release_driver_to_pool(self):
        """드라이버 풀 반납 테스트"""
        mock_driver = Mock()
        driver_id = "test_driver_123"
        
        # 활성 드라이버로 추가
        self.pool._active_drivers[driver_id] = {
            'driver': mock_driver,
            'acquired_at': time.time(),
            'config': DriverConfig(browser=BrowserType.CHROME)
        }
        self.pool._pool_stats['active'] = 1
        
        with patch.object(self.pool, '_is_driver_healthy', return_value=True):
            self.pool._release_driver(mock_driver, driver_id)
        
        assert driver_id not in self.pool._active_drivers
        assert self.pool._pool_stats['active'] == 0
        assert not self.pool._pool.empty()
    
    def test_is_driver_healthy_success(self):
        """드라이버 상태 확인 성공 테스트"""
        mock_driver = Mock()
        mock_driver.current_url = "http://example.com"
        
        assert self.pool._is_driver_healthy(mock_driver) is True
    
    def test_is_driver_healthy_failure(self):
        """드라이버 상태 확인 실패 테스트"""
        mock_driver = Mock()
        mock_driver.current_url = Mock(side_effect=Exception("Driver error"))
        
        assert self.pool._is_driver_healthy(mock_driver) is False
    
    def test_destroy_driver(self):
        """드라이버 제거 테스트"""
        mock_driver = Mock()
        
        self.pool._destroy_driver(mock_driver)
        
        mock_driver.quit.assert_called_once()
        assert self.pool._pool_stats['destroyed'] == 1
    
    def test_get_pool_stats(self):
        """풀 통계 정보 테스트"""
        self.pool._pool_stats['created'] = 5
        self.pool._pool_stats['reused'] = 3
        self.pool._active_drivers['driver1'] = {}
        self.pool._active_drivers['driver2'] = {}
        
        stats = self.pool.get_pool_stats()
        
        assert stats['created'] == 5
        assert stats['reused'] == 3
        assert stats['active_drivers'] == 2
        assert 'pool_size' in stats
    
    @patch('src.core.driver_factory.DriverPool._destroy_driver')
    def test_shutdown(self, mock_destroy):
        """풀 종료 테스트"""
        mock_driver1 = Mock()
        mock_driver2 = Mock()
        mock_driver3 = Mock()
        
        # 활성 드라이버 추가
        self.pool._active_drivers['driver1'] = {'driver': mock_driver1}
        self.pool._active_drivers['driver2'] = {'driver': mock_driver2}
        
        # 풀에 드라이버 추가
        self.pool._pool.put(mock_driver3)
        
        self.pool.shutdown()
        
        # 모든 드라이버가 제거되었는지 확인
        assert mock_destroy.call_count == 3
        assert len(self.pool._active_drivers) == 0
        assert self.pool._pool.empty()


class TestDriverFactoryRemoteFeatures:
    """DriverFactory 원격 기능 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.factory = DriverFactory()
    
    @patch('src.core.driver_factory.RemoteDriverManager')
    def test_create_remote_driver_advanced(self, mock_manager_class):
        """고급 원격 드라이버 생성 테스트"""
        mock_manager = Mock()
        mock_driver = Mock()
        mock_manager.create_remote_driver.return_value = mock_driver
        mock_manager_class.return_value = mock_manager
        
        remote_config = RemoteDriverConfig(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser=BrowserType.CHROME
        )
        driver_config = DriverConfig(browser=BrowserType.CHROME)
        
        driver = self.factory.create_remote_driver_advanced(remote_config, driver_config)
        
        assert driver == mock_driver
        mock_manager_class.assert_called_once_with(remote_config)
        mock_manager.create_remote_driver.assert_called_once_with(driver_config)
    
    def test_create_driver_pool(self):
        """드라이버 풀 생성 테스트"""
        pool_config = DriverPoolConfig()
        
        pool = self.factory.create_driver_pool(pool_config, "test_pool")
        
        assert isinstance(pool, DriverPool)
        assert "test_pool" in self.factory._driver_pools
        assert self.factory.get_driver_pool("test_pool") == pool
    
    def test_get_nonexistent_driver_pool(self):
        """존재하지 않는 드라이버 풀 조회 테스트"""
        pool = self.factory.get_driver_pool("nonexistent")
        assert pool is None
    
    @patch('src.core.driver_factory.DriverPool.shutdown')
    def test_shutdown_all_pools(self, mock_shutdown):
        """모든 드라이버 풀 종료 테스트"""
        # 테스트용 풀 생성
        pool_config = DriverPoolConfig()
        self.factory.create_driver_pool(pool_config, "pool1")
        self.factory.create_driver_pool(pool_config, "pool2")
        
        self.factory.shutdown_all_pools()
        
        assert mock_shutdown.call_count == 2
        assert len(self.factory._driver_pools) == 0
    
    @patch('src.core.driver_factory.RemoteDriverManager.quit_all_sessions')
    def test_shutdown_all_remote_managers(self, mock_quit_all):
        """모든 원격 드라이버 매니저 종료 테스트"""
        # 테스트용 매니저 생성
        remote_config = RemoteDriverConfig(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser=BrowserType.CHROME
        )
        driver_config = DriverConfig(browser=BrowserType.CHROME, remote_url="http://selenium-grid:4444/wd/hub")
        
        with patch('src.core.driver_factory.RemoteDriverManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            # 원격 드라이버 생성으로 매니저 추가
            self.factory.create_remote_driver_advanced(remote_config, driver_config)
            
            self.factory.shutdown_all_remote_managers()
            
            mock_manager.quit_all_sessions.assert_called_once()
            assert len(self.factory._remote_managers) == 0


class TestRemoteDriverConvenienceFunctions:
    """원격 드라이버 편의 함수 테스트"""
    
    @patch('src.core.driver_factory.DriverFactory.create_remote_driver_advanced')
    def test_create_remote_driver_function(self, mock_create_advanced):
        """create_remote_driver 편의 함수 테스트"""
        mock_driver = Mock()
        mock_create_advanced.return_value = mock_driver
        
        driver = create_remote_driver(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser="chrome",
            headless=True,
            browser_version="91.0"
        )
        
        assert driver == mock_driver
        mock_create_advanced.assert_called_once()
        
        # 호출 인자 확인
        args, kwargs = mock_create_advanced.call_args
        remote_config, driver_config = args
        
        assert remote_config.hub_url == "http://selenium-grid:4444/wd/hub"
        assert remote_config.browser == BrowserType.CHROME
        assert remote_config.browser_version == "91.0"
        assert driver_config.headless is True
    
    @patch('src.core.driver_factory.create_remote_driver')
    def test_create_docker_driver_function(self, mock_create_remote):
        """create_docker_driver 편의 함수 테스트"""
        mock_driver = Mock()
        mock_create_remote.return_value = mock_driver
        
        driver = create_docker_driver(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser="firefox",
            docker_image="selenium/standalone-firefox:4.0.0",
            docker_network="selenium-network"
        )
        
        assert driver == mock_driver
        mock_create_remote.assert_called_once()
        
        # 호출 인자 확인
        args, kwargs = mock_create_remote.call_args
        assert kwargs['docker_config']['image'] == "selenium/standalone-firefox:4.0.0"
        assert kwargs['docker_config']['network'] == "selenium-network"
    
    @patch('src.core.driver_factory.create_remote_driver')
    def test_create_grid_driver_function(self, mock_create_remote):
        """create_grid_driver 편의 함수 테스트"""
        mock_driver = Mock()
        mock_create_remote.return_value = mock_driver
        
        driver = create_grid_driver(
            hub_url="http://selenium-grid:4444/wd/hub",
            browser="edge",
            platform="WINDOWS",
            browser_version="91.0"
        )
        
        assert driver == mock_driver
        mock_create_remote.assert_called_once()
        
        # 호출 인자 확인
        args, kwargs = mock_create_remote.call_args
        assert kwargs['platform'] == "WINDOWS"
        assert kwargs['browser_version'] == "91.0"