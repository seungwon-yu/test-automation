"""
LoginPage 클래스 - 로그인 페이지 Page Object

이 모듈은 로그인 페이지의 UI 요소와 동작을 캡슐화합니다.
로그인 폼 상호작용, 로그인 성공/실패 검증, 에러 메시지 처리 등의 기능을 제공합니다.
"""

from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage
from ..core.logging import get_logger
from ..core.exceptions import (
    LoginException,
    ElementNotFoundException,
    PageLoadTimeoutException
)


class LoginPage(BasePage):
    """
    로그인 페이지 Page Object 클래스
    
    로그인 폼의 모든 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 로그인 폼 요소들
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-btn")
    REMEMBER_ME_CHECKBOX = (By.ID, "remember-me")
    
    # 대체 로케이터들 (다양한 사이트 지원)
    ALT_USERNAME_LOCATORS = [
        (By.NAME, "username"),
        (By.NAME, "email"),
        (By.NAME, "user"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[placeholder*='username' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='email' i]"),
        (By.XPATH, "//input[@type='text' and contains(@placeholder, 'username')]"),
        (By.XPATH, "//input[@type='email']")
    ]
    
    ALT_PASSWORD_LOCATORS = [
        (By.NAME, "password"),
        (By.NAME, "pass"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[placeholder*='password' i]"),
        (By.XPATH, "//input[@type='password']")
    ]
    
    ALT_LOGIN_BUTTON_LOCATORS = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.CSS_SELECTOR, "button:contains('Login')"),
        (By.CSS_SELECTOR, "button:contains('Sign In')"),
        (By.CSS_SELECTOR, "button:contains('로그인')"),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(text(), 'Sign In')]"),
        (By.XPATH, "//button[contains(text(), '로그인')]"),
        (By.XPATH, "//input[@value='Login']"),
        (By.XPATH, "//input[@value='Sign In']")
    ]
    
    # 메시지 및 상태 요소들
    ERROR_MESSAGE = (By.CLASS_NAME, "error-msg")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-msg")
    LOADING_INDICATOR = (By.CLASS_NAME, "loading")
    
    # 대체 에러 메시지 로케이터들
    ALT_ERROR_LOCATORS = [
        (By.CSS_SELECTOR, ".error"),
        (By.CSS_SELECTOR, ".alert-danger"),
        (By.CSS_SELECTOR, ".notification.error"),
        (By.CSS_SELECTOR, "[role='alert']"),
        (By.XPATH, "//*[contains(@class, 'error')]"),
        (By.XPATH, "//*[contains(@class, 'invalid')]"),
        (By.XPATH, "//*[contains(@class, 'danger')]")
    ]
    
    # 로그인 성공 확인 요소들
    DASHBOARD_INDICATOR = (By.CSS_SELECTOR, ".dashboard")
    USER_MENU = (By.CSS_SELECTOR, ".user-menu")
    LOGOUT_BUTTON = (By.CSS_SELECTOR, ".logout")
    PROFILE_LINK = (By.CSS_SELECTOR, ".profile")
    
    # 대체 성공 확인 로케이터들
    ALT_SUCCESS_INDICATORS = [
        (By.CSS_SELECTOR, ".welcome"),
        (By.CSS_SELECTOR, ".user-info"),
        (By.CSS_SELECTOR, ".main-content"),
        (By.CSS_SELECTOR, "[data-testid='dashboard']"),
        (By.XPATH, "//*[contains(@class, 'welcome')]"),
        (By.XPATH, "//*[contains(text(), 'Welcome')]"),
        (By.XPATH, "//*[contains(text(), '환영')]")
    ]
    
    # 추가 폼 요소들
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, ".forgot-password")
    SIGNUP_LINK = (By.CSS_SELECTOR, ".signup-link")
    CAPTCHA_INPUT = (By.ID, "captcha")
    
    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        LoginPage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 로그인 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        
        # 로그인 페이지 특화 설정
        self.login_timeout = 30  # 로그인 처리 대기 시간
        self.redirect_timeout = 10  # 리다이렉트 대기 시간
        
        self.logger.debug("LoginPage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_login(self, login_url: str = None) -> None:
        """
        로그인 페이지로 이동
        
        Args:
            login_url: 로그인 페이지 URL (None이면 기본 URL 사용)
        """
        url = login_url or f"{self.base_url}/login"
        self.logger.info(f"Navigating to login page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_login_page_load()
            self.logger.info("Successfully navigated to login page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to login page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_login_page_load(self) -> None:
        """로그인 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for login page to load")
        
        try:
            # 기본 페이지 로딩 대기
            self.wait_for_page_load()
            
            # 로그인 폼 요소들이 로드될 때까지 대기
            self._find_username_field()
            self._find_password_field()
            self._find_login_button()
            
            self.logger.debug("Login page loaded successfully")
            
        except ElementNotFoundException as e:
            self.logger.error(f"Login page elements not found: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Login page load failed: {str(e)}")
            raise PageLoadTimeoutException("login page", self.default_timeout)
    
    # ==================== 요소 찾기 (Smart Locator) ====================
    
    def _find_username_field(self) -> tuple:
        """사용자명 입력 필드 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.USERNAME_INPUT, timeout=2):
            return self.USERNAME_INPUT
        
        # 대체 로케이터들 시도
        for locator in self.ALT_USERNAME_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found username field with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("username field", timeout=self.default_timeout)
    
    def _find_password_field(self) -> tuple:
        """비밀번호 입력 필드 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.PASSWORD_INPUT, timeout=2):
            return self.PASSWORD_INPUT
        
        # 대체 로케이터들 시도
        for locator in self.ALT_PASSWORD_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found password field with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("password field", timeout=self.default_timeout)
    
    def _find_login_button(self) -> tuple:
        """로그인 버튼 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.LOGIN_BUTTON, timeout=2):
            return self.LOGIN_BUTTON
        
        # 대체 로케이터들 시도
        for locator in self.ALT_LOGIN_BUTTON_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found login button with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("login button", timeout=self.default_timeout)
    
    def _find_error_message_element(self) -> Optional[tuple]:
        """에러 메시지 요소 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.ERROR_MESSAGE, timeout=2):
            return self.ERROR_MESSAGE
        
        # 대체 로케이터들 시도
        for locator in self.ALT_ERROR_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found error message with alternative locator: {locator}")
                return locator
        
        return None
    
    def _find_success_indicator(self) -> Optional[tuple]:
        """로그인 성공 지표 요소 찾기"""
        # 기본 지표들 시도
        success_indicators = [
            self.DASHBOARD_INDICATOR,
            self.USER_MENU,
            self.LOGOUT_BUTTON,
            self.PROFILE_LINK
        ]
        
        for locator in success_indicators:
            if self.is_element_present(locator, timeout=2):
                return locator
        
        # 대체 지표들 시도
        for locator in self.ALT_SUCCESS_INDICATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found success indicator with alternative locator: {locator}")
                return locator
        
        return None
    
    # ==================== 로그인 폼 상호작용 ====================
    
    def enter_username(self, username: str) -> None:
        """
        사용자명 입력
        
        Args:
            username: 입력할 사용자명
        """
        self.logger.debug(f"Entering username: {username}")
        
        try:
            username_locator = self._find_username_field()
            self.input_text(username_locator, username, clear_first=True)
            self.logger.debug("Username entered successfully")
        except Exception as e:
            self.logger.error(f"Failed to enter username: {str(e)}")
            raise
    
    def enter_password(self, password: str) -> None:
        """
        비밀번호 입력
        
        Args:
            password: 입력할 비밀번호
        """
        self.logger.debug("Entering password")
        
        try:
            password_locator = self._find_password_field()
            self.input_text(password_locator, password, clear_first=True)
            self.logger.debug("Password entered successfully")
        except Exception as e:
            self.logger.error(f"Failed to enter password: {str(e)}")
            raise
    
    def click_login_button(self) -> None:
        """로그인 버튼 클릭"""
        self.logger.debug("Clicking login button")
        
        try:
            login_button_locator = self._find_login_button()
            self.click_element(login_button_locator)
            self.logger.debug("Login button clicked successfully")
        except Exception as e:
            self.logger.error(f"Failed to click login button: {str(e)}")
            raise
    
    def toggle_remember_me(self, enable: bool = True) -> None:
        """
        Remember Me 체크박스 토글
        
        Args:
            enable: 체크 여부
        """
        if not self.is_element_present(self.REMEMBER_ME_CHECKBOX, timeout=2):
            self.logger.warning("Remember Me checkbox not found")
            return
        
        try:
            checkbox = self.find_element(self.REMEMBER_ME_CHECKBOX)
            is_checked = checkbox.is_selected()
            
            if (enable and not is_checked) or (not enable and is_checked):
                self.click_element(self.REMEMBER_ME_CHECKBOX)
                self.logger.debug(f"Remember Me checkbox {'enabled' if enable else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to toggle Remember Me checkbox: {str(e)}")
    
    def enter_captcha(self, captcha_value: str) -> None:
        """
        CAPTCHA 입력 (있는 경우)
        
        Args:
            captcha_value: CAPTCHA 값
        """
        if not self.is_element_present(self.CAPTCHA_INPUT, timeout=2):
            self.logger.debug("CAPTCHA field not present")
            return
        
        try:
            self.input_text(self.CAPTCHA_INPUT, captcha_value, clear_first=True)
            self.logger.debug("CAPTCHA entered successfully")
        except Exception as e:
            self.logger.error(f"Failed to enter CAPTCHA: {str(e)}")
    
    # ==================== 로그인 메인 메서드 ====================
    
    def login(self, username: str, password: str, remember_me: bool = False, 
              captcha: str = None, wait_for_redirect: bool = True) -> bool:
        """
        로그인 수행
        
        Args:
            username: 사용자명
            password: 비밀번호
            remember_me: Remember Me 체크 여부
            captcha: CAPTCHA 값 (있는 경우)
            wait_for_redirect: 리다이렉트 대기 여부
            
        Returns:
            로그인 성공 여부
            
        Raises:
            LoginException: 로그인 실패 시
        """
        self.logger.info(f"Attempting login for user: {username}")
        
        try:
            # 로그인 페이지 로딩 확인
            self.wait_for_login_page_load()
            
            # 로그인 폼 입력
            self.enter_username(username)
            self.enter_password(password)
            
            # 선택적 요소들 처리
            if remember_me:
                self.toggle_remember_me(True)
            
            if captcha:
                self.enter_captcha(captcha)
            
            # 로그인 버튼 클릭
            self.click_login_button()
            
            # 로딩 대기 (있는 경우)
            self._wait_for_login_processing()
            
            # 로그인 결과 확인
            if wait_for_redirect:
                success = self.is_login_successful()
                
                if success:
                    self.logger.info(f"Login successful for user: {username}")
                    return True
                else:
                    error_msg = self.get_error_message()
                    self.logger.error(f"Login failed for user: {username}. Error: {error_msg}")
                    raise LoginException(f"Login failed: {error_msg}")
            else:
                self.logger.info("Login form submitted, not waiting for redirect")
                return True
                
        except LoginException:
            raise
        except Exception as e:
            self.logger.error(f"Login process failed: {str(e)}")
            raise LoginException(f"Login process error: {str(e)}")
    
    def quick_login(self, credentials: Dict[str, str]) -> bool:
        """
        빠른 로그인 (딕셔너리 형태의 인증 정보 사용)
        
        Args:
            credentials: {'username': '...', 'password': '...', 'captcha': '...'} 형태
            
        Returns:
            로그인 성공 여부
        """
        username = credentials.get('username', '')
        password = credentials.get('password', '')
        captcha = credentials.get('captcha')
        remember_me = credentials.get('remember_me', False)
        
        return self.login(username, password, remember_me, captcha)
    
    # ==================== 로그인 상태 확인 ====================
    
    def is_login_successful(self, timeout: int = None) -> bool:
        """
        로그인 성공 여부 확인
        
        Args:
            timeout: 확인 대기 시간
            
        Returns:
            로그인 성공 여부
        """
        timeout = timeout or self.redirect_timeout
        
        self.logger.debug("Checking login success")
        
        try:
            # URL 변경 확인 (로그인 페이지에서 벗어났는지)
            current_url = self.get_current_url()
            if '/login' not in current_url.lower():
                self.logger.debug("URL changed from login page")
                
                # 성공 지표 요소 확인
                success_indicator = self._find_success_indicator()
                if success_indicator:
                    self.logger.debug(f"Found success indicator: {success_indicator}")
                    return True
                
                # 에러 메시지가 없으면 성공으로 간주
                if not self.has_error_message():
                    self.logger.debug("No error message found, assuming success")
                    return True
            
            # 에러 메시지 확인
            if self.has_error_message():
                self.logger.debug("Error message found, login failed")
                return False
            
            # 추가 대기 후 재확인
            self.wait(2)
            current_url = self.get_current_url()
            if '/login' not in current_url.lower():
                self.logger.debug("Login successful - redirected from login page")
                return True
            
            self.logger.debug("Still on login page, login likely failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login success: {str(e)}")
            return False
    
    def is_logged_in(self) -> bool:
        """
        현재 로그인 상태 확인 (페이지 이동 없이)
        
        Returns:
            로그인 상태 여부
        """
        try:
            # 로그인 상태 지표들 확인
            success_indicator = self._find_success_indicator()
            if success_indicator:
                return True
            
            # 현재 URL이 로그인 페이지가 아닌지 확인
            current_url = self.get_current_url()
            if '/login' not in current_url.lower():
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False
    
    def _wait_for_login_processing(self) -> None:
        """로그인 처리 대기 (로딩 인디케이터 등)"""
        # 로딩 인디케이터가 있으면 사라질 때까지 대기
        if self.is_element_present(self.LOADING_INDICATOR, timeout=2):
            self.logger.debug("Waiting for loading indicator to disappear")
            self.wait_for_element_invisible(self.LOADING_INDICATOR, timeout=self.login_timeout)
        
        # 짧은 대기 (JavaScript 처리 시간)
        self.wait(1)
    
    # ==================== 에러 메시지 처리 ====================
    
    def has_error_message(self) -> bool:
        """
        에러 메시지 존재 여부 확인
        
        Returns:
            에러 메시지 존재 여부
        """
        error_locator = self._find_error_message_element()
        return error_locator is not None
    
    def get_error_message(self) -> str:
        """
        에러 메시지 텍스트 가져오기
        
        Returns:
            에러 메시지 텍스트 (없으면 빈 문자열)
        """
        try:
            error_locator = self._find_error_message_element()
            if error_locator:
                error_text = self.get_text(error_locator)
                self.logger.debug(f"Found error message: {error_text}")
                return error_text.strip()
            else:
                self.logger.debug("No error message found")
                return ""
        except Exception as e:
            self.logger.error(f"Failed to get error message: {str(e)}")
            return ""
    
    def get_all_error_messages(self) -> list:
        """
        모든 에러 메시지 가져오기
        
        Returns:
            에러 메시지 리스트
        """
        error_messages = []
        
        # 모든 가능한 에러 로케이터 확인
        all_error_locators = [self.ERROR_MESSAGE] + self.ALT_ERROR_LOCATORS
        
        for locator in all_error_locators:
            try:
                if self.is_element_present(locator, timeout=1):
                    elements = self.find_elements(locator)
                    for element in elements:
                        text = element.text.strip()
                        if text and text not in error_messages:
                            error_messages.append(text)
            except Exception:
                continue
        
        self.logger.debug(f"Found {len(error_messages)} error messages")
        return error_messages
    
    # ==================== 추가 기능 ====================
    
    def click_forgot_password(self) -> None:
        """비밀번호 찾기 링크 클릭"""
        if self.is_element_present(self.FORGOT_PASSWORD_LINK, timeout=2):
            self.click_element(self.FORGOT_PASSWORD_LINK)
            self.logger.debug("Clicked forgot password link")
        else:
            self.logger.warning("Forgot password link not found")
    
    def click_signup_link(self) -> None:
        """회원가입 링크 클릭"""
        if self.is_element_present(self.SIGNUP_LINK, timeout=2):
            self.click_element(self.SIGNUP_LINK)
            self.logger.debug("Clicked signup link")
        else:
            self.logger.warning("Signup link not found")
    
    def get_login_form_info(self) -> Dict[str, Any]:
        """
        로그인 폼 정보 수집
        
        Returns:
            폼 정보 딕셔너리
        """
        info = {
            'has_username_field': False,
            'has_password_field': False,
            'has_login_button': False,
            'has_remember_me': False,
            'has_captcha': False,
            'has_forgot_password': False,
            'has_signup_link': False,
            'current_url': self.get_current_url(),
            'page_title': self.get_page_title()
        }
        
        try:
            info['has_username_field'] = self._find_username_field() is not None
        except:
            pass
        
        try:
            info['has_password_field'] = self._find_password_field() is not None
        except:
            pass
        
        try:
            info['has_login_button'] = self._find_login_button() is not None
        except:
            pass
        
        info['has_remember_me'] = self.is_element_present(self.REMEMBER_ME_CHECKBOX, timeout=1)
        info['has_captcha'] = self.is_element_present(self.CAPTCHA_INPUT, timeout=1)
        info['has_forgot_password'] = self.is_element_present(self.FORGOT_PASSWORD_LINK, timeout=1)
        info['has_signup_link'] = self.is_element_present(self.SIGNUP_LINK, timeout=1)
        
        self.logger.debug(f"Login form info: {info}")
        return info
    
    def clear_login_form(self) -> None:
        """로그인 폼 초기화"""
        try:
            username_locator = self._find_username_field()
            password_locator = self._find_password_field()
            
            # 필드 내용 삭제
            username_element = self.find_element(username_locator)
            password_element = self.find_element(password_locator)
            
            username_element.clear()
            password_element.clear()
            
            # Remember Me 체크 해제
            if self.is_element_present(self.REMEMBER_ME_CHECKBOX, timeout=1):
                checkbox = self.find_element(self.REMEMBER_ME_CHECKBOX)
                if checkbox.is_selected():
                    self.click_element(self.REMEMBER_ME_CHECKBOX)
            
            self.logger.debug("Login form cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear login form: {str(e)}")
    
    # ==================== 테스트 지원 메서드 ====================
    
    def validate_login_page_elements(self) -> Dict[str, bool]:
        """
        로그인 페이지 필수 요소 검증
        
        Returns:
            검증 결과 딕셔너리
        """
        validation_results = {}
        
        try:
            validation_results['username_field'] = self._find_username_field() is not None
        except:
            validation_results['username_field'] = False
        
        try:
            validation_results['password_field'] = self._find_password_field() is not None
        except:
            validation_results['password_field'] = False
        
        try:
            validation_results['login_button'] = self._find_login_button() is not None
        except:
            validation_results['login_button'] = False
        
        validation_results['page_loaded'] = True
        
        all_valid = all(validation_results.values())
        validation_results['all_elements_present'] = all_valid
        
        self.logger.debug(f"Page validation results: {validation_results}")
        return validation_results
    
    def take_login_screenshot(self, filename: str = None) -> str:
        """
        로그인 페이지 스크린샷 촬영
        
        Args:
            filename: 파일명
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"login_page_{timestamp}.png"
        
        return self.take_screenshot(filename)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"LoginPage(url={self.get_current_url()})"