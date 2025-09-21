"""
BasePage 클래스 단위 테스트

이 모듈은 BasePage 클래스의 모든 기능에 대한
포괄적인 단위 테스트를 제공합니다.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

from src.pages.base_page import BasePage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestBasePage:
    """BasePage 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.mock_config_manager = Mock()
        
        # Mock 설정
        self.mock_config_manager.get_base_url.return_value = "http://test.com"
        self.mock_config_manager.get_timeout.return_value = 10
        
        with patch('src.pages.base_page.get_config_manager', return_value=self.mock_config_manager):
            self.page = BasePage(self.mock_driver, "http://test.com")
    
    def test_page_initialization(self):
        """페이지 초기화 테스트"""
        assert self.page.driver == self.mock_driver
        assert self.page.base_url == "http://test.com"
        assert self.page.default_timeout == 10
        assert hasattr(self.page, 'logger')
        assert hasattr(self.page, 'retry_manager')
        assert isinstance(self.page.screenshot_dir, Path)
    
    def test_navigate_to_default_url(self):
        """기본 URL로 이동 테스트"""
        with patch.object(self.page, 'wait_for_page_load'):
            self.page.navigate_to()
        
        self.mock_driver.get.assert_called_once_with("http://test.com")
    
    def test_navigate_to_custom_url(self):
        """사용자 지정 URL로 이동 테스트"""
        custom_url = "http://custom.com"
        
        with patch.object(self.page, 'wait_for_page_load'):
            self.page.navigate_to(custom_url)
        
        self.mock_driver.get.assert_called_once_with(custom_url)    
 
   def test_navigate_to_failure(self):
        """URL 이동 실패 테스트"""
        self.mock_driver.get.side_effect = Exception("Navigation failed")
        
        with pytest.raises(PageLoadTimeoutException):
            self.page.navigate_to("http://fail.com")
    
    def test_refresh_page(self):
        """페이지 새로고침 테스트"""
        with patch.object(self.page, 'wait_for_page_load'):
            self.page.refresh_page()
        
        self.mock_driver.refresh.assert_called_once()
    
    def test_go_back(self):
        """뒤로가기 테스트"""
        with patch.object(self.page, 'wait_for_page_load'):
            self.page.go_back()
        
        self.mock_driver.back.assert_called_once()
    
    def test_go_forward(self):
        """앞으로가기 테스트"""
        with patch.object(self.page, 'wait_for_page_load'):
            self.page.go_forward()
        
        self.mock_driver.forward.assert_called_once()
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_find_element_success(self, mock_wait):
        """요소 찾기 성공 테스트"""
        mock_element = Mock()
        mock_wait.return_value.until.return_value = mock_element
        
        locator = (By.ID, "test-element")
        result = self.page.find_element(locator)
        
        assert result == mock_element
        mock_wait.assert_called_once_with(self.mock_driver, 10)
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_find_element_timeout(self, mock_wait):
        """요소 찾기 타임아웃 테스트"""
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        locator = (By.ID, "missing-element")
        
        with pytest.raises(ElementNotFoundException):
            self.page.find_element(locator)
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_find_elements_success(self, mock_wait):
        """여러 요소 찾기 성공 테스트"""
        mock_elements = [Mock(), Mock(), Mock()]
        mock_wait.return_value.until.return_value = True
        self.mock_driver.find_elements.return_value = mock_elements
        
        locator = (By.CLASS_NAME, "test-elements")
        result = self.page.find_elements(locator)
        
        assert result == mock_elements
        assert len(result) == 3    

    @patch('src.pages.base_page.WebDriverWait')
    def test_find_elements_timeout(self, mock_wait):
        """여러 요소 찾기 타임아웃 테스트"""
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        locator = (By.CLASS_NAME, "missing-elements")
        result = self.page.find_elements(locator)
        
        assert result == []
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_is_element_present_true(self, mock_wait):
        """요소 존재 확인 - True"""
        mock_wait.return_value.until.return_value = True
        
        locator = (By.ID, "present-element")
        result = self.page.is_element_present(locator)
        
        assert result is True
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_is_element_present_false(self, mock_wait):
        """요소 존재 확인 - False"""
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        locator = (By.ID, "absent-element")
        result = self.page.is_element_present(locator)
        
        assert result is False
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_is_element_visible_true(self, mock_wait):
        """요소 가시성 확인 - True"""
        mock_wait.return_value.until.return_value = True
        
        locator = (By.ID, "visible-element")
        result = self.page.is_element_visible(locator)
        
        assert result is True
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_is_element_clickable_true(self, mock_wait):
        """요소 클릭 가능 확인 - True"""
        mock_wait.return_value.until.return_value = Mock()
        
        locator = (By.ID, "clickable-element")
        result = self.page.is_element_clickable(locator)
        
        assert result is True  
  
    def test_click_element(self):
        """요소 클릭 테스트"""
        mock_element = Mock()
        
        with patch.object(self.page, 'wait_for_element_clickable', return_value=mock_element):
            with patch.object(self.page, 'scroll_to_element'):
                self.page.click_element((By.ID, "click-me"))
        
        mock_element.click.assert_called_once()
    
    def test_input_text_with_clear(self):
        """텍스트 입력 테스트 (기존 텍스트 삭제)"""
        mock_element = Mock()
        
        with patch.object(self.page, 'wait_for_element_clickable', return_value=mock_element):
            self.page.input_text((By.ID, "input-field"), "test text", clear_first=True)
        
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("test text")
    
    def test_input_text_without_clear(self):
        """텍스트 입력 테스트 (기존 텍스트 유지)"""
        mock_element = Mock()
        
        with patch.object(self.page, 'wait_for_element_clickable', return_value=mock_element):
            self.page.input_text((By.ID, "input-field"), "append text", clear_first=False)
        
        mock_element.clear.assert_not_called()
        mock_element.send_keys.assert_called_once_with("append text")
    
    def test_get_text(self):
        """텍스트 가져오기 테스트"""
        mock_element = Mock()
        mock_element.text = "Element Text"
        
        with patch.object(self.page, 'wait_for_element_visible', return_value=mock_element):
            result = self.page.get_text((By.ID, "text-element"))
        
        assert result == "Element Text"
    
    def test_get_attribute(self):
        """속성값 가져오기 테스트"""
        mock_element = Mock()
        mock_element.get_attribute.return_value = "attribute-value"
        
        with patch.object(self.page, 'find_element', return_value=mock_element):
            result = self.page.get_attribute((By.ID, "attr-element"), "data-value")
        
        assert result == "attribute-value"
        mock_element.get_attribute.assert_called_once_with("data-value") 
   
    def test_scroll_to_element_with_locator(self):
        """로케이터로 요소 스크롤 테스트"""
        mock_element = Mock()
        
        with patch.object(self.page, 'find_element', return_value=mock_element):
            self.page.scroll_to_element((By.ID, "scroll-target"))
        
        self.mock_driver.execute_script.assert_called_once()
    
    def test_scroll_to_element_with_element(self):
        """WebElement로 스크롤 테스트"""
        mock_element = Mock()
        
        self.page.scroll_to_element(mock_element)
        
        self.mock_driver.execute_script.assert_called_once()
    
    def test_scroll_to_top(self):
        """페이지 맨 위로 스크롤 테스트"""
        self.page.scroll_to_top()
        
        self.mock_driver.execute_script.assert_called_once_with("window.scrollTo(0, 0);")
    
    def test_scroll_to_bottom(self):
        """페이지 맨 아래로 스크롤 테스트"""
        self.page.scroll_to_bottom()
        
        self.mock_driver.execute_script.assert_called_once_with("window.scrollTo(0, document.body.scrollHeight);")
    
    def test_scroll_by_pixels(self):
        """픽셀 단위 스크롤 테스트"""
        self.page.scroll_by_pixels(100, 200)
        
        self.mock_driver.execute_script.assert_called_once_with("window.scrollBy(100, 200);")
    
    @patch('src.pages.base_page.Select')
    def test_select_dropdown_by_text(self, mock_select_class):
        """드롭다운 텍스트 선택 테스트"""
        mock_element = Mock()
        mock_select = Mock()
        mock_select_class.return_value = mock_select
        
        with patch.object(self.page, 'wait_for_element_clickable', return_value=mock_element):
            self.page.select_dropdown_by_text((By.ID, "dropdown"), "Option 1")
        
        mock_select_class.assert_called_once_with(mock_element)
        mock_select.select_by_visible_text.assert_called_once_with("Option 1")   
 
    def test_take_screenshot_default_filename(self):
        """기본 파일명으로 스크린샷 테스트"""
        self.mock_driver.save_screenshot.return_value = True
        
        with patch('src.pages.base_page.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231222_143000"
            
            result = self.page.take_screenshot()
        
        expected_filename = "BasePage_20231222_143000.png"
        assert expected_filename in result
        self.mock_driver.save_screenshot.assert_called_once()
    
    def test_take_screenshot_custom_filename(self):
        """사용자 지정 파일명으로 스크린샷 테스트"""
        self.mock_driver.save_screenshot.return_value = True
        
        result = self.page.take_screenshot("custom_screenshot")
        
        assert "custom_screenshot.png" in result
        self.mock_driver.save_screenshot.assert_called_once()
    
    def test_get_current_url(self):
        """현재 URL 가져오기 테스트"""
        self.mock_driver.current_url = "http://current.com"
        
        result = self.page.get_current_url()
        
        assert result == "http://current.com"
    
    def test_get_page_title(self):
        """페이지 제목 가져오기 테스트"""
        self.mock_driver.title = "Test Page Title"
        
        result = self.page.get_page_title()
        
        assert result == "Test Page Title"
    
    def test_get_window_size(self):
        """브라우저 창 크기 가져오기 테스트"""
        self.mock_driver.get_window_size.return_value = {"width": 1920, "height": 1080}
        
        result = self.page.get_window_size()
        
        assert result == {"width": 1920, "height": 1080}
    
    def test_set_window_size(self):
        """브라우저 창 크기 설정 테스트"""
        self.page.set_window_size(1366, 768)
        
        self.mock_driver.set_window_size.assert_called_once_with(1366, 768)    
 
   def test_maximize_window(self):
        """브라우저 창 최대화 테스트"""
        self.page.maximize_window()
        
        self.mock_driver.maximize_window.assert_called_once()
    
    def test_get_cookie(self):
        """쿠키 가져오기 테스트"""
        expected_cookie = {"name": "test_cookie", "value": "test_value"}
        self.mock_driver.get_cookie.return_value = expected_cookie
        
        result = self.page.get_cookie("test_cookie")
        
        assert result == expected_cookie
        self.mock_driver.get_cookie.assert_called_once_with("test_cookie")
    
    def test_add_cookie(self):
        """쿠키 추가 테스트"""
        cookie_dict = {"name": "new_cookie", "value": "new_value"}
        
        self.page.add_cookie(cookie_dict)
        
        self.mock_driver.add_cookie.assert_called_once_with(cookie_dict)
    
    def test_delete_cookie(self):
        """쿠키 삭제 테스트"""
        self.page.delete_cookie("test_cookie")
        
        self.mock_driver.delete_cookie.assert_called_once_with("test_cookie")
    
    def test_execute_script(self):
        """JavaScript 실행 테스트"""
        self.mock_driver.execute_script.return_value = "script_result"
        
        result = self.page.execute_script("return document.title;")
        
        assert result == "script_result"
        self.mock_driver.execute_script.assert_called_once_with("return document.title;")
    
    def test_get_local_storage_item(self):
        """로컬 스토리지 아이템 가져오기 테스트"""
        self.mock_driver.execute_script.return_value = "stored_value"
        
        result = self.page.get_local_storage_item("test_key")
        
        assert result == "stored_value"
        expected_script = "return localStorage.getItem('test_key');"
        self.mock_driver.execute_script.assert_called_once_with(expected_script)  
  
    def test_set_local_storage_item(self):
        """로컬 스토리지 아이템 설정 테스트"""
        self.page.set_local_storage_item("test_key", "test_value")
        
        expected_script = "localStorage.setItem('test_key', 'test_value');"
        self.mock_driver.execute_script.assert_called_once_with(expected_script)
    
    def test_wait(self):
        """대기 테스트"""
        with patch('src.pages.base_page.time.sleep') as mock_sleep:
            self.page.wait(2.5)
        
        mock_sleep.assert_called_once_with(2.5)
    
    def test_switch_to_frame_by_locator(self):
        """로케이터로 프레임 전환 테스트"""
        mock_frame_element = Mock()
        
        with patch.object(self.page, 'find_element', return_value=mock_frame_element):
            self.page.switch_to_frame((By.ID, "frame-id"))
        
        self.mock_driver.switch_to.frame.assert_called_once_with(mock_frame_element)
    
    def test_switch_to_frame_by_name(self):
        """이름으로 프레임 전환 테스트"""
        self.page.switch_to_frame("frame_name")
        
        self.mock_driver.switch_to.frame.assert_called_once_with("frame_name")
    
    def test_switch_to_default_content(self):
        """기본 컨텐츠로 전환 테스트"""
        self.page.switch_to_default_content()
        
        self.mock_driver.switch_to.default_content.assert_called_once()
    
    def test_accept_alert(self):
        """알림창 수락 테스트"""
        mock_alert = Mock()
        mock_alert.text = "Alert message"
        self.mock_driver.switch_to.alert = mock_alert
        
        result = self.page.accept_alert()
        
        assert result == "Alert message"
        mock_alert.accept.assert_called_once()
    
    def test_verify_page_loaded_success(self):
        """페이지 로딩 검증 성공 테스트"""
        self.mock_driver.current_url = "http://test.com/page"
        self.mock_driver.title = "Test Page Title"
        
        with patch.object(self.page, 'wait_for_page_load'):
            result = self.page.verify_page_loaded("test.com", "Test Page")
        
        assert result is True    

    def test_verify_element_text_success(self):
        """요소 텍스트 검증 성공 테스트"""
        with patch.object(self.page, 'get_text', return_value="Expected text content"):
            result = self.page.verify_element_text((By.ID, "text-element"), "Expected text")
        
        assert result is True
    
    def test_verify_element_text_failure(self):
        """요소 텍스트 검증 실패 테스트"""
        with patch.object(self.page, 'get_text', return_value="Different text"):
            result = self.page.verify_element_text((By.ID, "text-element"), "Expected text")
        
        assert result is False
    
    def test_str_representation(self):
        """문자열 표현 테스트"""
        self.mock_driver.current_url = "http://test.com"
        
        result = str(self.page)
        
        assert "BasePage" in result
        assert "http://test.com" in result
    
    def test_repr_representation(self):
        """객체 표현 테스트"""
        self.mock_driver.current_url = "http://test.com"
        
        result = repr(self.page)
        
        assert "BasePage" in result
        assert "http://test.com" in result


class TestBasePageWaitMethods:
    """BasePage 대기 메서드 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.mock_config_manager = Mock()
        
        self.mock_config_manager.get_base_url.return_value = "http://test.com"
        self.mock_config_manager.get_timeout.return_value = 10
        
        with patch('src.pages.base_page.get_config_manager', return_value=self.mock_config_manager):
            self.page = BasePage(self.mock_driver)
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_wait_for_element_present_success(self, mock_wait):
        """요소 존재 대기 성공 테스트"""
        mock_element = Mock()
        mock_wait.return_value.until.return_value = mock_element
        
        result = self.page.wait_for_element_present((By.ID, "test-element"))
        
        assert result == mock_element
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_wait_for_element_present_timeout(self, mock_wait):
        """요소 존재 대기 타임아웃 테스트"""
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        with pytest.raises(ElementNotFoundException):
            self.page.wait_for_element_present((By.ID, "missing-element")) 
   
    @patch('src.pages.base_page.WebDriverWait')
    def test_wait_for_page_load_complete(self, mock_wait):
        """페이지 로딩 완료 대기 테스트"""
        # document.readyState가 complete를 반환하도록 설정
        self.mock_driver.execute_script.side_effect = ["complete", 0]  # readyState, jQuery.active
        mock_wait.return_value.until.return_value = True
        
        self.page.wait_for_page_load()
        
        # execute_script가 호출되었는지 확인
        assert self.mock_driver.execute_script.call_count >= 1
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_wait_for_text_present_success(self, mock_wait):
        """텍스트 존재 대기 성공 테스트"""
        mock_wait.return_value.until.return_value = True
        
        result = self.page.wait_for_text_present((By.ID, "text-element"), "Expected Text")
        
        assert result is True
    
    @patch('src.pages.base_page.WebDriverWait')
    def test_wait_for_text_present_timeout(self, mock_wait):
        """텍스트 존재 대기 타임아웃 테스트"""
        mock_wait.return_value.until.side_effect = TimeoutException()
        
        result = self.page.wait_for_text_present((By.ID, "text-element"), "Missing Text")
        
        assert result is False


class TestBasePageActionChains:
    """BasePage ActionChains 관련 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.mock_config_manager = Mock()
        
        self.mock_config_manager.get_base_url.return_value = "http://test.com"
        self.mock_config_manager.get_timeout.return_value = 10
        
        with patch('src.pages.base_page.get_config_manager', return_value=self.mock_config_manager):
            self.page = BasePage(self.mock_driver)
    
    @patch('src.pages.base_page.ActionChains')
    def test_double_click_element(self, mock_action_chains):
        """더블클릭 테스트"""
        mock_element = Mock()
        mock_actions = Mock()
        mock_action_chains.return_value = mock_actions
        
        with patch.object(self.page, 'wait_for_element_clickable', return_value=mock_element):
            self.page.double_click_element((By.ID, "double-click-me"))
        
        mock_action_chains.assert_called_once_with(self.mock_driver)
        mock_actions.double_click.assert_called_once_with(mock_element)
        mock_actions.perform.assert_called_once()
    
    @patch('src.pages.base_page.ActionChains')
    def test_hover_over_element(self, mock_action_chains):
        """마우스 호버 테스트"""
        mock_element = Mock()
        mock_actions = Mock()
        mock_action_chains.return_value = mock_actions
        
        with patch.object(self.page, 'wait_for_element_visible', return_value=mock_element):
            self.page.hover_over_element((By.ID, "hover-target"))
        
        mock_actions.move_to_element.assert_called_once_with(mock_element)
        mock_actions.perform.assert_called_once()