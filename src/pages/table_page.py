"""
TablePage 클래스 - 데이터 테이블 페이지 Page Object

이 모듈은 데이터 테이블 페이지의 UI 요소와 동작을 캡슐화합니다.
테이블 데이터 읽기, 정렬, 필터링, 페이지네이션 등의 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from .base_page import BasePage
from ..core.logging import get_logger
from ..core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TablePage(BasePage):
    """
    데이터 테이블 페이지 Page Object 클래스
    
    테이블 기능의 모든 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 테이블 컨테이너
    TABLE_CONTAINER = (By.CSS_SELECTOR, ".table-container")
    DATA_TABLE = (By.CSS_SELECTOR, "table")
    TABLE_HEADER = (By.CSS_SELECTOR, "thead")
    TABLE_BODY = (By.CSS_SELECTOR, "tbody")
    
    # 테이블 행과 열
    TABLE_ROWS = (By.CSS_SELECTOR, "tbody tr")
    TABLE_HEADERS = (By.CSS_SELECTOR, "thead th")
    TABLE_CELLS = (By.CSS_SELECTOR, "td")
    
    # 검색 및 필터
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-input")
    SEARCH_BUTTON = (By.CSS_SELECTOR, ".search-button")
    FILTER_DROPDOWN = (By.CSS_SELECTOR, ".filter-select")
    CLEAR_FILTER_BUTTON = (By.CSS_SELECTOR, ".clear-filter")
    
    # 정렬
    SORT_BUTTONS = (By.CSS_SELECTOR, ".sort-button")
    SORT_ASC = (By.CSS_SELECTOR, ".sort-asc")
    SORT_DESC = (By.CSS_SELECTOR, ".sort-desc")
    
    # 페이지네이션
    PAGINATION_CONTAINER = (By.CSS_SELECTOR, ".pagination")
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, ".prev-page")
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".next-page")
    PAGE_NUMBERS = (By.CSS_SELECTOR, ".page-number")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".current-page")
    
    # 행 선택 및 액션
    ROW_CHECKBOXES = (By.CSS_SELECTOR, "input[type='checkbox']")
    SELECT_ALL_CHECKBOX = (By.CSS_SELECTOR, ".select-all")
    ACTION_BUTTONS = (By.CSS_SELECTOR, ".action-button")
    DELETE_BUTTON = (By.CSS_SELECTOR, ".delete-button")
    EDIT_BUTTON = (By.CSS_SELECTOR, ".edit-button")
    
    # 테이블 정보
    TOTAL_RECORDS = (By.CSS_SELECTOR, ".total-records")
    RECORDS_PER_PAGE = (By.CSS_SELECTOR, ".records-per-page")
    NO_DATA_MESSAGE = (By.CSS_SELECTOR, ".no-data")
    
    # 대체 로케이터들
    ALT_TABLE_LOCATORS = [
        (By.CSS_SELECTOR, ".data-table"),
        (By.CSS_SELECTOR, ".grid"),
        (By.CSS_SELECTOR, "[data-testid='table']"),
        (By.XPATH, "//table")
    ]
    
    ALT_SEARCH_LOCATORS = [
        (By.CSS_SELECTOR, "input[placeholder*='Search' i]"),
        (By.CSS_SELECTOR, ".filter-input"),
        (By.XPATH, "//input[contains(@placeholder, 'Search')]")
    ]

    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        TablePage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 테이블 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("TablePage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_table(self, table_url: str = None) -> None:
        """
        테이블 페이지로 이동
        
        Args:
            table_url: 테이블 페이지 URL (None이면 기본 URL 사용)
        """
        url = table_url or f"{self.base_url}/data"
        self.logger.info(f"Navigating to table page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_table_load()
            self.logger.info("Successfully navigated to table page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to table page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_table_load(self) -> None:
        """테이블 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for table page to load")
        
        try:
            self.wait_for_page_load()
            self._find_table()
            self.logger.debug("Table page loaded successfully")
        except Exception as e:
            self.logger.error(f"Table page load failed: {str(e)}")
            raise PageLoadTimeoutException("table page", self.default_timeout)
    
    def _find_table(self) -> tuple:
        """테이블 찾기"""
        if self.is_element_present(self.DATA_TABLE, timeout=2):
            return self.DATA_TABLE
        
        for locator in self.ALT_TABLE_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found table with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("data table", timeout=self.default_timeout)
    
    # ==================== 테이블 데이터 읽기 ====================
    
    def get_table_headers(self) -> List[str]:
        """
        테이블 헤더 가져오기
        
        Returns:
            헤더 텍스트 리스트
        """
        headers = []
        
        try:
            if self.is_element_present(self.TABLE_HEADERS, timeout=2):
                header_elements = self.find_elements(self.TABLE_HEADERS)
                for header in header_elements:
                    header_text = header.text.strip()
                    if header_text:
                        headers.append(header_text)
            
            self.logger.debug(f"Found {len(headers)} table headers")
            return headers
            
        except Exception as e:
            self.logger.error(f"Failed to get table headers: {str(e)}")
            return headers
    
    def get_table_data(self) -> List[Dict[str, str]]:
        """
        테이블 전체 데이터 가져오기
        
        Returns:
            테이블 데이터 리스트 (각 행은 딕셔너리)
        """
        table_data = []
        
        try:
            headers = self.get_table_headers()
            
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                
                for row in row_elements:
                    cell_elements = row.find_elements(*self.TABLE_CELLS)
                    row_data = {}
                    
                    for i, cell in enumerate(cell_elements):
                        header_key = headers[i] if i < len(headers) else f"column_{i}"
                        row_data[header_key] = cell.text.strip()
                    
                    if row_data:  # 빈 행 제외
                        table_data.append(row_data)
            
            self.logger.debug(f"Retrieved {len(table_data)} rows of table data")
            return table_data
            
        except Exception as e:
            self.logger.error(f"Failed to get table data: {str(e)}")
            return table_data
    
    def get_row_data(self, row_index: int) -> Dict[str, str]:
        """
        특정 행의 데이터 가져오기
        
        Args:
            row_index: 행 인덱스 (0부터 시작)
            
        Returns:
            행 데이터 딕셔너리
        """
        try:
            headers = self.get_table_headers()
            
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                
                if row_index < len(row_elements):
                    row = row_elements[row_index]
                    cell_elements = row.find_elements(*self.TABLE_CELLS)
                    row_data = {}
                    
                    for i, cell in enumerate(cell_elements):
                        header_key = headers[i] if i < len(headers) else f"column_{i}"
                        row_data[header_key] = cell.text.strip()
                    
                    self.logger.debug(f"Retrieved data for row {row_index}")
                    return row_data
                else:
                    self.logger.warning(f"Row index {row_index} out of range")
                    return {}
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get row data: {str(e)}")
            return {}
    
    def get_column_data(self, column_name: str) -> List[str]:
        """
        특정 컬럼의 모든 데이터 가져오기
        
        Args:
            column_name: 컬럼명
            
        Returns:
            컬럼 데이터 리스트
        """
        column_data = []
        
        try:
            headers = self.get_table_headers()
            
            if column_name not in headers:
                self.logger.warning(f"Column '{column_name}' not found in headers")
                return column_data
            
            column_index = headers.index(column_name)
            
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                
                for row in row_elements:
                    cell_elements = row.find_elements(*self.TABLE_CELLS)
                    if column_index < len(cell_elements):
                        cell_text = cell_elements[column_index].text.strip()
                        column_data.append(cell_text)
            
            self.logger.debug(f"Retrieved {len(column_data)} values for column '{column_name}'")
            return column_data
            
        except Exception as e:
            self.logger.error(f"Failed to get column data: {str(e)}")
            return column_data
    
    # ==================== 검색 및 필터링 ====================
    
    def search_table(self, search_term: str) -> bool:
        """
        테이블 검색
        
        Args:
            search_term: 검색어
            
        Returns:
            검색 성공 여부
        """
        self.logger.debug(f"Searching table for: {search_term}")
        
        try:
            search_input = None
            
            # 기본 검색 입력 필드 찾기
            if self.is_element_present(self.SEARCH_INPUT, timeout=2):
                search_input = self.SEARCH_INPUT
            else:
                # 대체 로케이터들 시도
                for locator in self.ALT_SEARCH_LOCATORS:
                    if self.is_element_present(locator, timeout=1):
                        search_input = locator
                        break
            
            if search_input:
                self.input_text(search_input, search_term, clear_first=True)
                
                # 검색 버튼이 있으면 클릭
                if self.is_element_present(self.SEARCH_BUTTON, timeout=2):
                    self.click_element(self.SEARCH_BUTTON)
                else:
                    # Enter 키로 검색
                    from selenium.webdriver.common.keys import Keys
                    self.send_keys(search_input, Keys.RETURN)
                
                # 검색 결과 로딩 대기
                self.wait(2)
                
                self.logger.debug(f"Search completed for: {search_term}")
                return True
            else:
                self.logger.warning("Search input not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to search table: {str(e)}")
            return False
    
    def apply_filter(self, filter_value: str) -> bool:
        """
        필터 적용
        
        Args:
            filter_value: 필터 값
            
        Returns:
            필터 적용 성공 여부
        """
        try:
            if self.is_element_present(self.FILTER_DROPDOWN, timeout=2):
                self.select_dropdown_by_text(self.FILTER_DROPDOWN, filter_value)
                self.wait(2)  # 필터 적용 대기
                self.logger.debug(f"Filter applied: {filter_value}")
                return True
            else:
                self.logger.warning("Filter dropdown not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to apply filter: {str(e)}")
            return False
    
    def clear_filters(self) -> bool:
        """
        필터 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            if self.is_element_present(self.CLEAR_FILTER_BUTTON, timeout=2):
                self.click_element(self.CLEAR_FILTER_BUTTON)
                self.wait(2)
                self.logger.debug("Filters cleared")
                return True
            else:
                self.logger.warning("Clear filter button not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to clear filters: {str(e)}")
            return False
    
    # ==================== 정렬 ====================
    
    def sort_by_column(self, column_name: str, ascending: bool = True) -> bool:
        """
        컬럼별 정렬
        
        Args:
            column_name: 정렬할 컬럼명
            ascending: 오름차순 여부
            
        Returns:
            정렬 성공 여부
        """
        self.logger.debug(f"Sorting by column '{column_name}', ascending: {ascending}")
        
        try:
            headers = self.get_table_headers()
            
            if column_name not in headers:
                self.logger.warning(f"Column '{column_name}' not found")
                return False
            
            # 헤더 클릭으로 정렬 (일반적인 방법)
            header_elements = self.find_elements(self.TABLE_HEADERS)
            column_index = headers.index(column_name)
            
            if column_index < len(header_elements):
                header_element = header_elements[column_index]
                
                # 정렬 버튼이 헤더 내에 있는지 확인
                try:
                    sort_button = header_element.find_element(By.CSS_SELECTOR, ".sort-button")
                    sort_button.click()
                except:
                    # 헤더 자체를 클릭
                    header_element.click()
                
                self.wait(2)  # 정렬 완료 대기
                self.logger.debug(f"Column '{column_name}' sorted")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to sort by column: {str(e)}")
            return False
    
    # ==================== 페이지네이션 ====================
    
    def go_to_next_page(self) -> bool:
        """
        다음 페이지로 이동
        
        Returns:
            이동 성공 여부
        """
        try:
            if self.is_element_present(self.NEXT_PAGE_BUTTON, timeout=2):
                next_button = self.find_element(self.NEXT_PAGE_BUTTON)
                if next_button.is_enabled():
                    self.click_element(self.NEXT_PAGE_BUTTON)
                    self.wait(2)
                    self.logger.debug("Moved to next page")
                    return True
                else:
                    self.logger.debug("Next page button is disabled")
                    return False
            else:
                self.logger.warning("Next page button not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to go to next page: {str(e)}")
            return False
    
    def go_to_previous_page(self) -> bool:
        """
        이전 페이지로 이동
        
        Returns:
            이동 성공 여부
        """
        try:
            if self.is_element_present(self.PREV_PAGE_BUTTON, timeout=2):
                prev_button = self.find_element(self.PREV_PAGE_BUTTON)
                if prev_button.is_enabled():
                    self.click_element(self.PREV_PAGE_BUTTON)
                    self.wait(2)
                    self.logger.debug("Moved to previous page")
                    return True
                else:
                    self.logger.debug("Previous page button is disabled")
                    return False
            else:
                self.logger.warning("Previous page button not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to go to previous page: {str(e)}")
            return False
    
    def go_to_page(self, page_number: int) -> bool:
        """
        특정 페이지로 이동
        
        Args:
            page_number: 페이지 번호
            
        Returns:
            이동 성공 여부
        """
        try:
            if self.is_element_present(self.PAGE_NUMBERS, timeout=2):
                page_elements = self.find_elements(self.PAGE_NUMBERS)
                
                for page_element in page_elements:
                    if page_element.text.strip() == str(page_number):
                        page_element.click()
                        self.wait(2)
                        self.logger.debug(f"Moved to page {page_number}")
                        return True
                
                self.logger.warning(f"Page {page_number} not found")
                return False
            else:
                self.logger.warning("Page numbers not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to go to page {page_number}: {str(e)}")
            return False
    
    def get_current_page(self) -> int:
        """
        현재 페이지 번호 가져오기
        
        Returns:
            현재 페이지 번호
        """
        try:
            if self.is_element_present(self.CURRENT_PAGE, timeout=2):
                current_page_text = self.get_text(self.CURRENT_PAGE)
                # 숫자 추출
                import re
                numbers = re.findall(r'\d+', current_page_text)
                if numbers:
                    return int(numbers[0])
            
            return 1  # 기본값
            
        except Exception as e:
            self.logger.error(f"Failed to get current page: {str(e)}")
            return 1
    
    # ==================== 행 선택 및 액션 ====================
    
    def select_row(self, row_index: int) -> bool:
        """
        특정 행 선택
        
        Args:
            row_index: 행 인덱스 (0부터 시작)
            
        Returns:
            선택 성공 여부
        """
        try:
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                
                if row_index < len(row_elements):
                    row = row_elements[row_index]
                    
                    # 체크박스 찾기
                    try:
                        checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                        if not checkbox.is_selected():
                            checkbox.click()
                            self.logger.debug(f"Row {row_index} selected")
                            return True
                    except:
                        # 체크박스가 없으면 행 자체를 클릭
                        row.click()
                        self.logger.debug(f"Row {row_index} clicked")
                        return True
                else:
                    self.logger.warning(f"Row index {row_index} out of range")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to select row: {str(e)}")
            return False
    
    def select_all_rows(self) -> bool:
        """
        모든 행 선택
        
        Returns:
            선택 성공 여부
        """
        try:
            if self.is_element_present(self.SELECT_ALL_CHECKBOX, timeout=2):
                self.click_element(self.SELECT_ALL_CHECKBOX)
                self.logger.debug("All rows selected")
                return True
            else:
                self.logger.warning("Select all checkbox not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to select all rows: {str(e)}")
            return False
    
    # ==================== 테이블 정보 ====================
    
    def get_total_records(self) -> int:
        """
        총 레코드 수 가져오기
        
        Returns:
            총 레코드 수
        """
        try:
            if self.is_element_present(self.TOTAL_RECORDS, timeout=2):
                total_text = self.get_text(self.TOTAL_RECORDS)
                # 숫자 추출
                import re
                numbers = re.findall(r'\d+', total_text)
                if numbers:
                    return int(numbers[-1])  # 마지막 숫자가 총 개수일 가능성이 높음
            
            # 현재 페이지의 행 수로 대체
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                return len(row_elements)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to get total records: {str(e)}")
            return 0
    
    def is_table_empty(self) -> bool:
        """
        테이블이 비어있는지 확인
        
        Returns:
            테이블이 비어있으면 True
        """
        try:
            # "데이터 없음" 메시지 확인
            if self.is_element_present(self.NO_DATA_MESSAGE, timeout=2):
                return True
            
            # 행 개수 확인
            total_records = self.get_total_records()
            return total_records == 0
            
        except Exception as e:
            self.logger.error(f"Failed to check if table is empty: {str(e)}")
            return True
    
    def get_table_summary(self) -> Dict[str, Any]:
        """
        테이블 요약 정보 가져오기
        
        Returns:
            테이블 요약 정보 딕셔너리
        """
        summary = {
            'total_records': self.get_total_records(),
            'current_page': self.get_current_page(),
            'headers': self.get_table_headers(),
            'is_empty': self.is_table_empty(),
            'visible_rows': 0
        }
        
        try:
            if self.is_element_present(self.TABLE_ROWS, timeout=2):
                row_elements = self.find_elements(self.TABLE_ROWS)
                summary['visible_rows'] = len(row_elements)
            
            self.logger.debug(f"Table summary: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get table summary: {str(e)}")
            return summary