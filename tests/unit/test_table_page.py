"""
TablePage 클래스 단위 테스트

이 모듈은 TablePage 클래스의 핵심 기능에 대한
단위 테스트를 제공합니다.
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from src.pages.table_page import TablePage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestTablePage:
    """TablePage 클래스 테스트"""
    
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
                    self.table_page = TablePage(self.mock_driver, "http://test.com")
    
    def test_table_page_initialization(self):
        """TablePage 초기화 테스트"""
        assert self.table_page.driver == self.mock_driver
        assert self.table_page.base_url == "http://test.com"
        assert hasattr(self.table_page, 'logger')
    
    def test_navigate_to_table_default_url(self):
        """기본 URL로 테이블 페이지 이동 테스트"""
        with patch.object(self.table_page, 'navigate_to') as mock_navigate:
            with patch.object(self.table_page, 'wait_for_table_load'):
                self.table_page.navigate_to_table()
        
        mock_navigate.assert_called_once_with("http://test.com/data")
    
    def test_get_table_headers(self):
        """테이블 헤더 가져오기 테스트"""
        mock_header1 = Mock()
        mock_header1.text = "이름"
        mock_header2 = Mock()
        mock_header2.text = "이메일"
        mock_header3 = Mock()
        mock_header3.text = "전화번호"
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_elements', return_value=[mock_header1, mock_header2, mock_header3]):
                headers = self.table_page.get_table_headers()
        
        assert len(headers) == 3
        assert headers == ["이름", "이메일", "전화번호"]
    
    def test_get_table_data(self):
        """테이블 데이터 가져오기 테스트"""
        # Mock 헤더
        mock_header1 = Mock()
        mock_header1.text = "이름"
        mock_header2 = Mock()
        mock_header2.text = "이메일"
        
        # Mock 셀
        mock_cell1 = Mock()
        mock_cell1.text = "홍길동"
        mock_cell2 = Mock()
        mock_cell2.text = "hong@example.com"
        mock_cell3 = Mock()
        mock_cell3.text = "김철수"
        mock_cell4 = Mock()
        mock_cell4.text = "kim@example.com"
        
        # Mock 행
        mock_row1 = Mock()
        mock_row1.find_elements.return_value = [mock_cell1, mock_cell2]
        mock_row2 = Mock()
        mock_row2.find_elements.return_value = [mock_cell3, mock_cell4]
        
        with patch.object(self.table_page, 'get_table_headers', return_value=["이름", "이메일"]):
            with patch.object(self.table_page, 'is_element_present', return_value=True):
                with patch.object(self.table_page, 'find_elements', return_value=[mock_row1, mock_row2]):
                    table_data = self.table_page.get_table_data()
        
        assert len(table_data) == 2
        assert table_data[0]["이름"] == "홍길동"
        assert table_data[0]["이메일"] == "hong@example.com"
        assert table_data[1]["이름"] == "김철수"
        assert table_data[1]["이메일"] == "kim@example.com"
    
    def test_get_row_data(self):
        """특정 행 데이터 가져오기 테스트"""
        mock_cell1 = Mock()
        mock_cell1.text = "홍길동"
        mock_cell2 = Mock()
        mock_cell2.text = "hong@example.com"
        
        mock_row = Mock()
        mock_row.find_elements.return_value = [mock_cell1, mock_cell2]
        
        with patch.object(self.table_page, 'get_table_headers', return_value=["이름", "이메일"]):
            with patch.object(self.table_page, 'is_element_present', return_value=True):
                with patch.object(self.table_page, 'find_elements', return_value=[mock_row]):
                    row_data = self.table_page.get_row_data(0)
        
        assert row_data["이름"] == "홍길동"
        assert row_data["이메일"] == "hong@example.com"
    
    def test_get_column_data(self):
        """특정 컬럼 데이터 가져오기 테스트"""
        mock_cell1 = Mock()
        mock_cell1.text = "홍길동"
        mock_cell2 = Mock()
        mock_cell2.text = "김철수"
        
        mock_row1 = Mock()
        mock_row1.find_elements.return_value = [mock_cell1, Mock()]
        mock_row2 = Mock()
        mock_row2.find_elements.return_value = [mock_cell2, Mock()]
        
        with patch.object(self.table_page, 'get_table_headers', return_value=["이름", "이메일"]):
            with patch.object(self.table_page, 'is_element_present', return_value=True):
                with patch.object(self.table_page, 'find_elements', return_value=[mock_row1, mock_row2]):
                    column_data = self.table_page.get_column_data("이름")
        
        assert len(column_data) == 2
        assert column_data == ["홍길동", "김철수"]
    
    def test_search_table_success(self):
        """테이블 검색 성공 테스트"""
        with patch.object(self.table_page, 'is_element_present', side_effect=[True, True]):  # search input, search button
            with patch.object(self.table_page, 'input_text') as mock_input:
                with patch.object(self.table_page, 'click_element') as mock_click:
                    with patch.object(self.table_page, 'wait'):
                        result = self.table_page.search_table("홍길동")
        
        mock_input.assert_called_once_with(self.table_page.SEARCH_INPUT, "홍길동", clear_first=True)
        mock_click.assert_called_once_with(self.table_page.SEARCH_BUTTON)
        assert result is True
    
    def test_search_table_with_enter_key(self):
        """Enter 키로 테이블 검색 테스트"""
        with patch.object(self.table_page, 'is_element_present', side_effect=[True, False]):  # search input exists, no search button
            with patch.object(self.table_page, 'input_text'):
                with patch.object(self.table_page, 'send_keys') as mock_send_keys:
                    with patch.object(self.table_page, 'wait'):
                        result = self.table_page.search_table("홍길동")
        
        mock_send_keys.assert_called_once()
        assert result is True
    
    def test_apply_filter_success(self):
        """필터 적용 성공 테스트"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'select_dropdown_by_text') as mock_select:
                with patch.object(self.table_page, 'wait'):
                    result = self.table_page.apply_filter("활성")
        
        mock_select.assert_called_once_with(self.table_page.FILTER_DROPDOWN, "활성")
        assert result is True
    
    def test_clear_filters_success(self):
        """필터 초기화 성공 테스트"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'click_element') as mock_click:
                with patch.object(self.table_page, 'wait'):
                    result = self.table_page.clear_filters()
        
        mock_click.assert_called_once_with(self.table_page.CLEAR_FILTER_BUTTON)
        assert result is True
    
    def test_sort_by_column_success(self):
        """컬럼별 정렬 성공 테스트"""
        mock_header = Mock()
        mock_sort_button = Mock()
        mock_header.find_element.return_value = mock_sort_button
        
        with patch.object(self.table_page, 'get_table_headers', return_value=["이름", "이메일"]):
            with patch.object(self.table_page, 'find_elements', return_value=[mock_header, Mock()]):
                with patch.object(self.table_page, 'wait'):
                    result = self.table_page.sort_by_column("이름")
        
        mock_sort_button.click.assert_called_once()
        assert result is True
    
    def test_go_to_next_page_success(self):
        """다음 페이지 이동 성공 테스트"""
        mock_next_button = Mock()
        mock_next_button.is_enabled.return_value = True
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_element', return_value=mock_next_button):
                with patch.object(self.table_page, 'click_element') as mock_click:
                    with patch.object(self.table_page, 'wait'):
                        result = self.table_page.go_to_next_page()
        
        mock_click.assert_called_once_with(self.table_page.NEXT_PAGE_BUTTON)
        assert result is True
    
    def test_go_to_next_page_disabled(self):
        """다음 페이지 버튼 비활성화 테스트"""
        mock_next_button = Mock()
        mock_next_button.is_enabled.return_value = False
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_element', return_value=mock_next_button):
                result = self.table_page.go_to_next_page()
        
        assert result is False
    
    def test_go_to_previous_page_success(self):
        """이전 페이지 이동 성공 테스트"""
        mock_prev_button = Mock()
        mock_prev_button.is_enabled.return_value = True
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_element', return_value=mock_prev_button):
                with patch.object(self.table_page, 'click_element') as mock_click:
                    with patch.object(self.table_page, 'wait'):
                        result = self.table_page.go_to_previous_page()
        
        mock_click.assert_called_once_with(self.table_page.PREV_PAGE_BUTTON)
        assert result is True
    
    def test_go_to_page_success(self):
        """특정 페이지 이동 성공 테스트"""
        mock_page1 = Mock()
        mock_page1.text = "1"
        mock_page2 = Mock()
        mock_page2.text = "2"
        mock_page3 = Mock()
        mock_page3.text = "3"
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_elements', return_value=[mock_page1, mock_page2, mock_page3]):
                with patch.object(self.table_page, 'wait'):
                    result = self.table_page.go_to_page(2)
        
        mock_page2.click.assert_called_once()
        assert result is True
    
    def test_get_current_page(self):
        """현재 페이지 번호 가져오기 테스트"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'get_text', return_value="Page 3 of 10"):
                current_page = self.table_page.get_current_page()
        
        assert current_page == 3
    
    def test_select_row_success(self):
        """행 선택 성공 테스트"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = False
        
        mock_row = Mock()
        mock_row.find_element.return_value = mock_checkbox
        
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'find_elements', return_value=[mock_row]):
                result = self.table_page.select_row(0)
        
        mock_checkbox.click.assert_called_once()
        assert result is True
    
    def test_select_all_rows_success(self):
        """모든 행 선택 성공 테스트"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'click_element') as mock_click:
                result = self.table_page.select_all_rows()
        
        mock_click.assert_called_once_with(self.table_page.SELECT_ALL_CHECKBOX)
        assert result is True
    
    def test_get_total_records_from_element(self):
        """총 레코드 수 가져오기 - 요소에서"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            with patch.object(self.table_page, 'get_text', return_value="Total: 150 records"):
                total = self.table_page.get_total_records()
        
        assert total == 150
    
    def test_get_total_records_from_rows(self):
        """총 레코드 수 가져오기 - 행 개수에서"""
        mock_rows = [Mock(), Mock(), Mock()]
        
        with patch.object(self.table_page, 'is_element_present', side_effect=[False, True]):  # no total element, has rows
            with patch.object(self.table_page, 'find_elements', return_value=mock_rows):
                total = self.table_page.get_total_records()
        
        assert total == 3
    
    def test_is_table_empty_true(self):
        """테이블 비어있음 확인 - 비어있음"""
        with patch.object(self.table_page, 'is_element_present', return_value=True):
            result = self.table_page.is_table_empty()
        
        assert result is True
    
    def test_is_table_empty_false(self):
        """테이블 비어있음 확인 - 데이터 있음"""
        with patch.object(self.table_page, 'is_element_present', return_value=False):
            with patch.object(self.table_page, 'get_total_records', return_value=5):
                result = self.table_page.is_table_empty()
        
        assert result is False
    
    def test_get_table_summary(self):
        """테이블 요약 정보 가져오기 테스트"""
        mock_rows = [Mock(), Mock()]
        
        with patch.object(self.table_page, 'get_total_records', return_value=10):
            with patch.object(self.table_page, 'get_current_page', return_value=2):
                with patch.object(self.table_page, 'get_table_headers', return_value=["이름", "이메일"]):
                    with patch.object(self.table_page, 'is_table_empty', return_value=False):
                        with patch.object(self.table_page, 'is_element_present', return_value=True):
                            with patch.object(self.table_page, 'find_elements', return_value=mock_rows):
                                summary = self.table_page.get_table_summary()
        
        assert summary['total_records'] == 10
        assert summary['current_page'] == 2
        assert summary['headers'] == ["이름", "이메일"]
        assert summary['is_empty'] is False
        assert summary['visible_rows'] == 2