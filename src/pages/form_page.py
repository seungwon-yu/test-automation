"""
FormPage 클래스 - 폼 페이지 Page Object

이 모듈은 다양한 폼 페이지의 UI 요소와 동작을 캡슐화합니다.
텍스트 입력, 드롭다운 선택, 체크박스/라디오 버튼, 파일 업로드 등의 기능을 제공합니다.
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


class FormPage(BasePage):
    """
    폼 페이지 Page Object 클래스
    
    다양한 폼 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 폼 컨테이너
    FORM_CONTAINER = (By.CSS_SELECTOR, ".form-container")
    MAIN_FORM = (By.CSS_SELECTOR, "form")
    
    # 텍스트 입력 필드들
    FIRST_NAME = (By.ID, "first-name")
    LAST_NAME = (By.ID, "last-name")
    EMAIL = (By.ID, "email")
    PHONE = (By.ID, "phone")
    MESSAGE = (By.ID, "message")
    
    # 드롭다운 선택
    COUNTRY_SELECT = (By.ID, "country")
    CATEGORY_SELECT = (By.ID, "category")
    
    # 체크박스와 라디오 버튼
    NEWSLETTER_CHECKBOX = (By.ID, "newsletter")
    TERMS_CHECKBOX = (By.ID, "terms")
    GENDER_MALE = (By.CSS_SELECTOR, "input[name='gender'][value='male']")
    GENDER_FEMALE = (By.CSS_SELECTOR, "input[name='gender'][value='female']")
    
    # 파일 업로드
    FILE_UPLOAD = (By.ID, "file-upload")
    
    # 버튼들
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    RESET_BUTTON = (By.CSS_SELECTOR, "button[type='reset']")
    CANCEL_BUTTON = (By.CSS_SELECTOR, ".cancel-button")
    
    # 메시지 및 상태
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message")
    VALIDATION_ERROR = (By.CSS_SELECTOR, ".validation-error")
    
    # 대체 로케이터들
    ALT_FORM_LOCATORS = [
        (By.CSS_SELECTOR, ".contact-form"),
        (By.CSS_SELECTOR, ".registration-form"),
        (By.XPATH, "//form")
    ]
    
    ALT_SUBMIT_LOCATORS = [
        (By.CSS_SELECTOR, ".submit-btn"),
        (By.CSS_SELECTOR, ".send-button"),
        (By.XPATH, "//button[contains(text(), 'Submit')]"),
        (By.XPATH, "//input[@type='submit']")
    ]

    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        FormPage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 폼 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("FormPage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_form(self, form_url: str = None) -> None:
        """
        폼 페이지로 이동
        
        Args:
            form_url: 폼 페이지 URL (None이면 기본 URL 사용)
        """
        url = form_url or f"{self.base_url}/contact"
        self.logger.info(f"Navigating to form page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_form_load()
            self.logger.info("Successfully navigated to form page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to form page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_form_load(self) -> None:
        """폼 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for form page to load")
        
        try:
            self.wait_for_page_load()
            self._find_form_container()
            self.logger.debug("Form page loaded successfully")
        except Exception as e:
            self.logger.error(f"Form page load failed: {str(e)}")
            raise PageLoadTimeoutException("form page", self.default_timeout)
    
    def _find_form_container(self) -> tuple:
        """폼 컨테이너 찾기"""
        if self.is_element_present(self.FORM_CONTAINER, timeout=2):
            return self.FORM_CONTAINER
        
        for locator in self.ALT_FORM_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found form with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("form container", timeout=self.default_timeout)
    
    # ==================== 폼 입력 메서드 ====================
    
    def fill_personal_info(self, info: Dict[str, str]) -> bool:
        """
        개인 정보 입력
        
        Args:
            info: 개인 정보 딕셔너리
                {
                    'first_name': '홍',
                    'last_name': '길동',
                    'email': 'hong@example.com',
                    'phone': '010-1234-5678'
                }
        
        Returns:
            입력 성공 여부
        """
        self.logger.debug("Filling personal information")
        
        try:
            field_mappings = {
                'first_name': self.FIRST_NAME,
                'last_name': self.LAST_NAME,
                'email': self.EMAIL,
                'phone': self.PHONE
            }
            
            for field_name, locator in field_mappings.items():
                if field_name in info and info[field_name]:
                    if self.is_element_present(locator, timeout=2):
                        self.input_text(locator, info[field_name], clear_first=True)
                        self.logger.debug(f"Filled {field_name}: {info[field_name]}")
                    else:
                        self.logger.warning(f"Field {field_name} not found")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to fill personal info: {str(e)}")
            return False
    
    def fill_message(self, message: str) -> bool:
        """
        메시지 입력
        
        Args:
            message: 입력할 메시지
            
        Returns:
            입력 성공 여부
        """
        try:
            if self.is_element_present(self.MESSAGE, timeout=2):
                self.input_text(self.MESSAGE, message, clear_first=True)
                self.logger.debug("Message filled successfully")
                return True
            else:
                self.logger.warning("Message field not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to fill message: {str(e)}")
            return False
    
    def select_country(self, country: str) -> bool:
        """
        국가 선택
        
        Args:
            country: 선택할 국가명
            
        Returns:
            선택 성공 여부
        """
        try:
            if self.is_element_present(self.COUNTRY_SELECT, timeout=2):
                self.select_dropdown_by_text(self.COUNTRY_SELECT, country)
                self.logger.debug(f"Country selected: {country}")
                return True
            else:
                self.logger.warning("Country select not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to select country: {str(e)}")
            return False
    
    def select_category(self, category: str) -> bool:
        """
        카테고리 선택
        
        Args:
            category: 선택할 카테고리
            
        Returns:
            선택 성공 여부
        """
        try:
            if self.is_element_present(self.CATEGORY_SELECT, timeout=2):
                self.select_dropdown_by_text(self.CATEGORY_SELECT, category)
                self.logger.debug(f"Category selected: {category}")
                return True
            else:
                self.logger.warning("Category select not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to select category: {str(e)}")
            return False
    
    def set_newsletter_subscription(self, subscribe: bool) -> bool:
        """
        뉴스레터 구독 설정
        
        Args:
            subscribe: 구독 여부
            
        Returns:
            설정 성공 여부
        """
        try:
            if self.is_element_present(self.NEWSLETTER_CHECKBOX, timeout=2):
                checkbox = self.find_element(self.NEWSLETTER_CHECKBOX)
                is_checked = checkbox.is_selected()
                
                if (subscribe and not is_checked) or (not subscribe and is_checked):
                    self.click_element(self.NEWSLETTER_CHECKBOX)
                    self.logger.debug(f"Newsletter subscription set to: {subscribe}")
                
                return True
            else:
                self.logger.warning("Newsletter checkbox not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to set newsletter subscription: {str(e)}")
            return False
    
    def accept_terms(self, accept: bool = True) -> bool:
        """
        약관 동의
        
        Args:
            accept: 동의 여부
            
        Returns:
            설정 성공 여부
        """
        try:
            if self.is_element_present(self.TERMS_CHECKBOX, timeout=2):
                checkbox = self.find_element(self.TERMS_CHECKBOX)
                is_checked = checkbox.is_selected()
                
                if (accept and not is_checked) or (not accept and is_checked):
                    self.click_element(self.TERMS_CHECKBOX)
                    self.logger.debug(f"Terms acceptance set to: {accept}")
                
                return True
            else:
                self.logger.warning("Terms checkbox not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to set terms acceptance: {str(e)}")
            return False
    
    def select_gender(self, gender: str) -> bool:
        """
        성별 선택
        
        Args:
            gender: 'male' 또는 'female'
            
        Returns:
            선택 성공 여부
        """
        try:
            gender_locator = self.GENDER_MALE if gender.lower() == 'male' else self.GENDER_FEMALE
            
            if self.is_element_present(gender_locator, timeout=2):
                self.click_element(gender_locator)
                self.logger.debug(f"Gender selected: {gender}")
                return True
            else:
                self.logger.warning(f"Gender option '{gender}' not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to select gender: {str(e)}")
            return False
    
    def upload_file(self, file_path: str) -> bool:
        """
        파일 업로드
        
        Args:
            file_path: 업로드할 파일 경로
            
        Returns:
            업로드 성공 여부
        """
        try:
            if self.is_element_present(self.FILE_UPLOAD, timeout=2):
                file_input = self.find_element(self.FILE_UPLOAD)
                file_input.send_keys(file_path)
                self.logger.debug(f"File uploaded: {file_path}")
                return True
            else:
                self.logger.warning("File upload field not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to upload file: {str(e)}")
            return False
    
    # ==================== 폼 제출 ====================
    
    def submit_form(self) -> bool:
        """
        폼 제출
        
        Returns:
            제출 성공 여부
        """
        self.logger.debug("Submitting form")
        
        try:
            submit_button = self._find_submit_button()
            self.click_element(submit_button)
            
            # 제출 처리 대기
            self.wait(2)
            
            # 성공 메시지 확인
            if self.is_element_present(self.SUCCESS_MESSAGE, timeout=5):
                self.logger.debug("Form submitted successfully")
                return True
            elif self.is_element_present(self.ERROR_MESSAGE, timeout=2):
                error_msg = self.get_text(self.ERROR_MESSAGE)
                self.logger.warning(f"Form submission failed: {error_msg}")
                return False
            else:
                # URL 변경으로 성공 확인
                current_url = self.get_current_url()
                if "success" in current_url or "thank" in current_url:
                    self.logger.debug("Form submitted successfully (URL changed)")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to submit form: {str(e)}")
            return False
    
    def _find_submit_button(self) -> tuple:
        """제출 버튼 찾기"""
        if self.is_element_present(self.SUBMIT_BUTTON, timeout=2):
            return self.SUBMIT_BUTTON
        
        for locator in self.ALT_SUBMIT_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found submit button with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("submit button", timeout=self.default_timeout)
    
    def reset_form(self) -> bool:
        """
        폼 리셋
        
        Returns:
            리셋 성공 여부
        """
        try:
            if self.is_element_present(self.RESET_BUTTON, timeout=2):
                self.click_element(self.RESET_BUTTON)
                self.logger.debug("Form reset successfully")
                return True
            else:
                self.logger.warning("Reset button not found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to reset form: {str(e)}")
            return False
    
    # ==================== 유효성 검사 ====================
    
    def get_validation_errors(self) -> List[str]:
        """
        유효성 검사 오류 메시지 가져오기
        
        Returns:
            오류 메시지 리스트
        """
        errors = []
        
        try:
            if self.is_element_present(self.VALIDATION_ERROR, timeout=2):
                error_elements = self.find_elements(self.VALIDATION_ERROR)
                for element in error_elements:
                    error_text = element.text.strip()
                    if error_text:
                        errors.append(error_text)
            
            self.logger.debug(f"Found {len(errors)} validation errors")
            return errors
            
        except Exception as e:
            self.logger.error(f"Failed to get validation errors: {str(e)}")
            return errors
    
    def is_form_valid(self) -> bool:
        """
        폼 유효성 확인
        
        Returns:
            폼이 유효하면 True
        """
        try:
            errors = self.get_validation_errors()
            return len(errors) == 0
        except Exception as e:
            self.logger.error(f"Failed to check form validity: {str(e)}")
            return False
    
    # ==================== 폼 상태 확인 ====================
    
    def get_form_data(self) -> Dict[str, Any]:
        """
        현재 폼에 입력된 데이터 가져오기
        
        Returns:
            폼 데이터 딕셔너리
        """
        form_data = {}
        
        try:
            # 텍스트 필드들
            text_fields = {
                'first_name': self.FIRST_NAME,
                'last_name': self.LAST_NAME,
                'email': self.EMAIL,
                'phone': self.PHONE,
                'message': self.MESSAGE
            }
            
            for field_name, locator in text_fields.items():
                if self.is_element_present(locator, timeout=1):
                    element = self.find_element(locator)
                    form_data[field_name] = element.get_attribute('value') or ''
            
            # 드롭다운들
            if self.is_element_present(self.COUNTRY_SELECT, timeout=1):
                select_element = Select(self.find_element(self.COUNTRY_SELECT))
                form_data['country'] = select_element.first_selected_option.text
            
            # 체크박스들
            if self.is_element_present(self.NEWSLETTER_CHECKBOX, timeout=1):
                checkbox = self.find_element(self.NEWSLETTER_CHECKBOX)
                form_data['newsletter'] = checkbox.is_selected()
            
            if self.is_element_present(self.TERMS_CHECKBOX, timeout=1):
                checkbox = self.find_element(self.TERMS_CHECKBOX)
                form_data['terms'] = checkbox.is_selected()
            
            # 라디오 버튼들
            if self.is_element_present(self.GENDER_MALE, timeout=1):
                male_radio = self.find_element(self.GENDER_MALE)
                if male_radio.is_selected():
                    form_data['gender'] = 'male'
            
            if self.is_element_present(self.GENDER_FEMALE, timeout=1):
                female_radio = self.find_element(self.GENDER_FEMALE)
                if female_radio.is_selected():
                    form_data['gender'] = 'female'
            
            self.logger.debug(f"Retrieved form data: {form_data}")
            return form_data
            
        except Exception as e:
            self.logger.error(f"Failed to get form data: {str(e)}")
            return form_data
    
    def is_form_submitted(self) -> bool:
        """
        폼 제출 완료 여부 확인
        
        Returns:
            제출 완료되면 True
        """
        try:
            # 성공 메시지 확인
            if self.is_element_present(self.SUCCESS_MESSAGE, timeout=2):
                return True
            
            # URL 변경 확인
            current_url = self.get_current_url()
            success_indicators = ["success", "thank", "confirmation", "complete"]
            
            for indicator in success_indicators:
                if indicator in current_url.lower():
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check form submission status: {str(e)}")
            return False