"""
테스트 헬퍼 클래스들

이 모듈은 테스트 작성을 위한 기본 클래스들과 공통 기능을 제공합니다.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.core.config import ConfigManager
from src.core.logging import get_logger
from src.pages.base_page import BasePage


class BaseTestCase:
    """
    모든 테스트의 기본 클래스
    
    공통적으로 사용되는 설정과 유틸리티 메서드를 제공합니다.
    """
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.test_start_time = time.time()
        self.test_data = {}
        self.cleanup_tasks = []
        
    def teardown_method(self):
        """각 테스트 메서드 실행 후 정리"""
        # 정리 작업 실행
        for cleanup_task in reversed(self.cleanup_tasks):
            try:
                cleanup_task()
            except Exception as e:
                print(f"Cleanup task failed: {e}")
        
        # 테스트 실행 시간 기록
        execution_time = time.time() - self.test_start_time
        if execution_time > 5.0:  # 5초 이상 걸린 테스트 경고
            print(f"Warning: Test took {execution_time:.2f} seconds")
    
    def add_cleanup(self, cleanup_func):
        """정리 작업 추가"""
        self.cleanup_tasks.append(cleanup_func)
    
    def set_test_data(self, key: str, value: Any):
        """테스트 데이터 설정"""
        self.test_data[key] = value
    
    def get_test_data(self, key: str, default: Any = None):
        """테스트 데이터 가져오기"""
        return self.test_data.get(key, default)
    
    @contextmanager
    def assert_execution_time(self, max_seconds: float):
        """실행 시간 검증 컨텍스트 매니저"""
        start_time = time.time()
        yield
        execution_time = time.time() - start_time
        assert execution_time <= max_seconds, f"Execution took {execution_time:.2f}s, expected <= {max_seconds}s"
    
    @contextmanager
    def assert_no_exceptions(self, allowed_exceptions: tuple = ()):
        """예외 발생하지 않음을 검증하는 컨텍스트 매니저"""
        try:
            yield
        except allowed_exceptions:
            pass  # 허용된 예외는 무시
        except Exception as e:
            pytest.fail(f"Unexpected exception occurred: {type(e).__name__}: {e}")
    
    def create_temp_file(self, content: str = "", suffix: str = ".tmp") -> Path:
        """임시 파일 생성 (자동 정리됨)"""
        import tempfile
        temp_file = Path(tempfile.mktemp(suffix=suffix))
        temp_file.write_text(content)
        self.add_cleanup(lambda: temp_file.unlink() if temp_file.exists() else None)
        return temp_file


class PageTestCase(BaseTestCase):
    """
    페이지 객체 테스트를 위한 기본 클래스
    
    페이지 객체 테스트에 필요한 공통 Mock과 설정을 제공합니다.
    """
    
    def setup_method(self):
        """페이지 테스트 설정"""
        super().setup_method()
        
        # Mock 객체들 생성
        self.mock_driver = Mock(spec=WebDriver)
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger = Mock()
        self.mock_retry_manager = Mock()
        
        # 기본 Mock 설정
        self.setup_mock_config()
        self.setup_mock_driver()
        self.setup_mock_logger()
        
        # 패치 설정
        self.config_patch = patch('src.core.config.get_config_manager', return_value=self.mock_config_manager)
        self.logger_patch = patch('src.core.logging.get_logger', return_value=self.mock_logger)
        self.retry_patch = patch('src.core.retry_manager.SmartRetryManager', return_value=self.mock_retry_manager)
        
        # 패치 시작
        self.config_patch.start()
        self.logger_patch.start()
        self.retry_patch.start()
        
        # 정리 작업 등록
        self.add_cleanup(self.config_patch.stop)
        self.add_cleanup(self.logger_patch.stop)
        self.add_cleanup(self.retry_patch.stop)
    
    def setup_mock_config(self):
        """ConfigManager Mock 설정"""
        self.mock_config_manager.get_base_url.return_value = "http://test.example.com"
        self.mock_config_manager.get_timeout.return_value = 10
        self.mock_config_manager.get_screenshot_dir.return_value = Path("screenshots")
        self.mock_config_manager.get_browser_config.return_value = {
            'browser': 'chrome',
            'headless': True,
            'window_size': (1920, 1080)
        }
    
    def setup_mock_driver(self):
        """WebDriver Mock 설정"""
        self.mock_driver.current_url = "http://test.example.com"
        self.mock_driver.title = "Test Page"
        self.mock_driver.page_source = "<html><body>Test Content</body></html>"
        self.mock_driver.get_window_size.return_value = {'width': 1920, 'height': 1080}
        self.mock_driver.get_cookies.return_value = []
        
        # JavaScript 실행 Mock
        self.mock_driver.execute_script.return_value = "complete"
    
    def setup_mock_logger(self):
        """Logger Mock 설정"""
        self.mock_logger.debug = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.warning = Mock()
        self.mock_logger.error = Mock()
        self.mock_logger.critical = Mock()
    
    def create_mock_element(self, 
                           tag_name: str = "div",
                           text: str = "Test Element",
                           attributes: Dict[str, str] = None,
                           is_displayed: bool = True,
                           is_enabled: bool = True,
                           is_selected: bool = False) -> Mock:
        """Mock WebElement 생성"""
        element = Mock(spec=WebElement)
        element.tag_name = tag_name
        element.text = text
        element.is_displayed.return_value = is_displayed
        element.is_enabled.return_value = is_enabled
        element.is_selected.return_value = is_selected
        
        # 속성 설정
        if attributes:
            element.get_attribute = Mock(side_effect=lambda attr: attributes.get(attr))
        else:
            element.get_attribute.return_value = None
        
        # 기본 액션 Mock
        element.click = Mock()
        element.send_keys = Mock()
        element.clear = Mock()
        element.submit = Mock()
        
        return element
    
    def setup_element_finding(self, locator: tuple, element: Mock = None, found: bool = True):
        """요소 찾기 Mock 설정"""
        if not element and found:
            element = self.create_mock_element()
        
        if found:
            self.mock_driver.find_element.return_value = element
            self.mock_driver.find_elements.return_value = [element]
        else:
            from selenium.common.exceptions import NoSuchElementException
            self.mock_driver.find_element.side_effect = NoSuchElementException()
            self.mock_driver.find_elements.return_value = []
        
        return element
    
    def assert_element_interaction(self, element: Mock, action: str, *args, **kwargs):
        """요소 상호작용 검증"""
        action_method = getattr(element, action)
        if args or kwargs:
            action_method.assert_called_with(*args, **kwargs)
        else:
            action_method.assert_called()
    
    def assert_driver_action(self, action: str, *args, **kwargs):
        """드라이버 액션 검증"""
        action_method = getattr(self.mock_driver, action)
        if args or kwargs:
            action_method.assert_called_with(*args, **kwargs)
        else:
            action_method.assert_called()
    
    def assert_log_message(self, level: str, message_contains: str):
        """로그 메시지 검증"""
        log_method = getattr(self.mock_logger, level.lower())
        calls = log_method.call_args_list
        
        found = any(message_contains in str(call) for call in calls)
        assert found, f"Expected log message containing '{message_contains}' at level '{level}'"


class DriverTestCase(BaseTestCase):
    """
    드라이버 관련 테스트를 위한 기본 클래스
    
    WebDriver 테스트에 필요한 공통 설정과 유틸리티를 제공합니다.
    """
    
    def setup_method(self):
        """드라이버 테스트 설정"""
        super().setup_method()
        
        # 드라이버 관련 Mock 설정
        self.mock_chrome_driver = Mock()
        self.mock_firefox_driver = Mock()
        self.mock_edge_driver = Mock()
        
        # WebDriverManager Mock
        self.mock_chrome_manager = Mock()
        self.mock_firefox_manager = Mock()
        self.mock_edge_manager = Mock()
        
        # 드라이버 생성 Mock 설정
        self.setup_driver_mocks()
    
    def setup_driver_mocks(self):
        """드라이버 Mock 설정"""
        # Chrome 드라이버 Mock
        self.mock_chrome_driver.name = "chrome"
        self.mock_chrome_driver.capabilities = {"browserName": "chrome"}
        self.mock_chrome_driver.quit = Mock()
        
        # Firefox 드라이버 Mock
        self.mock_firefox_driver.name = "firefox"
        self.mock_firefox_driver.capabilities = {"browserName": "firefox"}
        self.mock_firefox_driver.quit = Mock()
        
        # Edge 드라이버 Mock
        self.mock_edge_driver.name = "MicrosoftEdge"
        self.mock_edge_driver.capabilities = {"browserName": "MicrosoftEdge"}
        self.mock_edge_driver.quit = Mock()
    
    @contextmanager
    def mock_webdriver_manager(self):
        """WebDriverManager Mock 컨텍스트"""
        with patch('webdriver_manager.chrome.ChromeDriverManager') as chrome_mgr, \
             patch('webdriver_manager.firefox.GeckoDriverManager') as firefox_mgr, \
             patch('webdriver_manager.microsoft.EdgeChromiumDriverManager') as edge_mgr:
            
            chrome_mgr.return_value = self.mock_chrome_manager
            firefox_mgr.return_value = self.mock_firefox_manager
            edge_mgr.return_value = self.mock_edge_manager
            
            self.mock_chrome_manager.install.return_value = "/path/to/chromedriver"
            self.mock_firefox_manager.install.return_value = "/path/to/geckodriver"
            self.mock_edge_manager.install.return_value = "/path/to/edgedriver"
            
            yield
    
    @contextmanager
    def mock_selenium_drivers(self):
        """Selenium 드라이버 Mock 컨텍스트"""
        with patch('selenium.webdriver.Chrome') as chrome, \
             patch('selenium.webdriver.Firefox') as firefox, \
             patch('selenium.webdriver.Edge') as edge:
            
            chrome.return_value = self.mock_chrome_driver
            firefox.return_value = self.mock_firefox_driver
            edge.return_value = self.mock_edge_driver
            
            yield


class ConfigTestCase(BaseTestCase):
    """
    설정 관련 테스트를 위한 기본 클래스
    
    ConfigManager 테스트에 필요한 공통 설정과 유틸리티를 제공합니다.
    """
    
    def setup_method(self):
        """설정 테스트 설정"""
        super().setup_method()
        
        # 환경 변수 백업
        import os
        self.original_env = os.environ.copy()
        self.add_cleanup(self.restore_environment)
        
        # 임시 설정 파일들
        self.temp_config_files = []
    
    def restore_environment(self):
        """환경 변수 복원"""
        import os
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def set_env_var(self, key: str, value: str):
        """환경 변수 설정"""
        import os
        os.environ[key] = value
    
    def create_temp_config(self, config_data: Dict[str, Any], format: str = "yaml") -> Path:
        """임시 설정 파일 생성"""
        import tempfile
        import yaml
        import json
        
        if format.lower() == "yaml":
            content = yaml.dump(config_data, default_flow_style=False)
            suffix = ".yml"
        elif format.lower() == "json":
            content = json.dumps(config_data, indent=2)
            suffix = ".json"
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        temp_file = self.create_temp_file(content, suffix)
        self.temp_config_files.append(temp_file)
        return temp_file
    
    def create_sample_config(self) -> Dict[str, Any]:
        """샘플 설정 데이터 생성"""
        return {
            'browser': {
                'default': 'chrome',
                'headless': True,
                'window_size': '1920x1080',
                'timeout': 30
            },
            'test': {
                'base_url': 'http://test.example.com',
                'parallel_workers': 4,
                'screenshot_on_failure': True
            },
            'reporting': {
                'html_report': True,
                'allure_report': False,
                'output_dir': 'reports'
            }
        }
    
    @contextmanager
    def temporary_config_manager(self, config_data: Dict[str, Any] = None):
        """임시 ConfigManager 컨텍스트"""
        if config_data is None:
            config_data = self.create_sample_config()
        
        config_file = self.create_temp_config(config_data)
        
        # ConfigManager 초기화 Mock
        with patch('src.core.config.ConfigManager._load_config_file') as mock_load:
            mock_load.return_value = config_data
            
            from src.core.config import ConfigManager
            config_manager = ConfigManager(str(config_file))
            
            yield config_manager


class APITestCase(BaseTestCase):
    """
    API 테스트를 위한 기본 클래스
    
    API 테스트에 필요한 공통 설정과 유틸리티를 제공합니다.
    """
    
    def setup_method(self):
        """API 테스트 설정"""
        super().setup_method()
        
        # requests Mock 설정
        self.mock_response = Mock()
        self.setup_mock_response()
    
    def setup_mock_response(self, 
                           status_code: int = 200,
                           json_data: Dict[str, Any] = None,
                           text: str = "OK",
                           headers: Dict[str, str] = None):
        """Mock Response 설정"""
        self.mock_response.status_code = status_code
        self.mock_response.text = text
        self.mock_response.json.return_value = json_data or {}
        self.mock_response.headers = headers or {'Content-Type': 'application/json'}
        self.mock_response.raise_for_status = Mock()
        
        if status_code >= 400:
            from requests.exceptions import HTTPError
            self.mock_response.raise_for_status.side_effect = HTTPError()
    
    @contextmanager
    def mock_requests(self, method: str = "get"):
        """requests Mock 컨텍스트"""
        with patch(f'requests.{method.lower()}') as mock_method:
            mock_method.return_value = self.mock_response
            yield mock_method
    
    def assert_api_call(self, mock_method: Mock, url: str, **kwargs):
        """API 호출 검증"""
        mock_method.assert_called_once()
        call_args = mock_method.call_args
        
        # URL 검증
        assert call_args[0][0] == url, f"Expected URL {url}, got {call_args[0][0]}"
        
        # 추가 파라미터 검증
        for key, expected_value in kwargs.items():
            actual_value = call_args[1].get(key)
            assert actual_value == expected_value, f"Expected {key}={expected_value}, got {actual_value}"


class PerformanceTestCase(BaseTestCase):
    """
    성능 테스트를 위한 기본 클래스
    
    성능 측정과 검증에 필요한 유틸리티를 제공합니다.
    """
    
    def setup_method(self):
        """성능 테스트 설정"""
        super().setup_method()
        self.performance_metrics = {}
    
    @contextmanager
    def measure_time(self, metric_name: str):
        """실행 시간 측정 컨텍스트"""
        start_time = time.time()
        yield
        end_time = time.time()
        self.performance_metrics[metric_name] = end_time - start_time
    
    def assert_performance(self, metric_name: str, max_time: float):
        """성능 검증"""
        actual_time = self.performance_metrics.get(metric_name)
        assert actual_time is not None, f"Metric '{metric_name}' not found"
        assert actual_time <= max_time, f"Performance test failed: {actual_time:.3f}s > {max_time}s"
    
    def get_performance_report(self) -> Dict[str, float]:
        """성능 리포트 반환"""
        return self.performance_metrics.copy()


# 편의 함수들
def create_test_suite(*test_classes):
    """테스트 스위트 생성"""
    import unittest
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_test_with_timeout(test_func, timeout_seconds: float = 30.0):
    """타임아웃이 있는 테스트 실행"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")
    
    # 타임아웃 설정
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout_seconds))
    
    try:
        result = test_func()
        return result
    finally:
        signal.alarm(0)  # 타임아웃 해제


def parametrize_test(test_func, parameters: List[tuple]):
    """테스트 파라미터화"""
    def wrapper():
        results = []
        for params in parameters:
            try:
                result = test_func(*params)
                results.append(('PASS', params, result))
            except Exception as e:
                results.append(('FAIL', params, str(e)))
        return results
    
    return wrapper