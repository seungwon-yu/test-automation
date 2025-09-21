"""
FormPage 클래스 - 폼 페이지 Page Object

이 모듈은 다양한 폼 페이지의 UI 요소와 동작을 캡슐화합니다.
텍스트 입력, 드롭다운 선택, 체크박스/라디오 버튼, 파일 업로드 등의 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any, Tuple
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
    결제 페이지 Page Object 클래스
    
    결제 기능의 모든 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 결제 페이지 컨테이너
    PAYMENT_CONTAINER = (By.CSS_SELECTOR, ".payment-container")
    CHECKOUT_FORM = (By.CSS_SELECTOR, ".checkout-form")
    
    # 대체 결제 컨테이너 로케이터들
    ALT_PAYMENT_CONTAINER_LOCATORS = [
        (By.CSS_SELECTOR, ".checkout-container"),
        (By.CSS_SELECTOR, ".payment-form"),
        (By.CSS_SELECTOR, ".billing-container"),
        (By.CSS_SELECTOR, "[data-testid='payment']"),
        (By.XPATH, "//*[contains(@class, 'payment')]"),
        (By.XPATH, "//*[contains(@class, 'checkout')]")
    ]
    
    # 배송 정보 섹션
    SHIPPING_SECTION = (By.CSS_SELECTOR, ".shipping-section")
    SHIPPING_FIRST_NAME = (By.ID, "shipping-first-name")
    SHIPPING_LAST_NAME = (By.ID, "shipping-last-name")
    SHIPPING_ADDRESS = (By.ID, "shipping-address")
    SHIPPING_CITY = (By.ID, "shipping-city")
    SHIPPING_STATE = (By.ID, "shipping-state")
    SHIPPING_ZIP = (By.ID, "shipping-zip")
    SHIPPING_COUNTRY = (By.ID, "shipping-country")
    SHIPPING_PHONE = (By.ID, "shipping-phone")
    
    # 대체 배송 정보 로케이터들
    ALT_SHIPPING_LOCATORS = {
        'first_name': [
            (By.NAME, "firstName"),
            (By.NAME, "first_name"),
            (By.CSS_SELECTOR, "input[placeholder*='First Name' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'First')]")
        ],
        'last_name': [
            (By.NAME, "lastName"),
            (By.NAME, "last_name"),
            (By.CSS_SELECTOR, "input[placeholder*='Last Name' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'Last')]")
        ],
        'address': [
            (By.NAME, "address"),
            (By.NAME, "street"),
            (By.CSS_SELECTOR, "input[placeholder*='Address' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'Address')]")
        ],
        'city': [
            (By.NAME, "city"),
            (By.CSS_SELECTOR, "input[placeholder*='City' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'City')]")
        ],
        'zip': [
            (By.NAME, "zip"),
            (By.NAME, "zipCode"),
            (By.NAME, "postal_code"),
            (By.CSS_SELECTOR, "input[placeholder*='Zip' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'Zip')]")
        ]
    }
    
    # 청구 정보 섹션
    BILLING_SECTION = (By.CSS_SELECTOR, ".billing-section")
    BILLING_SAME_AS_SHIPPING = (By.ID, "billing-same-as-shipping")
    BILLING_FIRST_NAME = (By.ID, "billing-first-name")
    BILLING_LAST_NAME = (By.ID, "billing-last-name")
    BILLING_ADDRESS = (By.ID, "billing-address")
    BILLING_CITY = (By.ID, "billing-city")
    BILLING_STATE = (By.ID, "billing-state")
    BILLING_ZIP = (By.ID, "billing-zip")
    BILLING_COUNTRY = (By.ID, "billing-country")
    
    # 결제 방법 섹션
    PAYMENT_METHOD_SECTION = (By.CSS_SELECTOR, ".payment-method-section")
    CREDIT_CARD_OPTION = (By.CSS_SELECTOR, "input[value='credit_card']")
    PAYPAL_OPTION = (By.CSS_SELECTOR, "input[value='paypal']")
    BANK_TRANSFER_OPTION = (By.CSS_SELECTOR, "input[value='bank_transfer']")
    
    # 대체 결제 방법 로케이터들
    ALT_PAYMENT_METHOD_LOCATORS = {
        'credit_card': [
            (By.XPATH, "//input[@type='radio' and @value='card']"),
            (By.XPATH, "//input[@type='radio' and contains(@id, 'credit')]"),
            (By.XPATH, "//label[contains(text(), 'Credit Card')]/../input")
        ],
        'paypal': [
            (By.XPATH, "//input[@type='radio' and @value='paypal']"),
            (By.XPATH, "//input[@type='radio' and contains(@id, 'paypal')]"),
            (By.XPATH, "//label[contains(text(), 'PayPal')]/../input")
        ]
    }
    
    # 신용카드 정보 섹션
    CARD_SECTION = (By.CSS_SELECTOR, ".card-section")
    CARD_NUMBER = (By.ID, "card-number")
    CARD_HOLDER_NAME = (By.ID, "card-holder-name")
    EXPIRY_MONTH = (By.ID, "expiry-month")
    EXPIRY_YEAR = (By.ID, "expiry-year")
    CVV = (By.ID, "cvv")
    
    # 대체 신용카드 로케이터들
    ALT_CARD_LOCATORS = {
        'number': [
            (By.NAME, "cardNumber"),
            (By.NAME, "card_number"),
            (By.CSS_SELECTOR, "input[placeholder*='Card Number' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'Card')]")
        ],
        'holder': [
            (By.NAME, "cardHolder"),
            (By.NAME, "card_holder"),
            (By.NAME, "cardholder_name"),
            (By.CSS_SELECTOR, "input[placeholder*='Cardholder' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'Name on Card')]")
        ],
        'cvv': [
            (By.NAME, "cvv"),
            (By.NAME, "cvc"),
            (By.NAME, "security_code"),
            (By.CSS_SELECTOR, "input[placeholder*='CVV' i]"),
            (By.XPATH, "//input[contains(@placeholder, 'CVV')]")
        ]
    }
    
    # 주문 요약 섹션
    ORDER_SUMMARY_SECTION = (By.CSS_SELECTOR, ".order-summary")
    ORDER_ITEMS = (By.CSS_SELECTOR, ".order-item")
    ORDER_SUBTOTAL = (By.CSS_SELECTOR, ".order-subtotal")
    ORDER_TAX = (By.CSS_SELECTOR, ".order-tax")
    ORDER_SHIPPING = (By.CSS_SELECTOR, ".order-shipping")
    ORDER_TOTAL = (By.CSS_SELECTOR, ".order-total")
    
    # 쿠폰 및 할인 섹션
    PROMO_CODE_INPUT = (By.CSS_SELECTOR, ".promo-code-input")
    APPLY_PROMO_BUTTON = (By.CSS_SELECTOR, ".apply-promo")
    DISCOUNT_AMOUNT = (By.CSS_SELECTOR, ".discount-amount")
    
    # 결제 버튼 및 액션
    PLACE_ORDER_BUTTON = (By.CSS_SELECTOR, ".place-order-button")
    COMPLETE_PAYMENT_BUTTON = (By.CSS_SELECTOR, ".complete-payment")
    BACK_TO_CART_BUTTON = (By.CSS_SELECTOR, ".back-to-cart")
    
    # 대체 결제 버튼 로케이터들
    ALT_PLACE_ORDER_LOCATORS = [
        (By.CSS_SELECTOR, ".checkout-button"),
        (By.CSS_SELECTOR, ".pay-now"),
        (By.CSS_SELECTOR, ".submit-order"),
        (By.CSS_SELECTOR, "[data-testid='place-order']"),
        (By.XPATH, "//button[contains(text(), 'Place Order')]"),
        (By.XPATH, "//button[contains(text(), '주문하기')]"),
        (By.XPATH, "//button[contains(text(), 'Pay Now')]"),
        (By.XPATH, "//input[@type='submit' and @value='Place Order']")
    ]
    
    # 상태 및 메시지 요소들
    LOADING_INDICATOR = (By.CSS_SELECTOR, ".loading")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message")
    VALIDATION_ERROR = (By.CSS_SELECTOR, ".validation-error")
    
    # 결제 완료 페이지 요소들
    ORDER_CONFIRMATION = (By.CSS_SELECTOR, ".order-confirmation")
    ORDER_NUMBER = (By.CSS_SELECTOR, ".order-number")
    CONFIRMATION_MESSAGE = (By.CSS_SELECTOR, ".confirmation-message")
    
    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        PaymentPage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 결제 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        
        # 결제 페이지 특화 설정
        self.payment_timeout = 30  # 결제 처리 대기 시간
        self.validation_timeout = 5  # 유효성 검사 대기 시간
        
        self.logger.debug("PaymentPage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_payment(self, payment_url: str = None) -> None:
        """
        결제 페이지로 이동
        
        Args:
            payment_url: 결제 페이지 URL (None이면 기본 URL 사용)
        """
        url = payment_url or f"{self.base_url}/checkout"
        self.logger.info(f"Navigating to payment page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_payment_page_load()
            self.logger.info("Successfully navigated to payment page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to payment page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_payment_page_load(self) -> None:
        """결제 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for payment page to load")
        
        try:
            # 기본 페이지 로딩 대기
            self.wait_for_page_load()
            
            # 결제 컨테이너가 로드될 때까지 대기
            self._find_payment_container()
            
            self.logger.debug("Payment page loaded successfully")
            
        except ElementNotFoundException as e:
            self.logger.error(f"Payment page elements not found: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Payment page load failed: {str(e)}")
            raise PageLoadTimeoutException("payment page", self.default_timeout)
    
    # ==================== 요소 찾기 (Smart Locator) ====================
    
    def _find_payment_container(self) -> tuple:
        """결제 컨테이너 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.PAYMENT_CONTAINER, timeout=2):
            return self.PAYMENT_CONTAINER
        
        # 대체 로케이터들 시도
        for locator in self.ALT_PAYMENT_CONTAINER_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found payment container with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("payment container", timeout=self.default_timeout)
    
    def _find_field_with_alternatives(self, field_name: str, default_locator: tuple, alt_locators: List[tuple]) -> tuple:
        """대체 로케이터를 사용하여 필드 찾기"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(default_locator, timeout=2):
            return default_locator
        
        # 대체 로케이터들 시도
        for locator in alt_locators:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found {field_name} field with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException(f"{field_name} field", timeout=self.default_timeout)
    
    def _find_place_order_button(self) -> tuple:
        """주문하기 버튼 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.PLACE_ORDER_BUTTON, timeout=2):
            return self.PLACE_ORDER_BUTTON
        
        # 대체 로케이터들 시도
        for locator in self.ALT_PLACE_ORDER_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found place order button with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("place order button", timeout=self.default_timeout)
    
    # ==================== 배송 정보 입력 ====================
    
    def fill_shipping_info(self, shipping_info: Dict[str, str]) -> bool:
        """
        배송 정보 입력
        
        Args:
            shipping_info: 배송 정보 딕셔너리
                {
                    'first_name': '홍',
                    'last_name': '길동',
                    'address': '서울시 강남구',
                    'city': '서울',
                    'state': '서울특별시',
                    'zip': '12345',
                    'country': '대한민국',
                    'phone': '010-1234-5678'
                }
                
        Returns:
            입력 성공 여부
        """
        self.logger.debug("Filling shipping information")
        
        try:
            # 배송 정보 섹션이 있는지 확인
            if not self.is_element_present(self.SHIPPING_SECTION, timeout=2):
                self.logger.warning("Shipping section not found")
                return False
            
            # 각 필드 입력
            field_mappings = {
                'first_name': (self.SHIPPING_FIRST_NAME, self.ALT_SHIPPING_LOCATORS['first_name']),
                'last_name': (self.SHIPPING_LAST_NAME, self.ALT_SHIPPING_LOCATORS['last_name']),
                'address': (self.SHIPPING_ADDRESS, self.ALT_SHIPPING_LOCATORS['address']),
                'city': (self.SHIPPING_CITY, self.ALT_SHIPPING_LOCATORS['city']),
                'zip': (self.SHIPPING_ZIP, self.ALT_SHIPPING_LOCATORS['zip'])
            }
            
            for field_name, (default_locator, alt_locators) in field_mappings.items():
                if field_name in shipping_info and shipping_info[field_name]:
                    try:
                        field_locator = self._find_field_with_alternatives(
                            field_name, default_locator, alt_locators
                        )
                        self.input_text(field_locator, shipping_info[field_name], clear_first=True)
                        self.logger.debug(f"Filled {field_name}: {shipping_info[field_name]}")
                    except ElementNotFoundException:
                        self.logger.warning(f"Could not find {field_name} field")
                        continue
            
            # 주/도 선택 (드롭다운인 경우)
            if 'state' in shipping_info and shipping_info['state']:
                try:
                    if self.is_element_present(self.SHIPPING_STATE, timeout=2):
                        state_element = self.find_element(self.SHIPPING_STATE)
                        if state_element.tag_name == 'select':
                            self.select_dropdown_by_text(self.SHIPPING_STATE, shipping_info['state'])
                        else:
                            self.input_text(self.SHIPPING_STATE, shipping_info['state'])
                except:
                    self.logger.warning("Could not fill state field")
            
            # 국가 선택 (드롭다운인 경우)
            if 'country' in shipping_info and shipping_info['country']:
                try:
                    if self.is_element_present(self.SHIPPING_COUNTRY, timeout=2):
                        country_element = self.find_element(self.SHIPPING_COUNTRY)
                        if country_element.tag_name == 'select':
                            self.select_dropdown_by_text(self.SHIPPING_COUNTRY, shipping_info['country'])
                        else:
                            self.input_text(self.SHIPPING_COUNTRY, shipping_info['country'])
                except:
                    self.logger.warning("Could not fill country field")
            
            # 전화번호 입력
            if 'phone' in shipping_info and shipping_info['phone']:
                try:
                    if self.is_element_present(self.SHIPPING_PHONE, timeout=2):
                        self.input_text(self.SHIPPING_PHONE, shipping_info['phone'])
                except:
                    self.logger.warning("Could not fill phone field")
            
            self.logger.debug("Shipping information filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill shipping information: {str(e)}")
            return False
    
    # ==================== 청구 정보 입력 ====================
    
    def set_billing_same_as_shipping(self, same_as_shipping: bool = True) -> bool:
        """
        청구지 주소를 배송지와 동일하게 설정
        
        Args:
            same_as_shipping: 배송지와 동일 여부
            
        Returns:
            설정 성공 여부
        """
        self.logger.debug(f"Setting billing same as shipping: {same_as_shipping}")
        
        try:
            if self.is_element_present(self.BILLING_SAME_AS_SHIPPING, timeout=2):
                checkbox = self.find_element(self.BILLING_SAME_AS_SHIPPING)
                is_checked = checkbox.is_selected()
                
                if (same_as_shipping and not is_checked) or (not same_as_shipping and is_checked):
                    self.click_element(self.BILLING_SAME_AS_SHIPPING)
                    self.logger.debug("Billing same as shipping checkbox toggled")
                
                return True
            else:
                self.logger.warning("Billing same as shipping checkbox not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set billing same as shipping: {str(e)}")
            return False
    
    def fill_billing_info(self, billing_info: Dict[str, str]) -> bool:
        """
        청구 정보 입력
        
        Args:
            billing_info: 청구 정보 딕셔너리 (배송 정보와 동일한 형식)
            
        Returns:
            입력 성공 여부
        """
        self.logger.debug("Filling billing information")
        
        try:
            # 청구 정보 섹션이 있는지 확인
            if not self.is_element_present(self.BILLING_SECTION, timeout=2):
                self.logger.warning("Billing section not found")
                return False
            
            # 각 필드 입력 (배송 정보와 유사하지만 billing 접두사 사용)
            field_mappings = {
                'first_name': self.BILLING_FIRST_NAME,
                'last_name': self.BILLING_LAST_NAME,
                'address': self.BILLING_ADDRESS,
                'city': self.BILLING_CITY,
                'zip': self.BILLING_ZIP
            }
            
            for field_name, locator in field_mappings.items():
                if field_name in billing_info and billing_info[field_name]:
                    try:
                        if self.is_element_present(locator, timeout=2):
                            self.input_text(locator, billing_info[field_name], clear_first=True)
                            self.logger.debug(f"Filled billing {field_name}: {billing_info[field_name]}")
                    except:
                        self.logger.warning(f"Could not find billing {field_name} field")
                        continue
            
            # 주/도 및 국가 선택
            if 'state' in billing_info and billing_info['state']:
                try:
                    if self.is_element_present(self.BILLING_STATE, timeout=2):
                        state_element = self.find_element(self.BILLING_STATE)
                        if state_element.tag_name == 'select':
                            self.select_dropdown_by_text(self.BILLING_STATE, billing_info['state'])
                        else:
                            self.input_text(self.BILLING_STATE, billing_info['state'])
                except:
                    self.logger.warning("Could not fill billing state field")
            
            if 'country' in billing_info and billing_info['country']:
                try:
                    if self.is_element_present(self.BILLING_COUNTRY, timeout=2):
                        country_element = self.find_element(self.BILLING_COUNTRY)
                        if country_element.tag_name == 'select':
                            self.select_dropdown_by_text(self.BILLING_COUNTRY, billing_info['country'])
                        else:
                            self.input_text(self.BILLING_COUNTRY, billing_info['country'])
                except:
                    self.logger.warning("Could not fill billing country field")
            
            self.logger.debug("Billing information filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill billing information: {str(e)}")
            return False
    
    # ==================== 결제 방법 선택 ====================
    
    def select_payment_method(self, method: str) -> bool:
        """
        결제 방법 선택
        
        Args:
            method: 결제 방법 ('credit_card', 'paypal', 'bank_transfer')
            
        Returns:
            선택 성공 여부
        """
        self.logger.debug(f"Selecting payment method: {method}")
        
        try:
            # 결제 방법 섹션 확인
            if not self.is_element_present(self.PAYMENT_METHOD_SECTION, timeout=2):
                self.logger.warning("Payment method section not found")
                return False
            
            # 결제 방법별 로케이터 매핑
            method_locators = {
                'credit_card': self.CREDIT_CARD_OPTION,
                'paypal': self.PAYPAL_OPTION,
                'bank_transfer': self.BANK_TRANSFER_OPTION
            }
            
            if method in method_locators:
                # 기본 로케이터 시도
                if self.is_element_present(method_locators[method], timeout=2):
                    self.click_element(method_locators[method])
                    self.logger.debug(f"Selected payment method: {method}")
                    return True
                
                # 대체 로케이터 시도
                if method in self.ALT_PAYMENT_METHOD_LOCATORS:
                    for alt_locator in self.ALT_PAYMENT_METHOD_LOCATORS[method]:
                        if self.is_element_present(alt_locator, timeout=1):
                            self.click_element(alt_locator)
                            self.logger.debug(f"Selected payment method {method} with alternative locator")
                            return True
            
            self.logger.warning(f"Payment method '{method}' not found or not supported")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to select payment method: {str(e)}")
            return False
    
    # ==================== 신용카드 정보 입력 ====================
    
    def fill_credit_card_info(self, card_info: Dict[str, str]) -> bool:
        """
        신용카드 정보 입력
        
        Args:
            card_info: 신용카드 정보 딕셔너리
                {
                    'number': '1234567890123456',
                    'holder_name': '홍길동',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cvv': '123'
                }
                
        Returns:
            입력 성공 여부
        """
        self.logger.debug("Filling credit card information")
        
        try:
            # 신용카드 섹션이 보이는지 확인
            if not self.is_element_present(self.CARD_SECTION, timeout=2):
                self.logger.warning("Credit card section not found")
                return False
            
            # 카드 번호 입력
            if 'number' in card_info and card_info['number']:
                try:
                    card_number_locator = self._find_field_with_alternatives(
                        'card_number', self.CARD_NUMBER, self.ALT_CARD_LOCATORS['number']
                    )
                    self.input_text(card_number_locator, card_info['number'], clear_first=True)
                    self.logger.debug("Card number entered")
                except ElementNotFoundException:
                    self.logger.warning("Card number field not found")
            
            # 카드 소유자명 입력
            if 'holder_name' in card_info and card_info['holder_name']:
                try:
                    holder_name_locator = self._find_field_with_alternatives(
                        'card_holder', self.CARD_HOLDER_NAME, self.ALT_CARD_LOCATORS['holder']
                    )
                    self.input_text(holder_name_locator, card_info['holder_name'], clear_first=True)
                    self.logger.debug("Card holder name entered")
                except ElementNotFoundException:
                    self.logger.warning("Card holder name field not found")
            
            # 만료 월 선택
            if 'expiry_month' in card_info and card_info['expiry_month']:
                try:
                    if self.is_element_present(self.EXPIRY_MONTH, timeout=2):
                        month_element = self.find_element(self.EXPIRY_MONTH)
                        if month_element.tag_name == 'select':
                            self.select_dropdown_by_value(self.EXPIRY_MONTH, card_info['expiry_month'])
                        else:
                            self.input_text(self.EXPIRY_MONTH, card_info['expiry_month'])
                        self.logger.debug("Expiry month selected")
                except:
                    self.logger.warning("Expiry month field not found")
            
            # 만료 년도 선택
            if 'expiry_year' in card_info and card_info['expiry_year']:
                try:
                    if self.is_element_present(self.EXPIRY_YEAR, timeout=2):
                        year_element = self.find_element(self.EXPIRY_YEAR)
                        if year_element.tag_name == 'select':
                            self.select_dropdown_by_value(self.EXPIRY_YEAR, card_info['expiry_year'])
                        else:
                            self.input_text(self.EXPIRY_YEAR, card_info['expiry_year'])
                        self.logger.debug("Expiry year selected")
                except:
                    self.logger.warning("Expiry year field not found")
            
            # CVV 입력
            if 'cvv' in card_info and card_info['cvv']:
                try:
                    cvv_locator = self._find_field_with_alternatives(
                        'cvv', self.CVV, self.ALT_CARD_LOCATORS['cvv']
                    )
                    self.input_text(cvv_locator, card_info['cvv'], clear_first=True)
                    self.logger.debug("CVV entered")
                except ElementNotFoundException:
                    self.logger.warning("CVV field not found")
            
            self.logger.debug("Credit card information filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill credit card information: {str(e)}")
            return False
    
    # ==================== 프로모션 코드 ====================
    
    def apply_promo_code(self, promo_code: str) -> bool:
        """
        프로모션 코드 적용
        
        Args:
            promo_code: 프로모션 코드
            
        Returns:
            적용 성공 여부
        """
        self.logger.debug(f"Applying promo code: {promo_code}")
        
        try:
            if not self.is_element_present(self.PROMO_CODE_INPUT, timeout=2):
                self.logger.warning("Promo code input not available")
                return False
            
            # 프로모션 코드 입력
            self.input_text(self.PROMO_CODE_INPUT, promo_code, clear_first=True)
            
            # 적용 버튼 클릭
            if self.is_element_present(self.APPLY_PROMO_BUTTON, timeout=2):
                self.click_element(self.APPLY_PROMO_BUTTON)
            else:
                # Enter 키로 적용
                from selenium.webdriver.common.keys import Keys
                self.send_keys(self.PROMO_CODE_INPUT, Keys.RETURN)
            
            # 적용 결과 대기
            self._wait_for_payment_update()
            
            # 할인 금액이 표시되면 성공으로 간주
            if self.is_element_present(self.DISCOUNT_AMOUNT, timeout=3):
                discount = self.get_text(self.DISCOUNT_AMOUNT)
                if discount and discount != "$0.00":
                    self.logger.debug(f"Promo code applied, discount: {discount}")
                    return True
            
            # 에러 메시지 확인
            if self.is_element_present(self.ERROR_MESSAGE, timeout=2):
                error_msg = self.get_text(self.ERROR_MESSAGE)
                self.logger.warning(f"Promo code application failed: {error_msg}")
                return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to apply promo code: {str(e)}")
            return False
    
    # ==================== 주문 요약 정보 ====================
    
    def get_order_summary(self) -> Dict[str, Any]:
        """
        주문 요약 정보 가져오기
        
        Returns:
            주문 요약 정보 딕셔너리
        """
        summary = {
            'items': [],
            'subtotal': '',
            'tax': '',
            'shipping': '',
            'discount': '',
            'total': ''
        }
        
        try:
            # 주문 아이템들 가져오기
            if self.is_element_present(self.ORDER_ITEMS, timeout=2):
                item_elements = self.find_elements(self.ORDER_ITEMS)
                for item_element in item_elements:
                    item_info = {
                        'name': '',
                        'quantity': '',
                        'price': ''
                    }
                    
                    # 아이템 정보 추출 (구체적인 로케이터는 사이트마다 다를 수 있음)
                    try:
                        item_info['name'] = item_element.find_element(By.CSS_SELECTOR, ".item-name").text.strip()
                    except:
                        pass
                    
                    try:
                        item_info['quantity'] = item_element.find_element(By.CSS_SELECTOR, ".item-quantity").text.strip()
                    except:
                        pass
                    
                    try:
                        item_info['price'] = item_element.find_element(By.CSS_SELECTOR, ".item-price").text.strip()
                    except:
                        pass
                    
                    summary['items'].append(item_info)
            
            # 금액 정보 가져오기
            if self.is_element_present(self.ORDER_SUBTOTAL, timeout=2):
                summary['subtotal'] = self.get_text(self.ORDER_SUBTOTAL).strip()
            
            if self.is_element_present(self.ORDER_TAX, timeout=2):
                summary['tax'] = self.get_text(self.ORDER_TAX).strip()
            
            if self.is_element_present(self.ORDER_SHIPPING, timeout=2):
                summary['shipping'] = self.get_text(self.ORDER_SHIPPING).strip()
            
            if self.is_element_present(self.DISCOUNT_AMOUNT, timeout=2):
                summary['discount'] = self.get_text(self.DISCOUNT_AMOUNT).strip()
            
            if self.is_element_present(self.ORDER_TOTAL, timeout=2):
                summary['total'] = self.get_text(self.ORDER_TOTAL).strip()
            
            self.logger.debug(f"Order summary: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting order summary: {str(e)}")
            return summary
    
    # ==================== 결제 완료 ====================
    
    def place_order(self) -> bool:
        """
        주문하기 (결제 완료)
        
        Returns:
            주문 성공 여부
        """
        self.logger.debug("Placing order")
        
        try:
            # 주문하기 버튼 찾기 및 클릭
            place_order_button_locator = self._find_place_order_button()
            self.click_element(place_order_button_locator)
            
            # 결제 처리 대기
            self._wait_for_payment_processing()
            
            # 결제 완료 확인
            if self.is_payment_successful():
                self.logger.info("Order placed successfully")
                return True
            else:
                # 에러 메시지 확인
                if self.is_element_present(self.ERROR_MESSAGE, timeout=3):
                    error_msg = self.get_text(self.ERROR_MESSAGE)
                    self.logger.error(f"Order placement failed: {error_msg}")
                else:
                    self.logger.error("Order placement failed: Unknown error")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to place order: {str(e)}")
            return False
    
    def is_payment_successful(self) -> bool:
        """
        결제 성공 여부 확인
        
        Returns:
            결제 성공 여부
        """
        try:
            # URL 변경 확인 (주문 완료 페이지로 이동했는지)
            current_url = self.get_current_url()
            if any(keyword in current_url.lower() for keyword in ['confirmation', 'success', 'complete', 'thank-you']):
                return True
            
            # 주문 확인 메시지 확인
            if self.is_element_present(self.ORDER_CONFIRMATION, timeout=5):
                return True
            
            if self.is_element_present(self.CONFIRMATION_MESSAGE, timeout=5):
                return True
            
            # 주문 번호 표시 확인
            if self.is_element_present(self.ORDER_NUMBER, timeout=5):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking payment success: {str(e)}")
            return False
    
    def get_order_number(self) -> str:
        """
        주문 번호 가져오기
        
        Returns:
            주문 번호 (없으면 빈 문자열)
        """
        try:
            if self.is_element_present(self.ORDER_NUMBER, timeout=2):
                order_number_text = self.get_text(self.ORDER_NUMBER)
                # 주문 번호만 추출 (예: "Order #12345" -> "12345")
                import re
                numbers = re.findall(r'[A-Z0-9]+', order_number_text.upper())
                if numbers:
                    return numbers[-1]  # 마지막 숫자/문자 조합을 주문 번호로 간주
                return order_number_text.strip()
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Error getting order number: {str(e)}")
            return ""
    
    # ==================== 유틸리티 메서드 ====================
    
    def _wait_for_payment_update(self) -> None:
        """결제 정보 업데이트 완료 대기"""
        # 로딩 인디케이터가 있으면 사라질 때까지 대기
        if self.is_element_present(self.LOADING_INDICATOR, timeout=2):
            self.logger.debug("Waiting for payment update to complete")
            self.wait_for_element_invisible(self.LOADING_INDICATOR, timeout=self.validation_timeout)
        
        # 짧은 대기 (JavaScript 처리 시간)
        self.wait(1)
    
    def _wait_for_payment_processing(self) -> None:
        """결제 처리 완료 대기"""
        self.logger.debug("Waiting for payment processing")
        
        # 로딩 인디케이터가 있으면 사라질 때까지 대기
        if self.is_element_present(self.LOADING_INDICATOR, timeout=2):
            self.wait_for_element_invisible(self.LOADING_INDICATOR, timeout=self.payment_timeout)
        
        # 결제 처리 시간 대기
        self.wait(3)
    
    def validate_form_fields(self) -> Dict[str, bool]:
        """
        폼 필드 유효성 검사 결과 확인
        
        Returns:
            필드별 유효성 검사 결과
        """
        validation_results = {}
        
        try:
            # 유효성 검사 에러 메시지들 확인
            if self.is_element_present(self.VALIDATION_ERROR, timeout=2):
                error_elements = self.find_elements(self.VALIDATION_ERROR)
                
                for error_element in error_elements:
                    error_text = error_element.text.strip()
                    # 에러 메시지에서 필드명 추출 (간단한 예시)
                    if 'name' in error_text.lower():
                        validation_results['name'] = False
                    elif 'address' in error_text.lower():
                        validation_results['address'] = False
                    elif 'card' in error_text.lower():
                        validation_results['card'] = False
                    elif 'email' in error_text.lower():
                        validation_results['email'] = False
            
            self.logger.debug(f"Form validation results: {validation_results}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating form fields: {str(e)}")
            return validation_results
    
    def back_to_cart(self) -> bool:
        """
        장바구니로 돌아가기
        
        Returns:
            이동 성공 여부
        """
        self.logger.debug("Going back to cart")
        
        try:
            if self.is_element_present(self.BACK_TO_CART_BUTTON, timeout=2):
                self.click_element(self.BACK_TO_CART_BUTTON)
                self.wait(2)  # 페이지 전환 대기
                
                # URL 확인
                current_url = self.get_current_url()
                if 'cart' in current_url.lower():
                    self.logger.debug("Successfully returned to cart")
                    return True
                else:
                    return False
            else:
                self.logger.warning("Back to cart button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to go back to cart: {str(e)}")
            return False
    
    def take_payment_screenshot(self, filename: str = None) -> str:
        """
        결제 페이지 스크린샷 촬영
        
        Args:
            filename: 파일명
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"payment_page_{timestamp}.png"
        
        return self.take_screenshot(filename)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"PaymentPage(url={self.get_current_url()})"