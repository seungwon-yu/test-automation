"""
LoginPage 클래스 단위 테스트

이 모듈은 LoginPage 클래스의 모든 기능에 대한
포괄적인 단위 테스트를 제공합니다.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)

from src.pages.login_page import LoginPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException,
    LoginException
)


class TestLoginPage:
    """LoginPage 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.mock_config_manager = Mock()
        self.mock_logger = Mock()
        self.mock_retry_manager = Mock()
        
        # Mock 설정
        self.mock_config_manager.get_base_url.return_value = "http://test.com"
        self.mock_config_manager.get_timeout.return_value = 10
        
        with patch('src.core.config.get_config_manager', return_value=self.mock_config_manager):
            with patch('src.core.logging.get_logger', return_value=self.mock_logger):
                with patch('src.core.retry_manager.SmartRetryManager', return_value=self.mock_retry_manager):
                    self.login_page = LoginPage(self.mock_driver, "http://test.com")
    
    def test_login_page_initialization(self):
        """LoginPage 초기화 테스트"""
        assert self.login_page.driver == self.mock_driver
        assert self.login_page.base_url == "http://test.com"
        assert self.login_page.login_timeout == 30
        assert self.login_page.redirect_timeout == 10
        assert hasattr(self.login_page, 'logger')
        assert hasattr(self.login_page, 'retry_manager')
    
    def test_navigate_to_login_default_url(self):
        """기본 URL로 로그인 페이지 이동 테스트"""
        with patch.object(self.login_page, 'navigate_to') as mock_navigate:
            with patch.object(self.login_page, 'wait_for_login_page_load'):
                self.login_page.navigate_to_login()
        
        mock_navigate.assert_called_once_with("http://test.com/login")
    
    def test_navigate_to_login_custom_url(self):
        """사용자 지정 URL로 로그인 페이지 이동 테스트"""
        custom_url = "http://custom.com/signin"
        
        with patch.object(self.login_page, 'navigate_to') as mock_navigate:
            with patch.object(self.login_page, 'wait_for_login_page_load'):
                self.login_page.navigate_to_login(custom_url)
        
        mock_navigate.assert_called_once_with(custom_url)
    
    def test_navigate_to_login_page_load_failure(self):
        """로그인 페이지 로딩 실패 테스트"""
        with patch.object(self.login_page, 'navigate_to'):
            with patch.object(self.login_page, 'wait_for_login_page_load', side_effect=ElementNotFoundException("Not found")):
                with pytest.raises(PageLoadTimeoutException):
                    self.login_page.navigate_to_login()
    
    def test_wait_for_login_page_load_success(self):
        """로그인 페이지 로딩 대기 성공 테스트"""
        with patch.object(self.login_page, 'wait_for_page_load'):
            with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
                with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                    with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                        # 예외가 발생하지 않아야 함
                        self.login_page.wait_for_login_page_load()
    
    def test_wait_for_login_page_load_failure(self):
        """로그인 페이지 로딩 대기 실패 테스트"""
        with patch.object(self.login_page, 'wait_for_page_load'):
            with patch.object(self.login_page, '_find_username_field', side_effect=ElementNotFoundException("Not found")):
                with pytest.raises(ElementNotFoundException):
                    self.login_page.wait_for_login_page_load()
    
    def test_find_username_field_default_locator(self):
        """기본 로케이터로 사용자명 필드 찾기 테스트"""
        with patch.object(self.login_page, 'is_element_present', return_value=True):
            result = self.login_page._find_username_field()
        
        assert result == self.login_page.USERNAME_INPUT
    
    def test_find_username_field_alternative_locator(self):
        """대체 로케이터로 사용자명 필드 찾기 테스트"""
        # 기본 로케이터는 실패, 첫 번째 대체 로케이터는 성공
        with patch.object(self.login_page, 'is_element_present', side_effect=[False, True]):
            result = self.login_page._find_username_field()
        
        assert result == self.login_page.ALT_USERNAME_LOCATORS[0]
    
    def test_find_username_field_not_found(self):
        """사용자명 필드를 찾을 수 없는 경우 테스트"""
        with patch.object(self.login_page, 'is_element_present', return_value=False):
            with pytest.raises(ElementNotFoundException):
                self.login_page._find_username_field()
    
    def test_find_error_message_element_found(self):
        """에러 메시지 요소 찾기 성공 테스트"""
        with patch.object(self.login_page, 'is_element_present', return_value=True):
            result = self.login_page._find_error_message_element()
        
        assert result == self.login_page.ERROR_MESSAGE
    
    def test_find_error_message_element_not_found(self):
        """에러 메시지 요소를 찾을 수 없는 경우 테스트"""
        with patch.object(self.login_page, 'is_element_present', return_value=False):
            result = self.login_page._find_error_message_element()
        
        assert result is None
    
    def test_enter_username(self):
        """사용자명 입력 테스트"""
        username_locator = (By.ID, "username")
        
        with patch.object(self.login_page, '_find_username_field', return_value=username_locator):
            with patch.object(self.login_page, 'input_text') as mock_input:
                self.login_page.enter_username("test_user")
        
        mock_input.assert_called_once_with(username_locator, "test_user", clear_first=True)
    
    def test_enter_password(self):
        """비밀번호 입력 테스트"""
        password_locator = (By.ID, "password")
        
        with patch.object(self.login_page, '_find_password_field', return_value=password_locator):
            with patch.object(self.login_page, 'input_text') as mock_input:
                self.login_page.enter_password("test_pass")
        
        mock_input.assert_called_once_with(password_locator, "test_pass", clear_first=True)
    
    def test_click_login_button(self):
        """로그인 버튼 클릭 테스트"""
        login_button_locator = (By.ID, "login-btn")
        
        with patch.object(self.login_page, '_find_login_button', return_value=login_button_locator):
            with patch.object(self.login_page, 'click_element') as mock_click:
                self.login_page.click_login_button()
        
        mock_click.assert_called_once_with(login_button_locator)
    
    def test_toggle_remember_me_enable(self):
        """Remember Me 체크박스 활성화 테스트"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = False
        
        with patch.object(self.login_page, 'is_element_present', return_value=True):
            with patch.object(self.login_page, 'find_element', return_value=mock_checkbox):
                with patch.object(self.login_page, 'click_element') as mock_click:
                    self.login_page.toggle_remember_me(True)
        
        mock_click.assert_called_once_with(self.login_page.REMEMBER_ME_CHECKBOX)
    
    def test_toggle_remember_me_not_present(self):
        """Remember Me 체크박스가 없는 경우 테스트"""
        with patch.object(self.login_page, 'is_element_present', return_value=False):
            # 예외가 발생하지 않아야 함
            self.login_page.toggle_remember_me(True)
    
    def test_has_error_message_true(self):
        """에러 메시지 존재 확인 - 있음"""
        with patch.object(self.login_page, '_find_error_message_element', return_value=(By.CLASS_NAME, "error")):
            result = self.login_page.has_error_message()
        
        assert result is True
    
    def test_has_error_message_false(self):
        """에러 메시지 존재 확인 - 없음"""
        with patch.object(self.login_page, '_find_error_message_element', return_value=None):
            result = self.login_page.has_error_message()
        
        assert result is False
    
    def test_get_error_message_found(self):
        """에러 메시지 텍스트 가져오기 - 발견됨"""
        error_locator = (By.CLASS_NAME, "error")
        error_text = "Invalid username or password"
        
        with patch.object(self.login_page, '_find_error_message_element', return_value=error_locator):
            with patch.object(self.login_page, 'get_text', return_value=error_text):
                result = self.login_page.get_error_message()
        
        assert result == error_text
    
    def test_get_error_message_not_found(self):
        """에러 메시지 텍스트 가져오기 - 발견되지 않음"""
        with patch.object(self.login_page, '_find_error_message_element', return_value=None):
            result = self.login_page.get_error_message()
        
        assert result == ""  
    def test_is_login_successful_true(self):
        """로그인 성공 확인 - 성공"""
        with patch.object(self.login_page, 'get_current_url', return_value="http://test.com/dashboard"):
            with patch.object(self.login_page, '_find_success_indicator', return_value=(By.CLASS_NAME, "dashboard")):
                result = self.login_page.is_login_successful()
        
        assert result is True
    
    def test_is_login_successful_false(self):
        """로그인 성공 확인 - 실패"""
        with patch.object(self.login_page, 'get_current_url', return_value="http://test.com/login"):
            with patch.object(self.login_page, 'has_error_message', return_value=True):
                result = self.login_page.is_login_successful()
        
        assert result is False
    
    def test_login_successful(self):
        """로그인 성공 테스트"""
        with patch.object(self.login_page, 'wait_for_login_page_load'):
            with patch.object(self.login_page, 'enter_username'):
                with patch.object(self.login_page, 'enter_password'):
                    with patch.object(self.login_page, 'click_login_button'):
                        with patch.object(self.login_page, '_wait_for_login_processing'):
                            with patch.object(self.login_page, 'is_login_successful', return_value=True):
                                
                                result = self.login_page.login("test_user", "test_pass")
        
        assert result is True
    
    def test_login_failed(self):
        """로그인 실패 테스트"""
        with patch.object(self.login_page, 'wait_for_login_page_load'):
            with patch.object(self.login_page, 'enter_username'):
                with patch.object(self.login_page, 'enter_password'):
                    with patch.object(self.login_page, 'click_login_button'):
                        with patch.object(self.login_page, '_wait_for_login_processing'):
                            with patch.object(self.login_page, 'is_login_successful', return_value=False):
                                with patch.object(self.login_page, 'get_error_message', return_value="Invalid credentials"):
                                    
                                    with pytest.raises(LoginException):
                                        self.login_page.login("wrong_user", "wrong_pass")
    
    def test_login_with_exception(self):
        """로그인 중 예외 발생 테스트"""
        with patch.object(self.login_page, 'wait_for_login_page_load'):
            with patch.object(self.login_page, 'enter_username', side_effect=Exception("Username input failed")):
                
                with pytest.raises(LoginException):
                    self.login_page.login("test_user", "test_pass")
    
    def test_quick_login_success(self):
        """빠른 로그인 성공 테스트"""
        credentials = {
            'username': 'test_user',
            'password': 'test_pass',
            'remember_me': True
        }
        
        with patch.object(self.login_page, 'login', return_value=True) as mock_login:
            result = self.login_page.quick_login(credentials)
        
        mock_login.assert_called_once_with('test_user', 'test_pass', True, None)
        assert result is True
    
    def test_quick_login_failure(self):
        """빠른 로그인 실패 테스트"""
        credentials = {
            'username': 'wrong_user',
            'password': 'wrong_pass'
        }
        
        with patch.object(self.login_page, 'login', side_effect=LoginException("Login failed")):
            with pytest.raises(LoginException):
                self.login_page.quick_login(credentials)
    
    def test_validate_login_page_elements_all_present(self):
        """로그인 페이지 요소 검증 - 모든 요소 존재"""
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    
                    result = self.login_page.validate_login_page_elements()
        
        assert result['username_field'] is True
        assert result['password_field'] is True
        assert result['login_button'] is True
        assert result['all_elements_present'] is True
    
    def test_validate_login_page_elements_missing(self):
        """로그인 페이지 요소 검증 - 일부 요소 누락"""
        with patch.object(self.login_page, '_find_username_field', side_effect=ElementNotFoundException("Not found")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    
                    result = self.login_page.validate_login_page_elements()
        
        assert result['username_field'] is False
        assert result['password_field'] is True
        assert result['login_button'] is True
        assert result['all_elements_present'] is False
    
    def test_clear_login_form(self):
        """로그인 폼 초기화 테스트"""
        mock_username_element = Mock()
        mock_password_element = Mock()
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = True
        
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, 'find_element', side_effect=[mock_username_element, mock_password_element, mock_checkbox]):
                    with patch.object(self.login_page, 'is_element_present', return_value=True):
                        with patch.object(self.login_page, 'click_element') as mock_click:
                            
                            self.login_page.clear_login_form()
        
        mock_username_element.clear.assert_called_once()
        mock_password_element.clear.assert_called_once()
        mock_click.assert_called_once_with(self.login_page.REMEMBER_ME_CHECKBOX)
    
    def test_get_login_form_info(self):
        """로그인 폼 정보 수집 테스트"""
        with patch.object(self.login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(self.login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(self.login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    with patch.object(self.login_page, 'is_element_present', return_value=False):
                        with patch.object(self.login_page, 'get_current_url', return_value="http://test.com/login"):
                            with patch.object(self.login_page, 'get_page_title', return_value="Login Page"):
                                
                                info = self.login_page.get_login_form_info()
        
        assert info['has_username_field'] is True
        assert info['has_password_field'] is True
        assert info['has_login_button'] is True
        assert info['current_url'] == "http://test.com/login"
        assert info['page_title'] == "Login Page"