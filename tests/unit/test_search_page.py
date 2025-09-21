"""
SearchPage 클래스 단위 테스트

이 모듈은 SearchPage 클래스의 모든 기능에 대한
포괄적인 단위 테스트를 제공합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from src.pages.search_page import SearchPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestSearchPage:
    """SearchPage 클래스 테스트"""
    
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
                    self.search_page = SearchPage(self.mock_driver, "http://test.com")
    
    def test_search_page_initialization(self):
        """SearchPage 초기화 테스트"""
        assert self.search_page.driver == self.mock_driver
        assert self.search_page.base_url == "http://test.com"
        assert self.search_page.search_timeout == 30
        assert self.search_page.suggestion_timeout == 5
        assert hasattr(self.search_page, 'logger')
    
    def test_navigate_to_search_default_url(self):
        """기본 URL로 검색 페이지 이동 테스트"""
        with patch.object(self.search_page, 'navigate_to') as mock_navigate:
            with patch.object(self.search_page, 'wait_for_search_page_load'):
                self.search_page.navigate_to_search()
        
        mock_navigate.assert_called_once_with("http://test.com/search")
    
    def test_navigate_to_search_custom_url(self):
        """사용자 지정 URL로 검색 페이지 이동 테스트"""
        custom_url = "http://custom.com/find"
        
        with patch.object(self.search_page, 'navigate_to') as mock_navigate:
            with patch.object(self.search_page, 'wait_for_search_page_load'):
                self.search_page.navigate_to_search(custom_url)
        
        mock_navigate.assert_called_once_with(custom_url)
    
    def test_navigate_to_search_page_load_failure(self):
        """검색 페이지 로딩 실패 테스트"""
        with patch.object(self.search_page, 'navigate_to'):
            with patch.object(self.search_page, 'wait_for_search_page_load', side_effect=ElementNotFoundException("Not found")):
                with pytest.raises(PageLoadTimeoutException):
                    self.search_page.navigate_to_search()
    
    def test_find_search_input_default_locator(self):
        """기본 로케이터로 검색 입력 필드 찾기 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            result = self.search_page._find_search_input()
        
        assert result == self.search_page.SEARCH_INPUT
    
    def test_find_search_input_alternative_locator(self):
        """대체 로케이터로 검색 입력 필드 찾기 테스트"""
        # 기본 로케이터는 실패, 첫 번째 대체 로케이터는 성공
        with patch.object(self.search_page, 'is_element_present', side_effect=[False, True]):
            result = self.search_page._find_search_input()
        
        assert result == self.search_page.ALT_SEARCH_INPUT_LOCATORS[0]
    
    def test_find_search_input_not_found(self):
        """검색 입력 필드를 찾을 수 없는 경우 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=False):
            with pytest.raises(ElementNotFoundException):
                self.search_page._find_search_input()
    
    def test_enter_search_term(self):
        """검색어 입력 테스트"""
        search_input_locator = (By.ID, "search")
        
        with patch.object(self.search_page, '_find_search_input', return_value=search_input_locator):
            with patch.object(self.search_page, 'input_text') as mock_input:
                self.search_page.enter_search_term("test query")
        
        mock_input.assert_called_once_with(search_input_locator, "test query", clear_first=True)
    
    def test_click_search_button(self):
        """검색 버튼 클릭 테스트"""
        search_button_locator = (By.ID, "search-btn")
        
        with patch.object(self.search_page, '_find_search_button', return_value=search_button_locator):
            with patch.object(self.search_page, 'click_element') as mock_click:
                self.search_page.click_search_button()
        
        mock_click.assert_called_once_with(search_button_locator)
    
    def test_search_successful(self):
        """검색 성공 테스트"""
        with patch.object(self.search_page, 'enter_search_term'):
            with patch.object(self.search_page, 'click_search_button'):
                with patch.object(self.search_page, '_wait_for_search_results'):
                    with patch.object(self.search_page, 'has_search_results', return_value=True):
                        
                        result = self.search_page.search("test query")
        
        assert result is True
    
    def test_search_no_results(self):
        """검색 결과 없음 테스트"""
        with patch.object(self.search_page, 'enter_search_term'):
            with patch.object(self.search_page, 'click_search_button'):
                with patch.object(self.search_page, '_wait_for_search_results'):
                    with patch.object(self.search_page, 'has_search_results', return_value=False):
                        
                        result = self.search_page.search("no results query")
        
        assert result is False
    
    def test_search_with_enter_key(self):
        """Enter 키로 검색 테스트"""
        with patch.object(self.search_page, 'enter_search_term'):
            with patch.object(self.search_page, 'press_enter_to_search') as mock_enter:
                with patch.object(self.search_page, '_wait_for_search_results'):
                    with patch.object(self.search_page, 'has_search_results', return_value=True):
                        
                        result = self.search_page.search("test query", use_enter=True)
        
        mock_enter.assert_called_once()
        assert result is True
    
    def test_has_search_results_true(self):
        """검색 결과 존재 확인 - 있음"""
        with patch.object(self.search_page, 'is_element_present', side_effect=[False, True]):  # no_results=False, results_container=True
            with patch.object(self.search_page, '_find_search_results_container', return_value=(By.CSS_SELECTOR, ".results")):
                with patch.object(self.search_page, '_find_result_items', return_value=[(By.CSS_SELECTOR, ".item")]):
                    with patch.object(self.search_page, 'find_elements', return_value=[Mock(), Mock()]):
                        
                        result = self.search_page.has_search_results()
        
        assert result is True
    
    def test_has_search_results_false_no_results_message(self):
        """검색 결과 존재 확인 - "결과 없음" 메시지 있음"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):  # no_results message present
            result = self.search_page.has_search_results()
        
        assert result is False
    
    def test_get_search_results_count(self):
        """검색 결과 개수 가져오기 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'get_text', return_value="123 results found"):
                result = self.search_page.get_search_results_count()
        
        assert result == 123
    
    def test_get_search_results_count_by_counting_elements(self):
        """요소 개수로 검색 결과 개수 가져오기 테스트"""
        mock_elements = [Mock(), Mock(), Mock()]
        
        with patch.object(self.search_page, 'is_element_present', return_value=False):  # no count element
            with patch.object(self.search_page, '_find_result_items', return_value=[(By.CSS_SELECTOR, ".item")]):
                with patch.object(self.search_page, 'find_elements', return_value=mock_elements):
                    result = self.search_page.get_search_results_count()
        
        assert result == 3
    
    def test_get_search_result_titles(self):
        """검색 결과 제목들 가져오기 테스트"""
        mock_elements = [Mock(), Mock()]
        mock_elements[0].text = "First Result"
        mock_elements[1].text = "Second Result"
        
        with patch.object(self.search_page, 'find_elements', return_value=mock_elements):
            result = self.search_page.get_search_result_titles()
        
        assert result == ["First Result", "Second Result"]
    
    def test_click_search_result(self):
        """검색 결과 클릭 테스트"""
        mock_result_element = Mock()
        mock_link_element = Mock()
        mock_result_element.find_element.return_value = mock_link_element
        
        with patch.object(self.search_page, '_find_result_items', return_value=[(By.CSS_SELECTOR, ".item")]):
            with patch.object(self.search_page, 'find_elements', return_value=[mock_result_element]):
                with patch.object(self.search_page, 'scroll_to_element'):
                    self.search_page.click_search_result(0)
        
        mock_link_element.click.assert_called_once()
    
    def test_apply_price_filter(self):
        """가격 필터 적용 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'click_element'):
                with patch.object(self.search_page, 'input_text'):
                    self.search_page.apply_price_filter(min_price=10.0, max_price=100.0)
        
        # 메서드가 예외 없이 실행되었는지 확인
        assert True
    
    def test_select_category_filter(self):
        """카테고리 필터 선택 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'click_element'):
                self.search_page.select_category_filter("Electronics")
        
        # 메서드가 예외 없이 실행되었는지 확인
        assert True
    
    def test_sort_results(self):
        """검색 결과 정렬 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'click_element'):
                self.search_page.sort_results("price_low_to_high")
        
        # 메서드가 예외 없이 실행되었는지 확인
        assert True
    
    def test_go_to_next_page_success(self):
        """다음 페이지 이동 성공 테스트"""
        mock_button = Mock()
        mock_button.is_enabled.return_value = True
        mock_button.get_attribute.return_value = "enabled"
        
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'find_element', return_value=mock_button):
                with patch.object(self.search_page, 'click_element'):
                    with patch.object(self.search_page, '_wait_for_search_results'):
                        result = self.search_page.go_to_next_page()
        
        assert result is True
    
    def test_go_to_next_page_disabled(self):
        """다음 페이지 버튼 비활성화 테스트"""
        mock_button = Mock()
        mock_button.is_enabled.return_value = False
        
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'find_element', return_value=mock_button):
                result = self.search_page.go_to_next_page()
        
        assert result is False
    
    def test_get_search_suggestions(self):
        """검색 제안 가져오기 테스트"""
        mock_elements = [Mock(), Mock()]
        mock_elements[0].text = "suggestion 1"
        mock_elements[1].text = "suggestion 2"
        
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'find_elements', return_value=mock_elements):
                result = self.search_page.get_search_suggestions()
        
        assert result == ["suggestion 1", "suggestion 2"]
    
    def test_select_search_suggestion(self):
        """검색 제안 선택 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'click_element') as mock_click:
                result = self.search_page.select_search_suggestion("test suggestion")
        
        mock_click.assert_called_once()
        assert result is True
    
    def test_clear_search(self):
        """검색어 초기화 테스트"""
        with patch.object(self.search_page, 'is_element_present', return_value=True):
            with patch.object(self.search_page, 'click_element') as mock_click:
                self.search_page.clear_search()
        
        mock_click.assert_called_once_with(self.search_page.CLEAR_SEARCH_BUTTON)
    
    def test_clear_search_no_button(self):
        """검색 초기화 버튼이 없는 경우 테스트"""
        mock_input = Mock()
        
        with patch.object(self.search_page, 'is_element_present', return_value=False):
            with patch.object(self.search_page, '_find_search_input', return_value=(By.ID, "search")):
                with patch.object(self.search_page, 'find_element', return_value=mock_input):
                    self.search_page.clear_search()
        
        mock_input.clear.assert_called_once()
    
    def test_get_search_result_info(self):
        """검색 결과 상세 정보 가져오기 테스트"""
        mock_result_element = Mock()
        mock_title_element = Mock()
        mock_price_element = Mock()
        mock_image_element = Mock()
        mock_link_element = Mock()
        
        mock_title_element.text = "Test Product"
        mock_price_element.text = "$19.99"
        mock_image_element.get_attribute.return_value = "http://test.com/image.jpg"
        mock_link_element.get_attribute.return_value = "http://test.com/product/1"
        
        mock_result_element.find_element.side_effect = [
            mock_title_element,
            mock_price_element,
            mock_image_element,
            mock_link_element
        ]
        
        with patch.object(self.search_page, '_find_result_items', return_value=[(By.CSS_SELECTOR, ".item")]):
            with patch.object(self.search_page, 'find_elements', return_value=[mock_result_element]):
                result = self.search_page.get_search_result_info(0)
        
        assert result['title'] == "Test Product"
        assert result['price'] == "$19.99"
        assert result['image_url'] == "http://test.com/image.jpg"
        assert result['link_url'] == "http://test.com/product/1"
        assert result['index'] == 0
    
    def test_take_search_screenshot(self):
        """검색 페이지 스크린샷 테스트"""
        with patch.object(self.search_page, 'take_screenshot', return_value="/path/to/screenshot.png") as mock_screenshot:
            result = self.search_page.take_search_screenshot("test_search.png")
        
        mock_screenshot.assert_called_once_with("test_search.png")
        assert result == "/path/to/screenshot.png"
    
    def test_str_representation(self):
        """문자열 표현 테스트"""
        with patch.object(self.search_page, 'get_current_url', return_value="http://test.com/search"):
            result = str(self.search_page)
        
        assert result == "SearchPage(url=http://test.com/search)"