"""
Mock 헬퍼 함수들

이 모듈은 테스트에서 사용할 수 있는 다양한 Mock 객체 생성 함수들을 제공합니다.
"""

from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


class MockDriverFactory:
    """WebDriver Mock 생성 팩토리"""
    
    @staticmethod
    def create_chrome_driver(
        current_url: str = "http://test.example.com",
        title: str = "Test Page",
        page_source: str = "<html><body>Test</body></html>",
        window_size: Dict[str, int] = None
    ) -> Mock:
        """Chrome WebDriver Mock 생성"""
        driver = Mock(spec=WebDriver)
        
        # 기본 속성 설정
        driver.name = "chrome"
        driver.current_url = current_url
        driver.title = title
        driver.page_source = page_source
        driver.capabilities = {
            "browserName": "chrome",
            "browserVersion": "120.0.6099.109",
            "platformName": "windows"
        }
        
        # 윈도우 크기 설정
        if window_size is None:
            window_size = {"width": 1920, "height": 1080}
        driver.get_window_size.return_value = window_size
        
        # 기본 메서드 Mock
        driver.get.return_value = None
        driver.quit.return_value = None
        driver.close.return_value = None
        driver.refresh.return_value = None
        driver.back.return_value = None
        driver.forward.return_value = None
        
        # JavaScript 실행
        driver.execute_script.return_value = "complete"
        
        # 쿠키 관리
        driver.get_cookies.return_value = []
        driver.get_cookie.return_value = None
        driver.add_cookie.return_value = None
        driver.delete_cookie.return_value = None
        driver.delete_all_cookies.return_value = None
        
        # 윈도우 관리
        driver.window_handles = ["window-1"]
        driver.current_window_handle = "window-1"
        driver.switch_to.window.return_value = None
        driver.switch_to.frame.return_value = None
        driver.switch_to.default_content.return_value = None
        
        # 알림창 관리
        driver.switch_to.alert.text = "Test Alert"
        driver.switch_to.alert.accept.return_value = None
        driver.switch_to.alert.dismiss.return_value = None
        
        return driver
    
    @staticmethod
    def create_firefox_driver(**kwargs) -> Mock:
        """Firefox WebDriver Mock 생성"""
        driver = MockDriverFactory.create_chrome_driver(**kwargs)
        driver.name = "firefox"
        driver.capabilities = {
            "browserName": "firefox",
            "browserVersion": "121.0",
            "platformName": "windows"
        }
        return driver
    
    @staticmethod
    def create_edge_driver(**kwargs) -> Mock:
        """Edge WebDriver Mock 생성"""
        driver = MockDriverFactory.create_chrome_driver(**kwargs)
        driver.name = "MicrosoftEdge"
        driver.capabilities = {
            "browserName": "MicrosoftEdge",
            "browserVersion": "120.0.2210.91",
            "platformName": "windows"
        }
        return driver
    
    @staticmethod
    def create_remote_driver(hub_url: str = "http://selenium-hub:4444/wd/hub", **kwargs) -> Mock:
        """Remote WebDriver Mock 생성"""
        driver = MockDriverFactory.create_chrome_driver(**kwargs)
        driver.command_executor._url = hub_url
        driver.session_id = "test-session-123"
        return driver


class MockElementFactory:
    """WebElement Mock 생성 팩토리"""
    
    @staticmethod
    def create_input_element(
        tag_name: str = "input",
        input_type: str = "text",
        value: str = "",
        placeholder: str = "",
        name: str = "",
        id: str = "",
        **kwargs
    ) -> Mock:
        """Input 요소 Mock 생성"""
        element = Mock(spec=WebElement)
        
        # 기본 속성
        element.tag_name = tag_name
        element.text = value
        
        # 속성 딕셔너리
        attributes = {
            "type": input_type,
            "value": value,
            "placeholder": placeholder,
            "name": name,
            "id": id,
            **kwargs
        }
        
        element.get_attribute = Mock(side_effect=lambda attr: attributes.get(attr))
        element.get_property = Mock(side_effect=lambda prop: attributes.get(prop))
        
        # 상태 메서드
        element.is_displayed.return_value = True
        element.is_enabled.return_value = True
        element.is_selected.return_value = False
        
        # 액션 메서드
        element.click = Mock()
        element.send_keys = Mock()
        element.clear = Mock()
        element.submit = Mock()
        
        # 크기 및 위치
        element.size = {"width": 200, "height": 30}
        element.location = {"x": 100, "y": 200}
        element.rect = {"x": 100, "y": 200, "width": 200, "height": 30}
        
        return element
    
    @staticmethod
    def create_button_element(
        text: str = "Click Me",
        button_type: str = "button",
        **kwargs
    ) -> Mock:
        """Button 요소 Mock 생성"""
        element = MockElementFactory.create_input_element(
            tag_name="button",
            input_type=button_type,
            **kwargs
        )
        element.text = text
        return element
    
    @staticmethod
    def create_link_element(
        text: str = "Link Text",
        href: str = "http://example.com",
        **kwargs
    ) -> Mock:
        """Link 요소 Mock 생성"""
        element = MockElementFactory.create_input_element(
            tag_name="a",
            **kwargs
        )
        element.text = text
        element.get_attribute = Mock(side_effect=lambda attr: href if attr == "href" else kwargs.get(attr))
        return element
    
    @staticmethod
    def create_select_element(
        options: List[str] = None,
        selected_option: str = None,
        **kwargs
    ) -> Mock:
        """Select 요소 Mock 생성"""
        if options is None:
            options = ["Option 1", "Option 2", "Option 3"]
        
        element = MockElementFactory.create_input_element(
            tag_name="select",
            **kwargs
        )
        
        # 옵션 요소들 생성
        option_elements = []
        for i, option_text in enumerate(options):
            option_element = Mock(spec=WebElement)
            option_element.text = option_text
            option_element.get_attribute.return_value = f"value_{i}"
            option_element.is_selected.return_value = (option_text == selected_option)
            option_elements.append(option_element)
        
        element.find_elements.return_value = option_elements
        
        return element
    
    @staticmethod
    def create_checkbox_element(
        checked: bool = False,
        **kwargs
    ) -> Mock:
        """Checkbox 요소 Mock 생성"""
        element = MockElementFactory.create_input_element(
            tag_name="input",
            input_type="checkbox",
            **kwargs
        )
        element.is_selected.return_value = checked
        return element
    
    @staticmethod
    def create_text_element(
        text: str = "Sample Text",
        tag_name: str = "div",
        **kwargs
    ) -> Mock:
        """텍스트 요소 Mock 생성"""
        element = MockElementFactory.create_input_element(
            tag_name=tag_name,
            **kwargs
        )
        element.text = text
        return element


class MockConfigManager:
    """ConfigManager Mock 생성"""
    
    @staticmethod
    def create_config_manager(
        base_url: str = "http://test.example.com",
        timeout: int = 10,
        browser_config: Dict[str, Any] = None,
        **kwargs
    ) -> Mock:
        """ConfigManager Mock 생성"""
        config_manager = Mock()
        
        # 기본 설정
        config_manager.get_base_url.return_value = base_url
        config_manager.get_timeout.return_value = timeout
        
        # 브라우저 설정
        if browser_config is None:
            browser_config = {
                "browser": "chrome",
                "headless": True,
                "window_size": (1920, 1080),
                "timeout": 30
            }
        config_manager.get_browser_config.return_value = browser_config
        
        # 추가 설정들
        config_manager.get_screenshot_dir.return_value = Path("screenshots")
        config_manager.get_report_dir.return_value = Path("reports")
        config_manager.get_test_data_dir.return_value = Path("test_data")
        
        # 환경 설정
        config_manager.get_environment.return_value = "test"
        config_manager.is_production.return_value = False
        config_manager.is_development.return_value = True
        
        # 추가 설정 적용
        for key, value in kwargs.items():
            setattr(config_manager, f"get_{key}", Mock(return_value=value))
        
        return config_manager


class MockLogger:
    """Logger Mock 생성"""
    
    @staticmethod
    def create_logger(name: str = "test_logger") -> Mock:
        """Logger Mock 생성"""
        logger = Mock()
        
        # 로그 레벨 메서드들
        logger.debug = Mock()
        logger.info = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        logger.critical = Mock()
        
        # 로거 속성
        logger.name = name
        logger.level = 10  # DEBUG level
        
        # 핸들러 관리
        logger.handlers = []
        logger.addHandler = Mock()
        logger.removeHandler = Mock()
        
        return logger


def create_mock_element(
    locator: tuple = (By.ID, "test-element"),
    element_type: str = "input",
    **kwargs
) -> Mock:
    """범용 Mock 요소 생성"""
    if element_type == "input":
        return MockElementFactory.create_input_element(**kwargs)
    elif element_type == "button":
        return MockElementFactory.create_button_element(**kwargs)
    elif element_type == "link":
        return MockElementFactory.create_link_element(**kwargs)
    elif element_type == "select":
        return MockElementFactory.create_select_element(**kwargs)
    elif element_type == "checkbox":
        return MockElementFactory.create_checkbox_element(**kwargs)
    elif element_type == "text":
        return MockElementFactory.create_text_element(**kwargs)
    else:
        return MockElementFactory.create_input_element(**kwargs)


def create_mock_driver(browser: str = "chrome", **kwargs) -> Mock:
    """범용 Mock 드라이버 생성"""
    if browser.lower() == "chrome":
        return MockDriverFactory.create_chrome_driver(**kwargs)
    elif browser.lower() == "firefox":
        return MockDriverFactory.create_firefox_driver(**kwargs)
    elif browser.lower() == "edge":
        return MockDriverFactory.create_edge_driver(**kwargs)
    elif browser.lower() == "remote":
        return MockDriverFactory.create_remote_driver(**kwargs)
    else:
        return MockDriverFactory.create_chrome_driver(**kwargs)


def setup_element_finding_mock(
    driver_mock: Mock,
    locator: tuple,
    element_mock: Mock = None,
    found: bool = True,
    multiple: bool = False
):
    """요소 찾기 Mock 설정"""
    if found and element_mock is None:
        element_mock = create_mock_element()
    
    if found:
        driver_mock.find_element.return_value = element_mock
        if multiple:
            driver_mock.find_elements.return_value = [element_mock, element_mock]
        else:
            driver_mock.find_elements.return_value = [element_mock]
    else:
        from selenium.common.exceptions import NoSuchElementException
        driver_mock.find_element.side_effect = NoSuchElementException()
        driver_mock.find_elements.return_value = []
    
    return element_mock


def setup_wait_mock(driver_mock: Mock, condition_result: Any = True):
    """WebDriverWait Mock 설정"""
    with patch('selenium.webdriver.support.ui.WebDriverWait') as wait_mock:
        wait_instance = Mock()
        wait_instance.until.return_value = condition_result
        wait_mock.return_value = wait_instance
        return wait_mock


@patch('selenium.webdriver.Chrome')
@patch('selenium.webdriver.Firefox')
@patch('selenium.webdriver.Edge')
def mock_all_drivers(edge_mock, firefox_mock, chrome_mock):
    """모든 드라이버 Mock 데코레이터"""
    chrome_mock.return_value = MockDriverFactory.create_chrome_driver()
    firefox_mock.return_value = MockDriverFactory.create_firefox_driver()
    edge_mock.return_value = MockDriverFactory.create_edge_driver()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class MockWebDriverWait:
    """WebDriverWait Mock 클래스"""
    
    def __init__(self, driver, timeout, poll_frequency=0.5, ignored_exceptions=None):
        self.driver = driver
        self.timeout = timeout
        self.poll_frequency = poll_frequency
        self.ignored_exceptions = ignored_exceptions or []
    
    def until(self, method, message=""):
        """조건이 True가 될 때까지 대기 (Mock)"""
        # Mock에서는 즉시 결과 반환
        try:
            result = method(self.driver)
            if result:
                return result
            else:
                from selenium.common.exceptions import TimeoutException
                raise TimeoutException(message)
        except Exception as e:
            if type(e) in self.ignored_exceptions:
                return None
            raise
    
    def until_not(self, method, message=""):
        """조건이 False가 될 때까지 대기 (Mock)"""
        try:
            result = method(self.driver)
            if not result:
                return True
            else:
                from selenium.common.exceptions import TimeoutException
                raise TimeoutException(message)
        except Exception as e:
            if type(e) in self.ignored_exceptions:
                return True
            raise


def patch_webdriver_wait():
    """WebDriverWait 패치 데코레이터"""
    return patch('selenium.webdriver.support.ui.WebDriverWait', MockWebDriverWait)