"""
SearchPage 클래스 - 검색 페이지 Page Object

이 모듈은 검색 페이지의 UI 요소와 동작을 캡슐화합니다.
검색 기능, 필터링, 결과 확인 등의 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys

from .base_page import BasePage
from ..core.logging import get_logger
from ..core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class SearchPage(BasePage):
    """
    검색 페이지 Page Object 클래스
    
    검색 기능의 모든 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 검색 관련 요소들
    SEARCH_INPUT = (By.ID, "search")
    SEARCH_BUTTON = (By.ID, "search-btn")
    SEARCH_SUGGESTIONS = (By.CSS_SELECTOR, ".search-suggestions")
    CLEAR_SEARCH_BUTTON = (By.CSS_SELECTOR, ".clear-search")
    
    # 대체 검색 로케이터들
    ALT_SEARCH_INPUT_LOCATORS = [
        (By.NAME, "search"),
        (By.NAME, "q"),
        (By.NAME, "query"),
        (By.CSS_SELECTOR, "input[type='search']"),
        (By.CSS_SELECTOR, "input[placeholder*='search' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='검색' i]"),
        (By.XPATH, "//input[@type='search']"),
        (By.XPATH, "//input[contains(@placeholder, 'search')]"),
        (By.XPATH, "//input[contains(@placeholder, '검색')]")
    ]
    
    ALT_SEARCH_BUTTON_LOCATORS = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, ".search-button"),
        (By.CSS_SELECTOR, ".btn-search"),
        (By.XPATH, "//button[contains(text(), 'Search')]"),
        (By.XPATH, "//button[contains(text(), '검색')]"),
        (By.XPATH, "//input[@type='submit' and @value='Search']"),
        (By.XPATH, "//input[@type='submit' and @value='검색']")
    ]
    
    # 검색 결과 관련 요소들
    SEARCH_RESULTS_CONTAINER = (By.CSS_SELECTOR, ".search-results")
    SEARCH_RESULT_ITEMS = (By.CSS_SELECTOR, ".search-result-item")
    SEARCH_RESULT_TITLE = (By.CSS_SELECTOR, ".result-title")
    SEARCH_RESULT_PRICE = (By.CSS_SELECTOR, ".result-price")
    SEARCH_RESULT_IMAGE = (By.CSS_SELECTOR, ".result-image")
    SEARCH_RESULT_LINK = (By.CSS_SELECTOR, ".result-link")
    
    # 대체 검색 결과 로케이터들
    ALT_SEARCH_RESULTS_LOCATORS = [
        (By.CSS_SELECTOR, ".results"),
        (By.CSS_SELECTOR, ".search-list"),
        (By.CSS_SELECTOR, ".product-list"),
        (By.CSS_SELECTOR, "[data-testid='search-results']"),
        (By.XPATH, "//*[contains(@class, 'results')]"),
        (By.XPATH, "//*[contains(@class, 'search')]")
    ]
    
    ALT_RESULT_ITEM_LOCATORS = [
        (By.CSS_SELECTOR, ".result-item"),
        (By.CSS_SELECTOR, ".product-item"),
        (By.CSS_SELECTOR, ".search-item"),
        (By.CSS_SELECTOR, "[data-testid='result-item']"),
        (By.XPATH, "//*[contains(@class, 'item')]")
    ]
    
    # 필터 및 정렬 관련 요소들
    FILTER_CONTAINER = (By.CSS_SELECTOR, ".filters")
    PRICE_FILTER = (By.CSS_SELECTOR, ".price-filter")
    CATEGORY_FILTER = (By.CSS_SELECTOR, ".category-filter")
    BRAND_FILTER = (By.CSS_SELECTOR, ".brand-filter")
    SORT_DROPDOWN = (By.CSS_SELECTOR, ".sort-dropdown")
    APPLY_FILTERS_BUTTON = (By.CSS_SELECTOR, ".apply-filters")
    CLEAR_FILTERS_BUTTON = (By.CSS_SELECTOR, ".clear-filters")
    
    # 페이지네이션 관련 요소들
    PAGINATION_CONTAINER = (By.CSS_SELECTOR, ".pagination")
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".next-page")
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, ".prev-page")
    PAGE_NUMBERS = (By.CSS_SELECTOR, ".page-number")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".current-page")
    
    # 상태 및 메시지 요소들
    NO_RESULTS_MESSAGE = (By.CSS_SELECTOR, ".no-results")
    LOADING_INDICATOR = (By.CSS_SELECTOR, ".loading")
    RESULTS_COUNT = (By.CSS_SELECTOR, ".results-count")
    
    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        SearchPage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 검색 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        
        # 검색 페이지 특화 설정
        self.search_timeout = 30  # 검색 결과 대기 시간
        self.suggestion_timeout = 5  # 검색 제안 대기 시간
        
        self.logger.debug("SearchPage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_search(self, search_url: str = None) -> None:
        """
        검색 페이지로 이동
        
        Args:
            search_url: 검색 페이지 URL (None이면 기본 URL 사용)
        """
        url = search_url or f"{self.base_url}/search"
        self.logger.info(f"Navigating to search page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_search_page_load()
            self.logger.info("Successfully navigated to search page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to search page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_search_page_load(self) -> None:
        """검색 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for search page to load")
        
        try:
            # 기본 페이지 로딩 대기
            self.wait_for_page_load()
            
            # 검색 입력 필드가 로드될 때까지 대기
            self._find_search_input()
            
            self.logger.debug("Search page loaded successfully")
            
        except ElementNotFoundException as e:
            self.logger.error(f"Search page elements not found: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Search page load failed: {str(e)}")
            raise PageLoadTimeoutException("search page", self.default_timeout)
    
    # ==================== 요소 찾기 (Smart Locator) ====================
    
    def _find_search_input(self) -> tuple:
        """검색 입력 필드 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.SEARCH_INPUT, timeout=2):
            return self.SEARCH_INPUT
        
        # 대체 로케이터들 시도
        for locator in self.ALT_SEARCH_INPUT_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found search input with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("search input field", timeout=self.default_timeout)
    
    def _find_search_button(self) -> tuple:
        """검색 버튼 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.SEARCH_BUTTON, timeout=2):
            return self.SEARCH_BUTTON
        
        # 대체 로케이터들 시도
        for locator in self.ALT_SEARCH_BUTTON_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found search button with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("search button", timeout=self.default_timeout)
    
    def _find_search_results_container(self) -> Optional[tuple]:
        """검색 결과 컨테이너 찾기"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.SEARCH_RESULTS_CONTAINER, timeout=2):
            return self.SEARCH_RESULTS_CONTAINER
        
        # 대체 로케이터들 시도
        for locator in self.ALT_SEARCH_RESULTS_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found search results with alternative locator: {locator}")
                return locator
        
        return None
    
    def _find_result_items(self) -> List[tuple]:
        """검색 결과 아이템들 찾기"""
        result_locators = []
        
        # 기본 로케이터 시도
        if self.is_element_present(self.SEARCH_RESULT_ITEMS, timeout=2):
            result_locators.append(self.SEARCH_RESULT_ITEMS)
        
        # 대체 로케이터들 시도
        for locator in self.ALT_RESULT_ITEM_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                result_locators.append(locator)
        
        return result_locators
    
    # ==================== 검색 기능 ====================
    
    def enter_search_term(self, search_term: str, clear_first: bool = True) -> None:
        """
        검색어 입력
        
        Args:
            search_term: 검색할 키워드
            clear_first: 기존 텍스트 삭제 여부
        """
        self.logger.debug(f"Entering search term: {search_term}")
        
        try:
            search_input_locator = self._find_search_input()
            self.input_text(search_input_locator, search_term, clear_first=clear_first)
            self.logger.debug("Search term entered successfully")
        except Exception as e:
            self.logger.error(f"Failed to enter search term: {str(e)}")
            raise
    
    def click_search_button(self) -> None:
        """검색 버튼 클릭"""
        self.logger.debug("Clicking search button")
        
        try:
            search_button_locator = self._find_search_button()
            self.click_element(search_button_locator)
            self.logger.debug("Search button clicked successfully")
        except Exception as e:
            self.logger.error(f"Failed to click search button: {str(e)}")
            raise
    
    def press_enter_to_search(self) -> None:
        """Enter 키를 눌러 검색 실행"""
        self.logger.debug("Pressing Enter to search")
        
        try:
            search_input_locator = self._find_search_input()
            self.send_keys(search_input_locator, Keys.RETURN)
            self.logger.debug("Enter key pressed for search")
        except Exception as e:
            self.logger.error(f"Failed to press Enter for search: {str(e)}")
            raise
    
    def search(self, search_term: str, use_enter: bool = False, wait_for_results: bool = True) -> bool:
        """
        검색 수행
        
        Args:
            search_term: 검색할 키워드
            use_enter: Enter 키 사용 여부 (False면 버튼 클릭)
            wait_for_results: 검색 결과 대기 여부
            
        Returns:
            검색 성공 여부
        """
        self.logger.info(f"Performing search for: {search_term}")
        
        try:
            # 검색어 입력
            self.enter_search_term(search_term)
            
            # 검색 실행
            if use_enter:
                self.press_enter_to_search()
            else:
                self.click_search_button()
            
            # 검색 결과 대기
            if wait_for_results:
                self._wait_for_search_results()
                
                # 검색 결과 확인
                if self.has_search_results():
                    self.logger.info(f"Search successful for: {search_term}")
                    return True
                else:
                    self.logger.warning(f"No search results found for: {search_term}")
                    return False
            else:
                self.logger.info("Search submitted, not waiting for results")
                return True
                
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise
    
    def _wait_for_search_results(self) -> None:
        """검색 결과 로딩 대기"""
        self.logger.debug("Waiting for search results")
        
        # 로딩 인디케이터가 있으면 사라질 때까지 대기
        if self.is_element_present(self.LOADING_INDICATOR, timeout=2):
            self.logger.debug("Waiting for loading indicator to disappear")
            self.wait_for_element_invisible(self.LOADING_INDICATOR, timeout=self.search_timeout)
        
        # 검색 결과 컨테이너가 나타날 때까지 대기
        results_container = self._find_search_results_container()
        if results_container:
            self.wait_for_element_visible(results_container, timeout=self.search_timeout)
        
        # 짧은 대기 (JavaScript 처리 시간)
        self.wait(1)
    
    # ==================== 검색 결과 확인 ====================
    
    def has_search_results(self) -> bool:
        """
        검색 결과 존재 여부 확인
        
        Returns:
            검색 결과 존재 여부
        """
        try:
            # "결과 없음" 메시지 확인
            if self.is_element_present(self.NO_RESULTS_MESSAGE, timeout=2):
                return False
            
            # 검색 결과 컨테이너 확인
            results_container = self._find_search_results_container()
            if not results_container:
                return False
            
            # 검색 결과 아이템들 확인
            result_locators = self._find_result_items()
            for locator in result_locators:
                if self.find_elements(locator):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking search results: {str(e)}")
            return False
    
    def get_search_results_count(self) -> int:
        """
        검색 결과 개수 가져오기
        
        Returns:
            검색 결과 개수
        """
        try:
            # 결과 개수 표시 요소에서 가져오기
            if self.is_element_present(self.RESULTS_COUNT, timeout=2):
                count_text = self.get_text(self.RESULTS_COUNT)
                # 숫자 추출 (예: "123 results found" -> 123)
                import re
                numbers = re.findall(r'\d+', count_text)
                if numbers:
                    return int(numbers[0])
            
            # 직접 결과 아이템 개수 세기
            result_locators = self._find_result_items()
            total_count = 0
            for locator in result_locators:
                elements = self.find_elements(locator)
                total_count += len(elements)
            
            return total_count
            
        except Exception as e:
            self.logger.error(f"Error getting search results count: {str(e)}")
            return 0
    
    def get_search_result_titles(self) -> List[str]:
        """
        검색 결과 제목들 가져오기
        
        Returns:
            검색 결과 제목 리스트
        """
        titles = []
        
        try:
            # 제목 요소들 찾기
            title_elements = self.find_elements(self.SEARCH_RESULT_TITLE)
            
            for element in title_elements:
                title = element.text.strip()
                if title:
                    titles.append(title)
            
            self.logger.debug(f"Found {len(titles)} search result titles")
            return titles
            
        except Exception as e:
            self.logger.error(f"Error getting search result titles: {str(e)}")
            return titles
    
    def get_search_result_info(self, index: int = 0) -> Dict[str, Any]:
        """
        특정 검색 결과의 상세 정보 가져오기
        
        Args:
            index: 검색 결과 인덱스 (0부터 시작)
            
        Returns:
            검색 결과 정보 딕셔너리
        """
        result_info = {
            'title': '',
            'price': '',
            'image_url': '',
            'link_url': '',
            'index': index
        }
        
        try:
            # 검색 결과 아이템들 가져오기
            result_locators = self._find_result_items()
            
            for locator in result_locators:
                result_elements = self.find_elements(locator)
                
                if index < len(result_elements):
                    result_element = result_elements[index]
                    
                    # 제목 가져오기
                    try:
                        title_element = result_element.find_element(*self.SEARCH_RESULT_TITLE)
                        result_info['title'] = title_element.text.strip()
                    except:
                        pass
                    
                    # 가격 가져오기
                    try:
                        price_element = result_element.find_element(*self.SEARCH_RESULT_PRICE)
                        result_info['price'] = price_element.text.strip()
                    except:
                        pass
                    
                    # 이미지 URL 가져오기
                    try:
                        image_element = result_element.find_element(*self.SEARCH_RESULT_IMAGE)
                        result_info['image_url'] = image_element.get_attribute('src')
                    except:
                        pass
                    
                    # 링크 URL 가져오기
                    try:
                        link_element = result_element.find_element(*self.SEARCH_RESULT_LINK)
                        result_info['link_url'] = link_element.get_attribute('href')
                    except:
                        pass
                    
                    break
            
            self.logger.debug(f"Retrieved info for search result {index}: {result_info}")
            return result_info
            
        except Exception as e:
            self.logger.error(f"Error getting search result info: {str(e)}")
            return result_info
    
    def click_search_result(self, index: int = 0) -> None:
        """
        특정 검색 결과 클릭
        
        Args:
            index: 클릭할 검색 결과 인덱스 (0부터 시작)
        """
        self.logger.debug(f"Clicking search result at index {index}")
        
        try:
            result_locators = self._find_result_items()
            
            for locator in result_locators:
                result_elements = self.find_elements(locator)
                
                if index < len(result_elements):
                    result_element = result_elements[index]
                    
                    # 링크 요소 찾아서 클릭
                    try:
                        link_element = result_element.find_element(*self.SEARCH_RESULT_LINK)
                        self.scroll_to_element(link_element)
                        link_element.click()
                        self.logger.debug(f"Clicked search result {index}")
                        return
                    except:
                        # 링크 요소가 없으면 결과 아이템 자체 클릭
                        self.scroll_to_element(result_element)
                        result_element.click()
                        self.logger.debug(f"Clicked search result item {index}")
                        return
            
            raise ElementNotFoundException(f"search result at index {index}")
            
        except Exception as e:
            self.logger.error(f"Failed to click search result {index}: {str(e)}")
            raise
    
    # ==================== 필터 및 정렬 기능 ====================
    
    def apply_price_filter(self, min_price: float = None, max_price: float = None) -> None:
        """
        가격 필터 적용
        
        Args:
            min_price: 최소 가격
            max_price: 최대 가격
        """
        self.logger.debug(f"Applying price filter: {min_price} - {max_price}")
        
        try:
            if not self.is_element_present(self.PRICE_FILTER, timeout=2):
                self.logger.warning("Price filter not available")
                return
            
            # 가격 필터 섹션 클릭하여 열기
            self.click_element(self.PRICE_FILTER)
            
            # 최소 가격 입력
            if min_price is not None:
                min_price_input = (By.CSS_SELECTOR, ".min-price-input")
                if self.is_element_present(min_price_input, timeout=2):
                    self.input_text(min_price_input, str(min_price))
            
            # 최대 가격 입력
            if max_price is not None:
                max_price_input = (By.CSS_SELECTOR, ".max-price-input")
                if self.is_element_present(max_price_input, timeout=2):
                    self.input_text(max_price_input, str(max_price))
            
            # 필터 적용 버튼 클릭
            if self.is_element_present(self.APPLY_FILTERS_BUTTON, timeout=2):
                self.click_element(self.APPLY_FILTERS_BUTTON)
            
            self.logger.debug("Price filter applied successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply price filter: {str(e)}")
            raise
    
    def select_category_filter(self, category: str) -> None:
        """
        카테고리 필터 선택
        
        Args:
            category: 선택할 카테고리명
        """
        self.logger.debug(f"Selecting category filter: {category}")
        
        try:
            if not self.is_element_present(self.CATEGORY_FILTER, timeout=2):
                self.logger.warning("Category filter not available")
                return
            
            # 카테고리 필터 섹션 클릭하여 열기
            self.click_element(self.CATEGORY_FILTER)
            
            # 특정 카테고리 체크박스 찾아서 클릭
            category_checkbox = (By.XPATH, f"//input[@type='checkbox' and following-sibling::*[contains(text(), '{category}')]]")
            
            if self.is_element_present(category_checkbox, timeout=2):
                self.click_element(category_checkbox)
                self.logger.debug(f"Category '{category}' selected")
            else:
                self.logger.warning(f"Category '{category}' not found")
            
        except Exception as e:
            self.logger.error(f"Failed to select category filter: {str(e)}")
            raise
    
    def sort_results(self, sort_option: str) -> None:
        """
        검색 결과 정렬
        
        Args:
            sort_option: 정렬 옵션 (예: "price_low_to_high", "price_high_to_low", "newest", "rating")
        """
        self.logger.debug(f"Sorting results by: {sort_option}")
        
        try:
            if not self.is_element_present(self.SORT_DROPDOWN, timeout=2):
                self.logger.warning("Sort dropdown not available")
                return
            
            # 정렬 드롭다운 클릭
            self.click_element(self.SORT_DROPDOWN)
            
            # 정렬 옵션 선택
            sort_option_locator = (By.XPATH, f"//option[@value='{sort_option}'] | //*[contains(text(), '{sort_option}')]")
            
            if self.is_element_present(sort_option_locator, timeout=2):
                self.click_element(sort_option_locator)
                self.logger.debug(f"Results sorted by: {sort_option}")
            else:
                self.logger.warning(f"Sort option '{sort_option}' not found")
            
        except Exception as e:
            self.logger.error(f"Failed to sort results: {str(e)}")
            raise
    
    def clear_all_filters(self) -> None:
        """모든 필터 초기화"""
        self.logger.debug("Clearing all filters")
        
        try:
            if self.is_element_present(self.CLEAR_FILTERS_BUTTON, timeout=2):
                self.click_element(self.CLEAR_FILTERS_BUTTON)
                self.logger.debug("All filters cleared")
            else:
                self.logger.warning("Clear filters button not found")
            
        except Exception as e:
            self.logger.error(f"Failed to clear filters: {str(e)}")
            raise
    
    # ==================== 페이지네이션 ====================
    
    def go_to_next_page(self) -> bool:
        """
        다음 페이지로 이동
        
        Returns:
            이동 성공 여부
        """
        self.logger.debug("Going to next page")
        
        try:
            if self.is_element_present(self.NEXT_PAGE_BUTTON, timeout=2):
                # 다음 페이지 버튼이 활성화되어 있는지 확인
                next_button = self.find_element(self.NEXT_PAGE_BUTTON)
                if next_button.is_enabled() and "disabled" not in next_button.get_attribute("class"):
                    self.click_element(self.NEXT_PAGE_BUTTON)
                    self._wait_for_search_results()
                    self.logger.debug("Moved to next page")
                    return True
                else:
                    self.logger.debug("Next page button is disabled")
                    return False
            else:
                self.logger.debug("Next page button not found")
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
        self.logger.debug("Going to previous page")
        
        try:
            if self.is_element_present(self.PREV_PAGE_BUTTON, timeout=2):
                # 이전 페이지 버튼이 활성화되어 있는지 확인
                prev_button = self.find_element(self.PREV_PAGE_BUTTON)
                if prev_button.is_enabled() and "disabled" not in prev_button.get_attribute("class"):
                    self.click_element(self.PREV_PAGE_BUTTON)
                    self._wait_for_search_results()
                    self.logger.debug("Moved to previous page")
                    return True
                else:
                    self.logger.debug("Previous page button is disabled")
                    return False
            else:
                self.logger.debug("Previous page button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to go to previous page: {str(e)}")
            return False
    
    def go_to_page(self, page_number: int) -> bool:
        """
        특정 페이지로 이동
        
        Args:
            page_number: 이동할 페이지 번호
            
        Returns:
            이동 성공 여부
        """
        self.logger.debug(f"Going to page {page_number}")
        
        try:
            # 페이지 번호 버튼 찾기
            page_button = (By.XPATH, f"//a[contains(@class, 'page-number') and text()='{page_number}']")
            
            if self.is_element_present(page_button, timeout=2):
                self.click_element(page_button)
                self._wait_for_search_results()
                self.logger.debug(f"Moved to page {page_number}")
                return True
            else:
                self.logger.debug(f"Page {page_number} button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to go to page {page_number}: {str(e)}")
            return False
    
    def get_current_page_number(self) -> int:
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
            self.logger.error(f"Error getting current page number: {str(e)}")
            return 1
    
    # ==================== 유틸리티 메서드 ====================
    
    def clear_search(self) -> None:
        """검색어 초기화"""
        self.logger.debug("Clearing search")
        
        try:
            # 검색 초기화 버튼이 있으면 클릭
            if self.is_element_present(self.CLEAR_SEARCH_BUTTON, timeout=2):
                self.click_element(self.CLEAR_SEARCH_BUTTON)
            else:
                # 검색 입력 필드 직접 초기화
                search_input_locator = self._find_search_input()
                search_input = self.find_element(search_input_locator)
                search_input.clear()
            
            self.logger.debug("Search cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear search: {str(e)}")
            raise
    
    def get_search_suggestions(self) -> List[str]:
        """
        검색 제안 목록 가져오기
        
        Returns:
            검색 제안 리스트
        """
        suggestions = []
        
        try:
            if self.is_element_present(self.SEARCH_SUGGESTIONS, timeout=self.suggestion_timeout):
                suggestion_elements = self.find_elements((By.CSS_SELECTOR, ".search-suggestions .suggestion"))
                
                for element in suggestion_elements:
                    suggestion = element.text.strip()
                    if suggestion:
                        suggestions.append(suggestion)
                
                self.logger.debug(f"Found {len(suggestions)} search suggestions")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting search suggestions: {str(e)}")
            return suggestions
    
    def select_search_suggestion(self, suggestion_text: str) -> bool:
        """
        검색 제안 선택
        
        Args:
            suggestion_text: 선택할 제안 텍스트
            
        Returns:
            선택 성공 여부
        """
        self.logger.debug(f"Selecting search suggestion: {suggestion_text}")
        
        try:
            if self.is_element_present(self.SEARCH_SUGGESTIONS, timeout=self.suggestion_timeout):
                suggestion_locator = (By.XPATH, f"//div[contains(@class, 'suggestion') and contains(text(), '{suggestion_text}')]")
                
                if self.is_element_present(suggestion_locator, timeout=2):
                    self.click_element(suggestion_locator)
                    self.logger.debug(f"Selected suggestion: {suggestion_text}")
                    return True
                else:
                    self.logger.warning(f"Suggestion '{suggestion_text}' not found")
                    return False
            else:
                self.logger.warning("Search suggestions not available")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to select search suggestion: {str(e)}")
            return False
    
    def take_search_screenshot(self, filename: str = None) -> str:
        """
        검색 페이지 스크린샷 촬영
        
        Args:
            filename: 파일명
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_page_{timestamp}.png"
        
        return self.take_screenshot(filename)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"SearchPage(url={self.get_current_url()})"