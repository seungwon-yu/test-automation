"""
FormPage 클래스 단위 테스트

이 모듈은 FormPage 클래스의 핵심 기능에 대한
단위 테스트를 제공합니다.
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from src.pages.form_page import FormPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestFormPage:
    """FormPage 클래스 테스트"""
    
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
                    self.form_page = FormPage(self.mock_driver, "http://test.com")
    
    def test_form_page_initialization(self):
        """FormPage 초기화 테스트"""
        assert self.form_page.driver == self.mock_driver
        assert self.form_page.base_url == "http://test.com"
        assert hasattr(self.form_page, 'logger')
    
    def test_navigate_to_form_default_url(self):
        """기본 URL로 폼 페이지 이동 테스트"""
        with patch.object(self.form_page, 'navigate_to') as mock_navigate:
            with patch.object(self.form_page, 'wait_for_form_load'):
                self.form_page.navigate_to_form()
        
        mock_navigate.assert_called_once_with("http://test.com/contact")
    
    def test_fill_personal_info_success(self):
        """개인 정보 입력 성공 테스트"""
        personal_info = {
            'first_name': '홍',
            'last_name': '길동',
            'email': 'hong@example.com',
            'phone': '010-1234-5678'
        }
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'input_text') as mock_input:
                result = self.form_page.fill_personal_info(personal_info)
        
        assert result is True
        assert mock_input.call_count == 4  # 4개 필드 입력
    
    def test_fill_message_success(self):
        """메시지 입력 성공 테스트"""
        message = "테스트 메시지입니다."
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'input_text') as mock_input:
                result = self.form_page.fill_message(message)
        
        mock_input.assert_called_once_with(self.form_page.MESSAGE, message, clear_first=True)
        assert result is True
    
    def test_select_country_success(self):
        """국가 선택 성공 테스트"""
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'select_dropdown_by_text') as mock_select:
                result = self.form_page.select_country("대한민국")
        
        mock_select.assert_called_once_with(self.form_page.COUNTRY_SELECT, "대한민국")
        assert result is True
    
    def test_set_newsletter_subscription_true(self):
        """뉴스레터 구독 설정 - 구독"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = False
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_element', return_value=mock_checkbox):
                with patch.object(self.form_page, 'click_element') as mock_click:
                    result = self.form_page.set_newsletter_subscription(True)
        
        mock_click.assert_called_once()
        assert result is True
    
    def test_set_newsletter_subscription_false(self):
        """뉴스레터 구독 설정 - 구독 해제"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = True
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_element', return_value=mock_checkbox):
                with patch.object(self.form_page, 'click_element') as mock_click:
                    result = self.form_page.set_newsletter_subscription(False)
        
        mock_click.assert_called_once()
        assert result is True
    
    def test_accept_terms_success(self):
        """약관 동의 테스트"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = False
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_element', return_value=mock_checkbox):
                with patch.object(self.form_page, 'click_element') as mock_click:
                    result = self.form_page.accept_terms(True)
        
        mock_click.assert_called_once()
        assert result is True
    
    def test_select_gender_male(self):
        """성별 선택 - 남성"""
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'click_element') as mock_click:
                result = self.form_page.select_gender('male')
        
        mock_click.assert_called_once_with(self.form_page.GENDER_MALE)
        assert result is True
    
    def test_select_gender_female(self):
        """성별 선택 - 여성"""
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'click_element') as mock_click:
                result = self.form_page.select_gender('female')
        
        mock_click.assert_called_once_with(self.form_page.GENDER_FEMALE)
        assert result is True
    
    def test_upload_file_success(self):
        """파일 업로드 성공 테스트"""
        file_path = "/path/to/test/file.txt"
        mock_file_input = Mock()
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_element', return_value=mock_file_input):
                result = self.form_page.upload_file(file_path)
        
        mock_file_input.send_keys.assert_called_once_with(file_path)
        assert result is True
    
    def test_submit_form_success(self):
        """폼 제출 성공 테스트"""
        with patch.object(self.form_page, '_find_submit_button', return_value=(By.CSS_SELECTOR, "button[type='submit']")):
            with patch.object(self.form_page, 'click_element'):
                with patch.object(self.form_page, 'wait'):
                    with patch.object(self.form_page, 'is_element_present', return_value=True):
                        result = self.form_page.submit_form()
        
        assert result is True
    
    def test_submit_form_with_error(self):
        """폼 제출 실패 테스트"""
        with patch.object(self.form_page, '_find_submit_button', return_value=(By.CSS_SELECTOR, "button[type='submit']")):
            with patch.object(self.form_page, 'click_element'):
                with patch.object(self.form_page, 'wait'):
                    with patch.object(self.form_page, 'is_element_present', side_effect=[False, True]):  # success=False, error=True
                        with patch.object(self.form_page, 'get_text', return_value="Validation error"):
                            result = self.form_page.submit_form()
        
        assert result is False
    
    def test_reset_form_success(self):
        """폼 리셋 성공 테스트"""
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'click_element') as mock_click:
                result = self.form_page.reset_form()
        
        mock_click.assert_called_once_with(self.form_page.RESET_BUTTON)
        assert result is True
    
    def test_get_validation_errors(self):
        """유효성 검사 오류 가져오기 테스트"""
        mock_error1 = Mock()
        mock_error1.text = "이메일 형식이 올바르지 않습니다."
        mock_error2 = Mock()
        mock_error2.text = "필수 입력 항목입니다."
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_elements', return_value=[mock_error1, mock_error2]):
                errors = self.form_page.get_validation_errors()
        
        assert len(errors) == 2
        assert "이메일 형식이 올바르지 않습니다." in errors
        assert "필수 입력 항목입니다." in errors
    
    def test_is_form_valid_true(self):
        """폼 유효성 확인 - 유효함"""
        with patch.object(self.form_page, 'get_validation_errors', return_value=[]):
            result = self.form_page.is_form_valid()
        
        assert result is True
    
    def test_is_form_valid_false(self):
        """폼 유효성 확인 - 유효하지 않음"""
        with patch.object(self.form_page, 'get_validation_errors', return_value=["Error message"]):
            result = self.form_page.is_form_valid()
        
        assert result is False
    
    def test_get_form_data(self):
        """폼 데이터 가져오기 테스트"""
        mock_first_name = Mock()
        mock_first_name.get_attribute.return_value = "홍"
        mock_last_name = Mock()
        mock_last_name.get_attribute.return_value = "길동"
        mock_email = Mock()
        mock_email.get_attribute.return_value = "hong@example.com"
        
        mock_newsletter = Mock()
        mock_newsletter.is_selected.return_value = True
        
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            with patch.object(self.form_page, 'find_element', side_effect=[mock_first_name, mock_last_name, mock_email, Mock(), Mock(), Mock(), mock_newsletter]):
                form_data = self.form_page.get_form_data()
        
        assert form_data['first_name'] == "홍"
        assert form_data['last_name'] == "길동"
        assert form_data['email'] == "hong@example.com"
        assert form_data['newsletter'] is True
    
    def test_is_form_submitted_success_message(self):
        """폼 제출 완료 확인 - 성공 메시지"""
        with patch.object(self.form_page, 'is_element_present', return_value=True):
            result = self.form_page.is_form_submitted()
        
        assert result is True
    
    def test_is_form_submitted_url_change(self):
        """폼 제출 완료 확인 - URL 변경"""
        with patch.object(self.form_page, 'is_element_present', return_value=False):
            with patch.object(self.form_page, 'get_current_url', return_value="http://test.com/success"):
                result = self.form_page.is_form_submitted()
        
        assert result is True