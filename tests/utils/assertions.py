"""
커스텀 어설션 함수들

이 모듈은 테스트에서 사용할 수 있는 다양한 커스텀 어설션 함수들을 제공합니다.
"""

import time
from typing import Any, Dict, List, Optional, Union, Callable
from unittest.mock import Mock
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ==================== 요소 관련 어설션 ====================

def assert_element_present(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """요소가 존재하는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
    except TimeoutException:
        error_msg = message or f"Element {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_element_visible(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """요소가 보이는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        error_msg = message or f"Element {locator} not visible within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_element_clickable(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """요소가 클릭 가능한지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
    except TimeoutException:
        error_msg = message or f"Element {locator} not clickable within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_element_invisible(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """요소가 보이지 않는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )
    except TimeoutException:
        error_msg = message or f"Element {locator} still visible after {timeout} seconds"
        raise AssertionError(error_msg)


def assert_element_text(driver: WebDriver, locator: tuple, expected_text: str, 
                       exact_match: bool = True, timeout: int = 10, message: str = None):
    """요소의 텍스트 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_text = element.text
        
        if exact_match:
            assert actual_text == expected_text, \
                message or f"Expected text '{expected_text}', got '{actual_text}'"
        else:
            assert expected_text in actual_text, \
                message or f"Text '{expected_text}' not found in '{actual_text}'"
    except TimeoutException:
        error_msg = message or f"Element {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_element_attribute(driver: WebDriver, locator: tuple, attribute: str, 
                           expected_value: str, timeout: int = 10, message: str = None):
    """요소의 속성값 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_value = element.get_attribute(attribute)
        
        assert actual_value == expected_value, \
            message or f"Expected {attribute}='{expected_value}', got '{actual_value}'"
    except TimeoutException:
        error_msg = message or f"Element {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_elements_count(driver: WebDriver, locator: tuple, expected_count: int, 
                         timeout: int = 10, message: str = None):
    """요소의 개수 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    
    def check_count(driver):
        elements = driver.find_elements(*locator)
        return len(elements) == expected_count
    
    try:
        WebDriverWait(driver, timeout).until(check_count)
    except TimeoutException:
        elements = driver.find_elements(*locator)
        actual_count = len(elements)
        error_msg = message or f"Expected {expected_count} elements, found {actual_count}"
        raise AssertionError(error_msg)


# ==================== 페이지 관련 어설션 ====================

def assert_page_loaded(driver: WebDriver, timeout: int = 30, message: str = None):
    """페이지가 완전히 로드되었는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    
    def page_loaded(driver):
        return driver.execute_script("return document.readyState") == "complete"
    
    try:
        WebDriverWait(driver, timeout).until(page_loaded)
    except TimeoutException:
        error_msg = message or f"Page not loaded within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_url_contains(driver: WebDriver, expected_url_part: str, timeout: int = 10, message: str = None):
    """URL에 특정 문자열이 포함되어 있는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.url_contains(expected_url_part)
        )
    except TimeoutException:
        current_url = driver.current_url
        error_msg = message or f"URL '{current_url}' does not contain '{expected_url_part}'"
        raise AssertionError(error_msg)


def assert_url_equals(driver: WebDriver, expected_url: str, timeout: int = 10, message: str = None):
    """URL이 정확히 일치하는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.url_to_be(expected_url)
        )
    except TimeoutException:
        current_url = driver.current_url
        error_msg = message or f"Expected URL '{expected_url}', got '{current_url}'"
        raise AssertionError(error_msg)


def assert_title_contains(driver: WebDriver, expected_title_part: str, timeout: int = 10, message: str = None):
    """페이지 제목에 특정 문자열이 포함되어 있는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.title_contains(expected_title_part)
        )
    except TimeoutException:
        current_title = driver.title
        error_msg = message or f"Title '{current_title}' does not contain '{expected_title_part}'"
        raise AssertionError(error_msg)


def assert_title_equals(driver: WebDriver, expected_title: str, timeout: int = 10, message: str = None):
    """페이지 제목이 정확히 일치하는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.title_is(expected_title)
        )
    except TimeoutException:
        current_title = driver.title
        error_msg = message or f"Expected title '{expected_title}', got '{current_title}'"
        raise AssertionError(error_msg)


# ==================== 텍스트 관련 어설션 ====================

def assert_text_present(driver: WebDriver, text: str, timeout: int = 10, message: str = None):
    """페이지에 특정 텍스트가 있는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    
    def text_present(driver):
        return text in driver.page_source
    
    try:
        WebDriverWait(driver, timeout).until(text_present)
    except TimeoutException:
        error_msg = message or f"Text '{text}' not found on page"
        raise AssertionError(error_msg)


def assert_text_not_present(driver: WebDriver, text: str, timeout: int = 10, message: str = None):
    """페이지에 특정 텍스트가 없는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    
    def text_not_present(driver):
        return text not in driver.page_source
    
    try:
        WebDriverWait(driver, timeout).until(text_not_present)
    except TimeoutException:
        error_msg = message or f"Text '{text}' found on page when it shouldn't be"
        raise AssertionError(error_msg)


# ==================== 폼 관련 어설션 ====================

def assert_form_field_value(driver: WebDriver, locator: tuple, expected_value: str, 
                           timeout: int = 10, message: str = None):
    """폼 필드의 값 확인"""
    assert_element_attribute(driver, locator, "value", expected_value, timeout, message)


def assert_checkbox_checked(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """체크박스가 체크되어 있는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        assert element.is_selected(), message or f"Checkbox {locator} is not checked"
    except TimeoutException:
        error_msg = message or f"Checkbox {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_checkbox_unchecked(driver: WebDriver, locator: tuple, timeout: int = 10, message: str = None):
    """체크박스가 체크되어 있지 않은지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        assert not element.is_selected(), message or f"Checkbox {locator} is checked"
    except TimeoutException:
        error_msg = message or f"Checkbox {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_dropdown_selected(driver: WebDriver, locator: tuple, expected_text: str, 
                            timeout: int = 10, message: str = None):
    """드롭다운에서 선택된 옵션 확인"""
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        select = Select(element)
        selected_option = select.first_selected_option
        actual_text = selected_option.text
        
        assert actual_text == expected_text, \
            message or f"Expected selected option '{expected_text}', got '{actual_text}'"
    except TimeoutException:
        error_msg = message or f"Dropdown {locator} not found within {timeout} seconds"
        raise AssertionError(error_msg)


# ==================== 알림 관련 어설션 ====================

def assert_alert_present(driver: WebDriver, timeout: int = 10, message: str = None):
    """알림창이 있는지 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
    except TimeoutException:
        error_msg = message or f"Alert not present within {timeout} seconds"
        raise AssertionError(error_msg)


def assert_alert_text(driver: WebDriver, expected_text: str, timeout: int = 10, message: str = None):
    """알림창의 텍스트 확인"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        alert = WebDriverWait(driver, timeout).until(EC.alert_is_present())
        actual_text = alert.text
        
        assert actual_text == expected_text, \
            message or f"Expected alert text '{expected_text}', got '{actual_text}'"
    except TimeoutException:
        error_msg = message or f"Alert not present within {timeout} seconds"
        raise AssertionError(error_msg)


# ==================== Mock 관련 어설션 ====================

def assert_mock_called(mock_obj: Mock, method_name: str = None, times: int = None, message: str = None):
    """Mock 객체의 호출 확인"""
    if method_name:
        mock_method = getattr(mock_obj, method_name)
        if times is not None:
            assert mock_method.call_count == times, \
                message or f"Expected {method_name} to be called {times} times, called {mock_method.call_count} times"
        else:
            assert mock_method.called, \
                message or f"Expected {method_name} to be called"
    else:
        if times is not None:
            assert mock_obj.call_count == times, \
                message or f"Expected mock to be called {times} times, called {mock_obj.call_count} times"
        else:
            assert mock_obj.called, \
                message or "Expected mock to be called"


def assert_mock_called_with(mock_obj: Mock, *args, method_name: str = None, **kwargs):
    """Mock 객체가 특정 인자로 호출되었는지 확인"""
    if method_name:
        mock_method = getattr(mock_obj, method_name)
        mock_method.assert_called_with(*args, **kwargs)
    else:
        mock_obj.assert_called_with(*args, **kwargs)


def assert_mock_not_called(mock_obj: Mock, method_name: str = None, message: str = None):
    """Mock 객체가 호출되지 않았는지 확인"""
    if method_name:
        mock_method = getattr(mock_obj, method_name)
        assert not mock_method.called, \
            message or f"Expected {method_name} not to be called"
    else:
        assert not mock_obj.called, \
            message or "Expected mock not to be called"


# ==================== 성능 관련 어설션 ====================

def assert_execution_time(func: Callable, max_time: float, *args, **kwargs):
    """함수 실행 시간 확인"""
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    
    assert execution_time <= max_time, \
        f"Function took {execution_time:.3f}s, expected <= {max_time}s"
    
    return result


def assert_page_load_time(driver: WebDriver, max_time: float, url: str = None):
    """페이지 로딩 시간 확인"""
    start_time = time.time()
    
    if url:
        driver.get(url)
    
    assert_page_loaded(driver)
    load_time = time.time() - start_time
    
    assert load_time <= max_time, \
        f"Page loaded in {load_time:.3f}s, expected <= {max_time}s"


# ==================== 파일 관련 어설션 ====================

def assert_file_exists(file_path: Union[str, Path], message: str = None):
    """파일이 존재하는지 확인"""
    path = Path(file_path)
    assert path.exists(), message or f"File {file_path} does not exist"


def assert_file_not_exists(file_path: Union[str, Path], message: str = None):
    """파일이 존재하지 않는지 확인"""
    path = Path(file_path)
    assert not path.exists(), message or f"File {file_path} exists when it shouldn't"


def assert_file_contains(file_path: Union[str, Path], expected_content: str, message: str = None):
    """파일에 특정 내용이 있는지 확인"""
    path = Path(file_path)
    assert path.exists(), f"File {file_path} does not exist"
    
    content = path.read_text()
    assert expected_content in content, \
        message or f"Content '{expected_content}' not found in file {file_path}"


def assert_directory_exists(dir_path: Union[str, Path], message: str = None):
    """디렉토리가 존재하는지 확인"""
    path = Path(dir_path)
    assert path.exists() and path.is_dir(), \
        message or f"Directory {dir_path} does not exist"


# ==================== 데이터 관련 어설션 ====================

def assert_dict_contains(actual_dict: Dict, expected_subset: Dict, message: str = None):
    """딕셔너리에 특정 키-값 쌍이 있는지 확인"""
    for key, expected_value in expected_subset.items():
        assert key in actual_dict, \
            message or f"Key '{key}' not found in dictionary"
        assert actual_dict[key] == expected_value, \
            message or f"Expected {key}='{expected_value}', got '{actual_dict[key]}'"


def assert_list_contains(actual_list: List, expected_item: Any, message: str = None):
    """리스트에 특정 항목이 있는지 확인"""
    assert expected_item in actual_list, \
        message or f"Item '{expected_item}' not found in list"


def assert_list_length(actual_list: List, expected_length: int, message: str = None):
    """리스트의 길이 확인"""
    actual_length = len(actual_list)
    assert actual_length == expected_length, \
        message or f"Expected list length {expected_length}, got {actual_length}"


# ==================== 복합 어설션 ====================

def assert_login_successful(driver: WebDriver, expected_url_part: str = None, 
                          success_indicator: tuple = None, timeout: int = 10):
    """로그인 성공 확인 (복합 검증)"""
    # URL 변경 확인
    if expected_url_part:
        assert_url_contains(driver, expected_url_part, timeout)
    
    # 성공 지표 요소 확인
    if success_indicator:
        assert_element_present(driver, success_indicator, timeout)
    
    # 로그인 페이지가 아님을 확인
    current_url = driver.current_url
    assert '/login' not in current_url.lower(), \
        f"Still on login page: {current_url}"


def assert_form_validation_error(driver: WebDriver, error_locator: tuple, 
                               expected_error: str = None, timeout: int = 10):
    """폼 검증 오류 확인"""
    # 오류 요소가 보이는지 확인
    assert_element_visible(driver, error_locator, timeout)
    
    # 오류 메시지 확인
    if expected_error:
        assert_element_text(driver, error_locator, expected_error, exact_match=False, timeout=timeout)


def assert_page_navigation(driver: WebDriver, from_url_part: str, to_url_part: str, 
                          navigation_action: Callable, timeout: int = 10):
    """페이지 네비게이션 확인"""
    # 시작 페이지 확인
    assert_url_contains(driver, from_url_part, timeout)
    
    # 네비게이션 액션 실행
    navigation_action()
    
    # 목적지 페이지 확인
    assert_url_contains(driver, to_url_part, timeout)


# ==================== 커스텀 어설션 데코레이터 ====================

def soft_assert(func):
    """소프트 어설션 데코레이터 (실패해도 테스트 계속 진행)"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError as e:
            print(f"Soft assertion failed: {e}")
            return False
    return wrapper


def retry_assert(max_attempts: int = 3, delay: float = 1.0):
    """재시도 어설션 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except AssertionError as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue
            
            raise last_exception
        return wrapper
    return decorator