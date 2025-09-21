"""
BasePage 클래스 - Page Object Pattern의 기본 클래스

이 모듈은 모든 페이지 클래스의 기본이 되는 BasePage 클래스를 제공합니다.
공통 웹 요소 조작, 스크린샷 캡처, 페이지 로딩 대기 등의 기능을 포함합니다.
"""

import os
import time
from datetime import datetime
from typing import List, Optional, Union, Any, Tuple
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

from ..core.logging import get_logger
from ..core.retry_manager import SmartRetryManager, RetryConfig, smart_retry
from ..core.config import get_config_manager
from ..core.exceptions import (
    PageObjectException,
    ElementNotFoundException,
    PageLoadTimeoutException
)


class BasePage:
    """
    모든 페이지 클래스의 기본 클래스
    
    Page Object Pattern을 구현하며, 공통적으로 사용되는
    웹 요소 조작 메서드들을 제공합니다.
    """
    
    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        BasePage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 기본 URL (None이면 설정에서 가져옴)
        """
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)
        self.config_manager = get_config_manager()
        
        # 기본 설정
        self.base_url = base_url or self.config_manager.get_base_url()
        self.default_timeout = self.config_manager.get_timeout()
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Smart Retry 설정
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            enable_self_healing=True,
            learning_enabled=True
        )
        self.retry_manager = SmartRetryManager(driver, retry_config)
        
        self.logger.debug(f"Initialized {self.__class__.__name__} with base_url: {self.base_url}")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to(self, url: str = None) -> None:
        """
        지정된 URL로 이동
        
        Args:
            url: 이동할 URL (None이면 base_url 사용)
        """
        target_url = url or self.base_url
        self.logger.info(f"Navigating to: {target_url}")
        
        try:
            self.driver.get(target_url)
            self.wait_for_page_load()
            self.logger.info(f"Successfully navigated to: {target_url}")
        except Exception as e:
            self.logger.error(f"Failed to navigate to {target_url}: {str(e)}")
            raise PageLoadTimeoutException(target_url, self.default_timeout)
    
    def refresh_page(self) -> None:
        """페이지 새로고침"""
        self.logger.info("Refreshing page")
        self.driver.refresh()
        self.wait_for_page_load()
    
    def go_back(self) -> None:
        """브라우저 뒤로가기"""
        self.logger.info("Going back")
        self.driver.back()
        self.wait_for_page_load()
    
    def go_forward(self) -> None:
        """브라우저 앞으로가기"""
        self.logger.info("Going forward")
        self.driver.forward()
        self.wait_for_page_load()
    
    # ==================== 요소 찾기 ====================
    
    def find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """
        단일 요소 찾기 (Smart Retry 적용)
        
        Args:
            locator: 요소 로케이터 (By.ID, "element-id")
            timeout: 대기 시간 (None이면 기본값 사용)
            
        Returns:
            WebElement 인스턴스
            
        Raises:
            ElementNotFoundException: 요소를 찾을 수 없는 경우
        """
        timeout = timeout or self.default_timeout
        
        try:
            self.logger.debug(f"Finding element: {locator}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.debug(f"Found element: {locator}")
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {locator} (timeout: {timeout}s)")
            raise ElementNotFoundException(f"{locator[0]}={locator[1]}", timeout=timeout)
    
    def find_elements(self, locator: Tuple[str, str], timeout: int = None) -> List[WebElement]:
        """
        여러 요소 찾기
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
            
        Returns:
            WebElement 리스트
        """
        timeout = timeout or self.default_timeout
        
        try:
            self.logger.debug(f"Finding elements: {locator}")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            elements = self.driver.find_elements(*locator)
            self.logger.debug(f"Found {len(elements)} elements: {locator}")
            return elements
        except TimeoutException:
            self.logger.warning(f"No elements found: {locator}")
            return []
    
    def is_element_present(self, locator: Tuple[str, str], timeout: int = 2) -> bool:
        """
        요소 존재 여부 확인
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간 (짧게 설정)
            
        Returns:
            요소 존재 여부
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def is_element_visible(self, locator: Tuple[str, str], timeout: int = 2) -> bool:
        """
        요소 가시성 확인
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
            
        Returns:
            요소 가시성 여부
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def is_element_clickable(self, locator: Tuple[str, str], timeout: int = 2) -> bool:
        """
        요소 클릭 가능 여부 확인
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
            
        Returns:
            클릭 가능 여부
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return True
        except TimeoutException:
            return False
    
    # ==================== 요소 상호작용 ====================
    
    def click_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """
        요소 클릭 (Smart Retry 적용)
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
        """
        timeout = timeout or self.default_timeout
        
        def _click_action():
            self.logger.debug(f"Clicking element: {locator}")
            element = self.wait_for_element_clickable(locator, timeout)
            
            # 요소가 뷰포트에 보이도록 스크롤
            self.scroll_to_element(element)
            
            element.click()
            self.logger.debug(f"Clicked element: {locator}")
            return True
        
        return self.retry_manager.execute_with_retry(_click_action)
    
    def double_click_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """
        요소 더블클릭
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
        """
        timeout = timeout or self.default_timeout
        
        self.logger.debug(f"Double clicking element: {locator}")
        element = self.wait_for_element_clickable(locator, timeout)
        
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        self.logger.debug(f"Double clicked element: {locator}")
    
    def right_click_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """
        요소 우클릭
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
        """
        timeout = timeout or self.default_timeout
        
        self.logger.debug(f"Right clicking element: {locator}")
        element = self.wait_for_element_clickable(locator, timeout)
        
        actions = ActionChains(self.driver)
        actions.context_click(element).perform()
        self.logger.debug(f"Right clicked element: {locator}")
    
    def input_text(self, locator: Tuple[str, str], text: str, clear_first: bool = True, timeout: int = None) -> None:
        """
        텍스트 입력 (Smart Retry 적용)
        
        Args:
            locator: 요소 로케이터
            text: 입력할 텍스트
            clear_first: 기존 텍스트 삭제 여부
            timeout: 대기 시간
        """
        timeout = timeout or self.default_timeout
        
        def _input_action():
            self.logger.debug(f"Inputting text to element: {locator}")
            element = self.wait_for_element_clickable(locator, timeout)
            
            if clear_first:
                element.clear()
            
            element.send_keys(text)
            self.logger.debug(f"Input text '{text}' to element: {locator}")
            return True
        
        return self.retry_manager.execute_with_retry(_input_action)
    
    def get_text(self, locator: Tuple[str, str], timeout: int = None) -> str:
        """
        요소 텍스트 가져오기
        
        Args:
            locator: 요소 로케이터
            timeout: 대기 시간
            
        Returns:
            요소의 텍스트
        """
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_visible(locator, timeout)
        text = element.text
        self.logger.debug(f"Got text '{text}' from element: {locator}")
        return text
    
    def get_attribute(self, locator: Tuple[str, str], attribute: str, timeout: int = None) -> str:
        """
        요소 속성값 가져오기
        
        Args:
            locator: 요소 로케이터
            attribute: 속성명
            timeout: 대기 시간
            
        Returns:
            속성값
        """
        timeout = timeout or self.default_timeout
        
        element = self.find_element(locator, timeout)
        value = element.get_attribute(attribute)
        self.logger.debug(f"Got attribute '{attribute}' = '{value}' from element: {locator}")
        return value
    
    # ==================== 대기 메서드 ====================
    
    def wait_for_element_present(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """요소가 DOM에 존재할 때까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            raise ElementNotFoundException(f"{locator[0]}={locator[1]}", timeout=timeout)
    
    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """요소가 보일 때까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            raise ElementNotFoundException(f"{locator[0]}={locator[1]}", timeout=timeout)
    
    def wait_for_element_clickable(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """요소가 클릭 가능할 때까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
        except TimeoutException:
            raise ElementNotFoundException(f"{locator[0]}={locator[1]}", timeout=timeout)
    
    def wait_for_element_invisible(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """요소가 사라질 때까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
        except TimeoutException:
            return False
    
    def wait_for_text_present(self, locator: Tuple[str, str], text: str, timeout: int = None) -> bool:
        """특정 텍스트가 요소에 나타날 때까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator, text)
            )
        except TimeoutException:
            return False
    
    def wait_for_page_load(self, timeout: int = None) -> None:
        """페이지 로딩 완료까지 대기"""
        timeout = timeout or self.default_timeout
        
        try:
            # JavaScript 실행 완료 대기
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # jQuery가 있다면 jQuery 완료 대기
            try:
                WebDriverWait(self.driver, 2).until(
                    lambda driver: driver.execute_script("return jQuery.active == 0")
                )
            except:
                pass  # jQuery가 없는 경우 무시
            
            self.logger.debug("Page loading completed")
            
        except TimeoutException:
            self.logger.warning(f"Page load timeout after {timeout}s")
    
    # ==================== 스크롤 및 뷰포트 ====================
    
    def scroll_to_element(self, element: Union[WebElement, Tuple[str, str]]) -> None:
        """요소로 스크롤"""
        if isinstance(element, tuple):
            element = self.find_element(element)
        
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)  # 스크롤 완료 대기
        self.logger.debug("Scrolled to element")
    
    def scroll_to_top(self) -> None:
        """페이지 맨 위로 스크롤"""
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        self.logger.debug("Scrolled to top")
    
    def scroll_to_bottom(self) -> None:
        """페이지 맨 아래로 스크롤"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        self.logger.debug("Scrolled to bottom")
    
    def scroll_by_pixels(self, x: int, y: int) -> None:
        """지정된 픽셀만큼 스크롤"""
        self.driver.execute_script(f"window.scrollBy({x}, {y});")
        time.sleep(0.5)
        self.logger.debug(f"Scrolled by ({x}, {y}) pixels")
    
    # ==================== 드롭다운 및 선택 ====================
    
    def select_dropdown_by_text(self, locator: Tuple[str, str], text: str, timeout: int = None) -> None:
        """드롭다운에서 텍스트로 선택"""
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_clickable(locator, timeout)
        select = Select(element)
        select.select_by_visible_text(text)
        self.logger.debug(f"Selected dropdown option by text: {text}")
    
    def select_dropdown_by_value(self, locator: Tuple[str, str], value: str, timeout: int = None) -> None:
        """드롭다운에서 값으로 선택"""
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_clickable(locator, timeout)
        select = Select(element)
        select.select_by_value(value)
        self.logger.debug(f"Selected dropdown option by value: {value}")
    
    def select_dropdown_by_index(self, locator: Tuple[str, str], index: int, timeout: int = None) -> None:
        """드롭다운에서 인덱스로 선택"""
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_clickable(locator, timeout)
        select = Select(element)
        select.select_by_index(index)
        self.logger.debug(f"Selected dropdown option by index: {index}")
    
    def get_dropdown_options(self, locator: Tuple[str, str], timeout: int = None) -> List[str]:
        """드롭다운 옵션 목록 가져오기"""
        timeout = timeout or self.default_timeout
        
        element = self.find_element(locator, timeout)
        select = Select(element)
        options = [option.text for option in select.options]
        self.logger.debug(f"Got dropdown options: {options}")
        return options
    
    # ==================== 키보드 및 마우스 액션 ====================
    
    def send_keys(self, locator: Tuple[str, str], keys: str, timeout: int = None) -> None:
        """키 입력 (특수키 포함)"""
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_clickable(locator, timeout)
        element.send_keys(keys)
        self.logger.debug(f"Sent keys '{keys}' to element: {locator}")
    
    def press_enter(self, locator: Tuple[str, str] = None) -> None:
        """Enter 키 입력"""
        if locator:
            element = self.find_element(locator)
            element.send_keys(Keys.RETURN)
        else:
            ActionChains(self.driver).send_keys(Keys.RETURN).perform()
        self.logger.debug("Pressed Enter key")
    
    def press_escape(self) -> None:
        """Escape 키 입력"""
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.logger.debug("Pressed Escape key")
    
    def press_tab(self) -> None:
        """Tab 키 입력"""
        ActionChains(self.driver).send_keys(Keys.TAB).perform()
        self.logger.debug("Pressed Tab key")
    
    def hover_over_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """요소 위에 마우스 호버"""
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_visible(locator, timeout)
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        self.logger.debug(f"Hovered over element: {locator}")
    
    def drag_and_drop(self, source_locator: Tuple[str, str], target_locator: Tuple[str, str], timeout: int = None) -> None:
        """드래그 앤 드롭"""
        timeout = timeout or self.default_timeout
        
        source = self.wait_for_element_visible(source_locator, timeout)
        target = self.wait_for_element_visible(target_locator, timeout)
        
        actions = ActionChains(self.driver)
        actions.drag_and_drop(source, target).perform()
        self.logger.debug(f"Dragged from {source_locator} to {target_locator}")
    
    # ==================== 스크린샷 및 디버깅 ====================
    
    def take_screenshot(self, filename: str = None) -> str:
        """
        스크린샷 캡처
        
        Args:
            filename: 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.__class__.__name__}_{timestamp}.png"
        
        # 확장자가 없으면 추가
        if not filename.endswith('.png'):
            filename += '.png'
        
        filepath = self.screenshot_dir / filename
        
        try:
            self.driver.save_screenshot(str(filepath))
            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            raise
    
    def take_element_screenshot(self, locator: Tuple[str, str], filename: str = None, timeout: int = None) -> str:
        """
        특정 요소의 스크린샷 캡처
        
        Args:
            locator: 요소 로케이터
            filename: 파일명
            timeout: 대기 시간
            
        Returns:
            저장된 파일 경로
        """
        timeout = timeout or self.default_timeout
        
        element = self.wait_for_element_visible(locator, timeout)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"element_{timestamp}.png"
        
        if not filename.endswith('.png'):
            filename += '.png'
        
        filepath = self.screenshot_dir / filename
        
        try:
            element.screenshot(str(filepath))
            self.logger.info(f"Element screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to take element screenshot: {str(e)}")
            raise
    
    # ==================== 브라우저 정보 ====================
    
    def get_current_url(self) -> str:
        """현재 URL 가져오기"""
        url = self.driver.current_url
        self.logger.debug(f"Current URL: {url}")
        return url
    
    def get_page_title(self) -> str:
        """페이지 제목 가져오기"""
        title = self.driver.title
        self.logger.debug(f"Page title: {title}")
        return title
    
    def get_page_source(self) -> str:
        """페이지 소스 가져오기"""
        return self.driver.page_source
    
    def get_window_size(self) -> dict:
        """브라우저 창 크기 가져오기"""
        size = self.driver.get_window_size()
        self.logger.debug(f"Window size: {size}")
        return size
    
    def set_window_size(self, width: int, height: int) -> None:
        """브라우저 창 크기 설정"""
        self.driver.set_window_size(width, height)
        self.logger.debug(f"Set window size to {width}x{height}")
    
    def maximize_window(self) -> None:
        """브라우저 창 최대화"""
        self.driver.maximize_window()
        self.logger.debug("Maximized window")
    
    def minimize_window(self) -> None:
        """브라우저 창 최소화"""
        self.driver.minimize_window()
        self.logger.debug("Minimized window")
    
    # ==================== 쿠키 및 로컬 스토리지 ====================
    
    def get_cookie(self, name: str) -> dict:
        """쿠키 가져오기"""
        cookie = self.driver.get_cookie(name)
        self.logger.debug(f"Got cookie '{name}': {cookie}")
        return cookie
    
    def get_all_cookies(self) -> List[dict]:
        """모든 쿠키 가져오기"""
        cookies = self.driver.get_cookies()
        self.logger.debug(f"Got {len(cookies)} cookies")
        return cookies
    
    def add_cookie(self, cookie_dict: dict) -> None:
        """쿠키 추가"""
        self.driver.add_cookie(cookie_dict)
        self.logger.debug(f"Added cookie: {cookie_dict}")
    
    def delete_cookie(self, name: str) -> None:
        """쿠키 삭제"""
        self.driver.delete_cookie(name)
        self.logger.debug(f"Deleted cookie: {name}")
    
    def delete_all_cookies(self) -> None:
        """모든 쿠키 삭제"""
        self.driver.delete_all_cookies()
        self.logger.debug("Deleted all cookies")
    
    def execute_script(self, script: str, *args) -> Any:
        """JavaScript 실행"""
        result = self.driver.execute_script(script, *args)
        self.logger.debug(f"Executed script: {script[:50]}...")
        return result
    
    def get_local_storage_item(self, key: str) -> str:
        """로컬 스토리지 아이템 가져오기"""
        value = self.execute_script(f"return localStorage.getItem('{key}');")
        self.logger.debug(f"Got localStorage item '{key}': {value}")
        return value
    
    def set_local_storage_item(self, key: str, value: str) -> None:
        """로컬 스토리지 아이템 설정"""
        self.execute_script(f"localStorage.setItem('{key}', '{value}');")
        self.logger.debug(f"Set localStorage item '{key}': {value}")
    
    def remove_local_storage_item(self, key: str) -> None:
        """로컬 스토리지 아이템 삭제"""
        self.execute_script(f"localStorage.removeItem('{key}');")
        self.logger.debug(f"Removed localStorage item: {key}")
    
    def clear_local_storage(self) -> None:
        """로컬 스토리지 전체 삭제"""
        self.execute_script("localStorage.clear();")
        self.logger.debug("Cleared localStorage")
    
    # ==================== 유틸리티 메서드 ====================
    
    def wait(self, seconds: float) -> None:
        """지정된 시간만큼 대기"""
        self.logger.debug(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
    
    def switch_to_frame(self, frame_locator: Union[str, int, Tuple[str, str]]) -> None:
        """프레임으로 전환"""
        if isinstance(frame_locator, tuple):
            frame = self.find_element(frame_locator)
            self.driver.switch_to.frame(frame)
        else:
            self.driver.switch_to.frame(frame_locator)
        self.logger.debug(f"Switched to frame: {frame_locator}")
    
    def switch_to_default_content(self) -> None:
        """기본 컨텐츠로 전환"""
        self.driver.switch_to.default_content()
        self.logger.debug("Switched to default content")
    
    def switch_to_window(self, window_handle: str) -> None:
        """다른 윈도우로 전환"""
        self.driver.switch_to.window(window_handle)
        self.logger.debug(f"Switched to window: {window_handle}")
    
    def get_window_handles(self) -> List[str]:
        """모든 윈도우 핸들 가져오기"""
        handles = self.driver.window_handles
        self.logger.debug(f"Got {len(handles)} window handles")
        return handles
    
    def close_current_window(self) -> None:
        """현재 윈도우 닫기"""
        self.driver.close()
        self.logger.debug("Closed current window")
    
    def accept_alert(self) -> str:
        """알림창 수락"""
        alert = self.driver.switch_to.alert
        text = alert.text
        alert.accept()
        self.logger.debug(f"Accepted alert: {text}")
        return text
    
    def dismiss_alert(self) -> str:
        """알림창 취소"""
        alert = self.driver.switch_to.alert
        text = alert.text
        alert.dismiss()
        self.logger.debug(f"Dismissed alert: {text}")
        return text
    
    def get_alert_text(self) -> str:
        """알림창 텍스트 가져오기"""
        alert = self.driver.switch_to.alert
        text = alert.text
        self.logger.debug(f"Alert text: {text}")
        return text
    
    def is_alert_present(self, timeout: int = 2) -> bool:
        """알림창 존재 여부 확인"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            return True
        except TimeoutException:
            return False
    
    # ==================== 페이지 검증 ====================
    
    def verify_page_loaded(self, expected_url_part: str = None, expected_title: str = None) -> bool:
        """
        페이지 로딩 검증
        
        Args:
            expected_url_part: 예상 URL 일부
            expected_title: 예상 페이지 제목
            
        Returns:
            검증 결과
        """
        try:
            self.wait_for_page_load()
            
            if expected_url_part:
                current_url = self.get_current_url()
                if expected_url_part not in current_url:
                    self.logger.error(f"URL verification failed. Expected: {expected_url_part}, Actual: {current_url}")
                    return False
            
            if expected_title:
                current_title = self.get_page_title()
                if expected_title not in current_title:
                    self.logger.error(f"Title verification failed. Expected: {expected_title}, Actual: {current_title}")
                    return False
            
            self.logger.info("Page verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Page verification failed: {str(e)}")
            return False
    
    def verify_element_text(self, locator: Tuple[str, str], expected_text: str, timeout: int = None) -> bool:
        """
        요소 텍스트 검증
        
        Args:
            locator: 요소 로케이터
            expected_text: 예상 텍스트
            timeout: 대기 시간
            
        Returns:
            검증 결과
        """
        try:
            actual_text = self.get_text(locator, timeout)
            if expected_text in actual_text:
                self.logger.debug(f"Text verification passed: {expected_text}")
                return True
            else:
                self.logger.error(f"Text verification failed. Expected: {expected_text}, Actual: {actual_text}")
                return False
        except Exception as e:
            self.logger.error(f"Text verification failed: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.__class__.__name__}(url={self.get_current_url()})"
    
    def __repr__(self) -> str:
        """객체 표현"""
        return self.__str__()