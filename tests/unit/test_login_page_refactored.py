"""
LoginPage 클래스 리팩토링된 단위 테스트

새로운 테스트 유틸리티를 활용한 개선된 테스트입니다.
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from tests.utils import (
    PageTestCase,
    assert_element_present,
    assert_mock_called,
    assert_mock_called_with,
    create_mock_element,
    MockElementFactory
)

from src.pages.login_page import LoginPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException,
    LoginException
)


class TestLoginPageRefactored(PageTestCase):
    """리팩토링된 LoginPage 테스트"""
    
    def setup_method(self):
        """테스트 설정 (PageTestCase에서 대부분 처리)"""
        super().setup_method()
        self.login_page = LoginPage(self.mock_driver, "http://test.example.com")
    
    def test_initialization_with_utilities(self):
        """유틸리티를 사용한 초기화 테스트"""
        # 기본 속성 확인
        assert self.login_page.driver == self.mock_driver
        assert self.login_page.base_url == "http://test.example.com"
        assert self.login_page.login_timeout == 30
        assert self.login_page.redirect_timeout == 10
        
        # Mock 객체들이 올바르게 설정되었는지 확인
        assert hasattr(self.login_page, 'logger')
        assert hasattr(self.login_page, 'retry_manager')
    
    def test_navigate_to_login_with_assertions(self):
        """커스텀 어설션을 사용한 로그인 페이지 이동 테스트"""
        with patch.object(self.login_page, 'navigate_to') as mock_navigate:
            with patch.object(self.login_page, 'wait_for_login_page_load'):
                self.login_page.navigate_to_login()
        
        # Mock 호출 검증 (새로운 어설션 사용)
        assert_mock_called_with(mock_navigate, "http://test.example.com/login")
        
        # 로그 메시지 검증
        self.assert_log_message("info", "Navigating to login page")
        self.assert_log_message("info", "Successfully navigated to login page")
    
    def test_smart_locator_system(self):
        """Smart Locator 시스템 테스트"""
        # 기본 로케이터 성공 케이스
        with patch.object(self.login_page, 'is_element_present', return_value=True):
            result = self.login_page._find_username_field()
            assert result == self.login_page.USERNAME_INPUT
        
        # 대체 로케이터 사용 케이스
        def mock_element_present(locator, timeout=2):
            if locator == self.login_page.USERNAME_INPUT:
                return False  # 기본 로케이터 실패
            elif locator == self.login_page.ALT_USERNAME_LOCATORS[0]:
                return True   # 첫 번째 대체 로케이터 성공
            return False
        
        with patch.object(self.login_page, 'is_element_present', side_effect=mock_element_present):
            result = self.login_page._find_username_field()
            assert result == self.login_page.ALT_USERNAME_LOCATORS[0]
        
        # 모든 로케이터 실패 케이스
        with patch.object(self.login_page, 'is_element_present', return_value=False):
            with pytest.raises(ElementNotFoundException):
                self.login_page._find_username_field()
    
    def test_form_interaction_with_mock_elements(self):
        """Mock 요소를 사용한 폼 상호작용 테스트"""
        # Mock 요소들 생성 (새로운 팩토리 사용)
        username_element = MockElementFactory.create_input_element(
            input_type="text",
            id="username",
            placeholder="Enter username"
        )
        
        password_element = MockElementFactory.create_input_element(
            input_type="password",
            id="password",
            placeholder="Enter password"
        )
        
        login_button = MockElementFactory.create_button_element(
            text="Login",
            button_type="submit"
        )
        
        # 요소 찾기 Mock 설정
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    with patch.object(self.login_page, 'input_text') as mock_input:
                        with patch.object(self.login_page, 'click_element') as mock_click:
                            
                            # 폼 입력 테스트
                            self.login_page.enter_username("testuser")
                            self.login_page.enter_password("testpass")
                            self.login_page.click_login_button()
        
        # 상호작용 검증
        assert_mock_called_with(mock_input, (By.ID, "username"), "testuser", clear_first=True)
        assert_mock_called_with(mock_input, (By.ID, "password"), "testpass", clear_first=True)
        assert_mock_called_with(mock_click, (By.ID, "login-btn"))
    
    def test_login_success_validation(self):
        """로그인 성공 검증 테스트"""
        # 성공 시나리오 Mock 설정
        self.mock_driver.current_url = "http://test.example.com/dashboard"
        
        with patch.object(self.login_page, '_find_success_indicator', return_value=(By.CLASS_NAME, "dashboard")):
            with patch.object(self.login_page, 'has_error_message', return_value=False):
                result = self.login_page.is_login_successful()
        
        assert result is True
        
        # 실패 시나리오 Mock 설정
        self.mock_driver.current_url = "http://test.example.com/login"
        
        with patch.object(self.login_page, 'has_error_message', return_value=True):
            result = self.login_page.is_login_successful()
        
        assert result is False
    
    def test_error_message_handling(self):
        """에러 메시지 처리 테스트"""
        error_text = "Invalid username or password"
        
        # 에러 메시지 존재 케이스
        with patch.object(self.login_page, '_find_error_message_element', return_value=(By.CLASS_NAME, "error")):
            with patch.object(self.login_page, 'get_text', return_value=error_text):
                result = self.login_page.get_error_message()
                assert result == error_text
        
        # 에러 메시지 없는 케이스
        with patch.object(self.login_page, '_find_error_message_element', return_value=None):
            result = self.login_page.get_error_message()
            assert result == ""
        
        # 여러 에러 메시지 수집 테스트
        error_messages = ["Error 1", "Error 2"]
        mock_elements = [
            MockElementFactory.create_text_element(text=msg) 
            for msg in error_messages
        ]
        
        with patch.object(self.login_page, 'is_element_present', return_value=True):
            with patch.object(self.login_page, 'find_elements', return_value=mock_elements):
                result = self.login_page.get_all_error_messages()
                assert len(result) == 2
                assert "Error 1" in result
                assert "Error 2" in result
    
    def test_complete_login_flow(self):
        """완전한 로그인 플로우 테스트"""
        # 성공 시나리오
        with patch.object(self.login_page, 'wait_for_login_page_load'):
            with patch.object(self.login_page, 'enter_username') as mock_username:
                with patch.object(self.login_page, 'enter_password') as mock_password:
                    with patch.object(self.login_page, 'click_login_button') as mock_click:
                        with patch.object(self.login_page, '_wait_for_login_processing'):
                            with patch.object(self.login_page, 'is_login_successful', return_value=True):
                                
                                result = self.login_page.login("testuser", "testpass")
        
        # 결과 검증
        assert result is True
        
        # 메서드 호출 검증
        assert_mock_called_with(mock_username, "testuser")
        assert_mock_called_with(mock_password, "testpass")
        assert_mock_called(mock_click)
        
        # 로그 메시지 검증
        self.assert_log_message("info", "Attempting login for user: testuser")
        self.assert_log_message("info", "Login successful for user: testuser")
    
    def test_login_failure_handling(self):
        """로그인 실패 처리 테스트"""
        error_message = "Invalid credentials"
        
        with patch.object(self.login_page, 'wait_for_login_page_load'):
            with patch.object(self.login_page, 'enter_username'):
                with patch.object(self.login_page, 'enter_password'):
                    with patch.object(self.login_page, 'click_login_button'):
                        with patch.object(self.login_page, '_wait_for_login_processing'):
                            with patch.object(self.login_page, 'is_login_successful', return_value=False):
                                with patch.object(self.login_page, 'get_error_message', return_value=error_message):
                                    
                                    with pytest.raises(LoginException) as exc_info:
                                        self.login_page.login("wrong_user", "wrong_pass")
        
        # 예외 메시지 확인
        assert error_message in str(exc_info.value)
        
        # 에러 로그 확인
        self.assert_log_message("error", "Login failed for user: wrong_user")
    
    def test_quick_login_utility(self):
        """빠른 로그인 유틸리티 테스트"""
        credentials = {
            'username': 'testuser',
            'password': 'testpass',
            'remember_me': True,
            'captcha': '1234'
        }
        
        with patch.object(self.login_page, 'login', return_value=True) as mock_login:
            result = self.login_page.quick_login(credentials)
        
        # 호출 검증
        assert_mock_called_with(
            mock_login, 
            'testuser', 
            'testpass', 
            True,  # remember_me
            '1234'  # captcha
        )
        assert result is True
    
    def test_form_utilities(self):
        """폼 유틸리티 테스트"""
        # Mock 요소들 설정
        username_element = MockElementFactory.create_input_element(value="old_user")
        password_element = MockElementFactory.create_input_element(value="old_pass")
        checkbox_element = MockElementFactory.create_checkbox_element(checked=True)
        
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, 'find_element', side_effect=[username_element, password_element, checkbox_element]):
                    with patch.object(self.login_page, 'is_element_present', return_value=True):
                        with patch.object(self.login_page, 'click_element') as mock_click:
                            
                            # 폼 초기화 테스트
                            self.login_page.clear_login_form()
        
        # 요소 상호작용 검증
        assert_mock_called(username_element, "clear")
        assert_mock_called(password_element, "clear")
        assert_mock_called_with(mock_click, self.login_page.REMEMBER_ME_CHECKBOX)
    
    def test_page_validation_utilities(self):
        """페이지 검증 유틸리티 테스트"""
        # 모든 요소 존재 시나리오
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    
                    result = self.login_page.validate_login_page_elements()
        
        assert result['username_field'] is True
        assert result['password_field'] is True
        assert result['login_button'] is True
        assert result['all_elements_present'] is True
        
        # 일부 요소 누락 시나리오
        with patch.object(self.login_page, '_find_username_field', side_effect=ElementNotFoundException("Not found")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    
                    result = self.login_page.validate_login_page_elements()
        
        assert result['username_field'] is False
        assert result['password_field'] is True
        assert result['login_button'] is True
        assert result['all_elements_present'] is False
    
    def test_form_info_collection(self):
        """폼 정보 수집 테스트"""
        # Mock 설정
        self.mock_driver.current_url = "http://test.example.com/login"
        self.mock_driver.title = "Login Page"
        
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    with patch.object(self.login_page, 'is_element_present', return_value=False):
                        
                        info = self.login_page.get_login_form_info()
        
        # 정보 검증
        assert info['has_username_field'] is True
        assert info['has_password_field'] is True
        assert info['has_login_button'] is True
        assert info['current_url'] == "http://test.example.com/login"
        assert info['page_title'] == "Login Page"
    
    def test_performance_with_utilities(self):
        """성능 테스트 유틸리티 사용"""
        # 성능 측정과 함께 로그인 테스트
        with self.measure_time('login_process'):
            with patch.object(self.login_page, 'wait_for_login_page_load'):
                with patch.object(self.login_page, 'enter_username'):
                    with patch.object(self.login_page, 'enter_password'):
                        with patch.object(self.login_page, 'click_login_button'):
                            with patch.object(self.login_page, '_wait_for_login_processing'):
                                with patch.object(self.login_page, 'is_login_successful', return_value=True):
                                    
                                    self.login_page.login("testuser", "testpass")
        
        # 성능 검증 (1초 이내)
        self.assert_performance('login_process', 1.0)
    
    def test_exception_handling_with_context(self):
        """컨텍스트를 포함한 예외 처리 테스트"""
        # 예외 발생하지 않는 케이스
        with self.assert_no_exceptions():
            with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
                self.login_page._find_username_field()
        
        # 특정 예외만 허용하는 케이스
        with self.assert_no_exceptions(allowed_exceptions=(ElementNotFoundException,)):
            with patch.object(self.login_page, '_find_username_field', side_effect=ElementNotFoundException("Not found")):
                self.login_page._find_username_field()


@pytest.mark.parametrize("browser_type", ["chrome", "firefox", "edge"])
class TestCrossBrowserCompatibility(PageTestCase):
    """크로스 브라우저 호환성 테스트"""
    
    def test_login_page_cross_browser(self, browser_type):
        """브라우저별 LoginPage 테스트"""
        from tests.utils import create_mock_driver
        
        # 브라우저별 Mock 드라이버 생성
        mock_driver = create_mock_driver(browser_type)
        
        # LoginPage 생성
        login_page = LoginPage(mock_driver)
        
        # 기본 기능 테스트
        assert hasattr(login_page, 'login')
        assert hasattr(login_page, 'enter_username')
        assert hasattr(login_page, 'enter_password')
        
        # 브라우저별 특성 확인
        expected_names = {
            "chrome": "chrome",
            "firefox": "firefox", 
            "edge": "MicrosoftEdge"
        }
        assert mock_driver.name == expected_names[browser_type]


@pytest.mark.slow
class TestPerformanceScenarios(PageTestCase):
    """성능 시나리오 테스트"""
    
    def test_bulk_login_attempts(self):
        """대량 로그인 시도 성능 테스트"""
        login_page = LoginPage(self.mock_driver)
        
        # 100회 로그인 시도 시뮬레이션
        with self.measure_time('bulk_login'):
            for i in range(100):
                with patch.object(login_page, 'wait_for_login_page_load'):
                    with patch.object(login_page, 'enter_username'):
                        with patch.object(login_page, 'enter_password'):
                            with patch.object(login_page, 'click_login_button'):
                                with patch.object(login_page, '_wait_for_login_processing'):
                                    with patch.object(login_page, 'is_login_successful', return_value=True):
                                        login_page.login(f"user{i}", f"pass{i}")
        
        # 성능 검증 (5초 이내)
        self.assert_performance('bulk_login', 5.0)


if __name__ == "__main__":
    # 개별 테스트 실행 예제
    pytest.main([__file__, "-v", "--tb=short"])