"""
CartPage 클래스 - 장바구니 페이지 Page Object

이 모듈은 장바구니 페이지의 UI 요소와 동작을 캡슐화합니다.
상품 추가/제거, 수량 변경, 총액 계산 등의 기능을 제공합니다.
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


class CartPage(BasePage):
    """
    장바구니 페이지 Page Object 클래스
    
    장바구니 기능의 모든 요소와 동작을 캡슐화하여
    테스트 코드에서 쉽게 사용할 수 있도록 합니다.
    """
    
    # ==================== 페이지 요소 로케이터 ====================
    
    # 장바구니 컨테이너 및 기본 요소들
    CART_CONTAINER = (By.CSS_SELECTOR, ".cart-container")
    CART_ITEMS_LIST = (By.CSS_SELECTOR, ".cart-items")
    CART_ITEM = (By.CSS_SELECTOR, ".cart-item")
    EMPTY_CART_MESSAGE = (By.CSS_SELECTOR, ".empty-cart")
    
    # 대체 장바구니 컨테이너 로케이터들
    ALT_CART_CONTAINER_LOCATORS = [
        (By.CSS_SELECTOR, ".shopping-cart"),
        (By.CSS_SELECTOR, ".basket"),
        (By.CSS_SELECTOR, ".cart"),
        (By.CSS_SELECTOR, "[data-testid='cart']"),
        (By.XPATH, "//*[contains(@class, 'cart')]"),
        (By.XPATH, "//*[contains(@class, 'basket')]")
    ]
    
    ALT_CART_ITEM_LOCATORS = [
        (By.CSS_SELECTOR, ".cart-product"),
        (By.CSS_SELECTOR, ".basket-item"),
        (By.CSS_SELECTOR, ".shopping-item"),
        (By.CSS_SELECTOR, "[data-testid='cart-item']"),
        (By.XPATH, "//*[contains(@class, 'item')]")
    ]
    
    # 개별 상품 요소들
    ITEM_NAME = (By.CSS_SELECTOR, ".item-name")
    ITEM_PRICE = (By.CSS_SELECTOR, ".item-price")
    ITEM_QUANTITY = (By.CSS_SELECTOR, ".item-quantity")
    ITEM_TOTAL = (By.CSS_SELECTOR, ".item-total")
    ITEM_IMAGE = (By.CSS_SELECTOR, ".item-image")
    ITEM_SKU = (By.CSS_SELECTOR, ".item-sku")
    
    # 수량 조절 요소들
    QUANTITY_INPUT = (By.CSS_SELECTOR, ".quantity-input")
    QUANTITY_INCREASE = (By.CSS_SELECTOR, ".quantity-increase")
    QUANTITY_DECREASE = (By.CSS_SELECTOR, ".quantity-decrease")
    UPDATE_QUANTITY_BUTTON = (By.CSS_SELECTOR, ".update-quantity")
    
    # 대체 수량 조절 로케이터들
    ALT_QUANTITY_INPUT_LOCATORS = [
        (By.CSS_SELECTOR, "input[name='quantity']"),
        (By.CSS_SELECTOR, ".qty-input"),
        (By.CSS_SELECTOR, "[data-testid='quantity']"),
        (By.XPATH, "//input[@type='number']")
    ]
    
    ALT_QUANTITY_INCREASE_LOCATORS = [
        (By.CSS_SELECTOR, ".qty-plus"),
        (By.CSS_SELECTOR, ".increase-qty"),
        (By.CSS_SELECTOR, "[data-action='increase']"),
        (By.XPATH, "//button[contains(text(), '+')]")
    ]
    
    ALT_QUANTITY_DECREASE_LOCATORS = [
        (By.CSS_SELECTOR, ".qty-minus"),
        (By.CSS_SELECTOR, ".decrease-qty"),
        (By.CSS_SELECTOR, "[data-action='decrease']"),
        (By.XPATH, "//button[contains(text(), '-')]")
    ]
    
    # 상품 제거 요소들
    REMOVE_ITEM_BUTTON = (By.CSS_SELECTOR, ".remove-item")
    DELETE_ITEM_BUTTON = (By.CSS_SELECTOR, ".delete-item")
    CLEAR_CART_BUTTON = (By.CSS_SELECTOR, ".clear-cart")
    
    # 대체 제거 버튼 로케이터들
    ALT_REMOVE_ITEM_LOCATORS = [
        (By.CSS_SELECTOR, ".remove"),
        (By.CSS_SELECTOR, ".delete"),
        (By.CSS_SELECTOR, ".trash"),
        (By.CSS_SELECTOR, "[data-action='remove']"),
        (By.XPATH, "//button[contains(text(), 'Remove')]"),
        (By.XPATH, "//button[contains(text(), '제거')]"),
        (By.XPATH, "//button[contains(text(), 'Delete')]")
    ]
    
    # 총액 및 요약 정보 요소들
    SUBTOTAL = (By.CSS_SELECTOR, ".subtotal")
    TAX_AMOUNT = (By.CSS_SELECTOR, ".tax-amount")
    SHIPPING_COST = (By.CSS_SELECTOR, ".shipping-cost")
    DISCOUNT_AMOUNT = (By.CSS_SELECTOR, ".discount-amount")
    TOTAL_AMOUNT = (By.CSS_SELECTOR, ".total-amount")
    ITEM_COUNT = (By.CSS_SELECTOR, ".item-count")
    
    # 대체 총액 로케이터들
    ALT_TOTAL_AMOUNT_LOCATORS = [
        (By.CSS_SELECTOR, ".grand-total"),
        (By.CSS_SELECTOR, ".final-total"),
        (By.CSS_SELECTOR, ".cart-total"),
        (By.CSS_SELECTOR, "[data-testid='total']"),
        (By.XPATH, "//*[contains(@class, 'total')]")
    ]
    
    # 쿠폰 및 할인 요소들
    COUPON_INPUT = (By.CSS_SELECTOR, ".coupon-input")
    APPLY_COUPON_BUTTON = (By.CSS_SELECTOR, ".apply-coupon")
    COUPON_MESSAGE = (By.CSS_SELECTOR, ".coupon-message")
    REMOVE_COUPON_BUTTON = (By.CSS_SELECTOR, ".remove-coupon")
    
    # 체크아웃 관련 요소들
    CHECKOUT_BUTTON = (By.CSS_SELECTOR, ".checkout-button")
    CONTINUE_SHOPPING_BUTTON = (By.CSS_SELECTOR, ".continue-shopping")
    SAVE_FOR_LATER_BUTTON = (By.CSS_SELECTOR, ".save-for-later")
    
    # 대체 체크아웃 버튼 로케이터들
    ALT_CHECKOUT_BUTTON_LOCATORS = [
        (By.CSS_SELECTOR, ".proceed-checkout"),
        (By.CSS_SELECTOR, ".checkout"),
        (By.CSS_SELECTOR, "[data-testid='checkout']"),
        (By.XPATH, "//button[contains(text(), 'Checkout')]"),
        (By.XPATH, "//button[contains(text(), '결제')]"),
        (By.XPATH, "//a[contains(text(), 'Checkout')]")
    ]
    
    # 상태 및 메시지 요소들
    LOADING_INDICATOR = (By.CSS_SELECTOR, ".loading")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message")
    
    def __init__(self, driver: WebDriver, base_url: str = None):
        """
        CartPage 초기화
        
        Args:
            driver: WebDriver 인스턴스
            base_url: 장바구니 페이지 URL
        """
        super().__init__(driver, base_url)
        self.logger = get_logger(self.__class__.__name__)
        
        # 장바구니 페이지 특화 설정
        self.update_timeout = 10  # 수량 업데이트 대기 시간
        self.checkout_timeout = 15  # 체크아웃 처리 대기 시간
        
        self.logger.debug("CartPage initialized")
    
    # ==================== 페이지 네비게이션 ====================
    
    def navigate_to_cart(self, cart_url: str = None) -> None:
        """
        장바구니 페이지로 이동
        
        Args:
            cart_url: 장바구니 페이지 URL (None이면 기본 URL 사용)
        """
        url = cart_url or f"{self.base_url}/cart"
        self.logger.info(f"Navigating to cart page: {url}")
        
        try:
            self.navigate_to(url)
            self.wait_for_cart_page_load()
            self.logger.info("Successfully navigated to cart page")
        except Exception as e:
            self.logger.error(f"Failed to navigate to cart page: {str(e)}")
            raise PageLoadTimeoutException(url, self.default_timeout)
    
    def wait_for_cart_page_load(self) -> None:
        """장바구니 페이지 로딩 완료 대기"""
        self.logger.debug("Waiting for cart page to load")
        
        try:
            # 기본 페이지 로딩 대기
            self.wait_for_page_load()
            
            # 장바구니 컨테이너가 로드될 때까지 대기
            self._find_cart_container()
            
            self.logger.debug("Cart page loaded successfully")
            
        except ElementNotFoundException as e:
            self.logger.error(f"Cart page elements not found: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Cart page load failed: {str(e)}")
            raise PageLoadTimeoutException("cart page", self.default_timeout)
    
    # ==================== 요소 찾기 (Smart Locator) ====================
    
    def _find_cart_container(self) -> tuple:
        """장바구니 컨테이너 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.CART_CONTAINER, timeout=2):
            return self.CART_CONTAINER
        
        # 대체 로케이터들 시도
        for locator in self.ALT_CART_CONTAINER_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found cart container with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("cart container", timeout=self.default_timeout)
    
    def _find_cart_items(self) -> List[tuple]:
        """장바구니 아이템들 찾기"""
        item_locators = []
        
        # 기본 로케이터 시도
        if self.is_element_present(self.CART_ITEM, timeout=2):
            item_locators.append(self.CART_ITEM)
        
        # 대체 로케이터들 시도
        for locator in self.ALT_CART_ITEM_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                item_locators.append(locator)
        
        return item_locators
    
    def _find_checkout_button(self) -> tuple:
        """체크아웃 버튼 찾기 (여러 로케이터 시도)"""
        # 기본 로케이터 먼저 시도
        if self.is_element_present(self.CHECKOUT_BUTTON, timeout=2):
            return self.CHECKOUT_BUTTON
        
        # 대체 로케이터들 시도
        for locator in self.ALT_CHECKOUT_BUTTON_LOCATORS:
            if self.is_element_present(locator, timeout=1):
                self.logger.debug(f"Found checkout button with alternative locator: {locator}")
                return locator
        
        raise ElementNotFoundException("checkout button", timeout=self.default_timeout)
    
    # ==================== 장바구니 상태 확인 ====================
    
    def is_cart_empty(self) -> bool:
        """
        장바구니 비어있음 여부 확인
        
        Returns:
            장바구니가 비어있으면 True
        """
        try:
            # "빈 장바구니" 메시지 확인
            if self.is_element_present(self.EMPTY_CART_MESSAGE, timeout=2):
                return True
            
            # 장바구니 아이템 개수 확인
            item_count = self.get_cart_item_count()
            return item_count == 0
            
        except Exception as e:
            self.logger.error(f"Error checking if cart is empty: {str(e)}")
            return True  # 오류 시 비어있다고 가정
    
    def get_cart_item_count(self) -> int:
        """
        장바구니 아이템 개수 가져오기
        
        Returns:
            장바구니 아이템 개수
        """
        try:
            # 아이템 개수 표시 요소에서 가져오기
            if self.is_element_present(self.ITEM_COUNT, timeout=2):
                count_text = self.get_text(self.ITEM_COUNT)
                # 숫자 추출
                import re
                numbers = re.findall(r'\d+', count_text)
                if numbers:
                    return int(numbers[0])
            
            # 직접 아이템 개수 세기
            item_locators = self._find_cart_items()
            total_count = 0
            for locator in item_locators:
                elements = self.find_elements(locator)
                total_count += len(elements)
            
            return total_count
            
        except Exception as e:
            self.logger.error(f"Error getting cart item count: {str(e)}")
            return 0
    
    def get_cart_items_info(self) -> List[Dict[str, Any]]:
        """
        장바구니 모든 아이템 정보 가져오기
        
        Returns:
            장바구니 아이템 정보 리스트
        """
        items_info = []
        
        try:
            item_locators = self._find_cart_items()
            
            for locator in item_locators:
                item_elements = self.find_elements(locator)
                
                for i, item_element in enumerate(item_elements):
                    item_info = {
                        'index': i,
                        'name': '',
                        'price': '',
                        'quantity': 0,
                        'total': '',
                        'sku': '',
                        'image_url': ''
                    }
                    
                    # 상품명 가져오기
                    try:
                        name_element = item_element.find_element(*self.ITEM_NAME)
                        item_info['name'] = name_element.text.strip()
                    except:
                        pass
                    
                    # 가격 가져오기
                    try:
                        price_element = item_element.find_element(*self.ITEM_PRICE)
                        item_info['price'] = price_element.text.strip()
                    except:
                        pass
                    
                    # 수량 가져오기
                    try:
                        quantity_element = item_element.find_element(*self.ITEM_QUANTITY)
                        quantity_text = quantity_element.text.strip()
                        # 숫자 추출
                        import re
                        numbers = re.findall(r'\d+', quantity_text)
                        if numbers:
                            item_info['quantity'] = int(numbers[0])
                    except:
                        pass
                    
                    # 총액 가져오기
                    try:
                        total_element = item_element.find_element(*self.ITEM_TOTAL)
                        item_info['total'] = total_element.text.strip()
                    except:
                        pass
                    
                    # SKU 가져오기
                    try:
                        sku_element = item_element.find_element(*self.ITEM_SKU)
                        item_info['sku'] = sku_element.text.strip()
                    except:
                        pass
                    
                    # 이미지 URL 가져오기
                    try:
                        image_element = item_element.find_element(*self.ITEM_IMAGE)
                        item_info['image_url'] = image_element.get_attribute('src')
                    except:
                        pass
                    
                    items_info.append(item_info)
                
                break  # 첫 번째 유효한 로케이터만 사용
            
            self.logger.debug(f"Retrieved info for {len(items_info)} cart items")
            return items_info
            
        except Exception as e:
            self.logger.error(f"Error getting cart items info: {str(e)}")
            return items_info
    
    # ==================== 수량 관리 ====================
    
    def update_item_quantity(self, item_index: int, new_quantity: int) -> bool:
        """
        특정 아이템의 수량 변경
        
        Args:
            item_index: 아이템 인덱스 (0부터 시작)
            new_quantity: 새로운 수량
            
        Returns:
            수량 변경 성공 여부
        """
        self.logger.debug(f"Updating item {item_index} quantity to {new_quantity}")
        
        try:
            item_locators = self._find_cart_items()
            
            for locator in item_locators:
                item_elements = self.find_elements(locator)
                
                if item_index < len(item_elements):
                    item_element = item_elements[item_index]
                    
                    # 수량 입력 필드 찾기
                    quantity_input = None
                    
                    # 기본 로케이터 시도
                    try:
                        quantity_input = item_element.find_element(*self.QUANTITY_INPUT)
                    except:
                        # 대체 로케이터들 시도
                        for alt_locator in self.ALT_QUANTITY_INPUT_LOCATORS:
                            try:
                                quantity_input = item_element.find_element(*alt_locator)
                                break
                            except:
                                continue
                    
                    if quantity_input:
                        # 수량 입력
                        quantity_input.clear()
                        quantity_input.send_keys(str(new_quantity))
                        
                        # 업데이트 버튼이 있으면 클릭
                        try:
                            update_button = item_element.find_element(*self.UPDATE_QUANTITY_BUTTON)
                            update_button.click()
                        except:
                            # 업데이트 버튼이 없으면 Enter 키 입력
                            from selenium.webdriver.common.keys import Keys
                            quantity_input.send_keys(Keys.RETURN)
                        
                        # 업데이트 완료 대기
                        self._wait_for_cart_update()
                        
                        self.logger.debug(f"Item {item_index} quantity updated to {new_quantity}")
                        return True
                    else:
                        self.logger.error(f"Quantity input not found for item {item_index}")
                        return False
            
            raise ElementNotFoundException(f"cart item at index {item_index}")
            
        except Exception as e:
            self.logger.error(f"Failed to update item quantity: {str(e)}")
            return False
    
    def increase_item_quantity(self, item_index: int) -> bool:
        """
        특정 아이템의 수량 1 증가
        
        Args:
            item_index: 아이템 인덱스 (0부터 시작)
            
        Returns:
            수량 증가 성공 여부
        """
        self.logger.debug(f"Increasing quantity for item {item_index}")
        
        try:
            item_locators = self._find_cart_items()
            
            for locator in item_locators:
                item_elements = self.find_elements(locator)
                
                if item_index < len(item_elements):
                    item_element = item_elements[item_index]
                    
                    # 수량 증가 버튼 찾기
                    increase_button = None
                    
                    # 기본 로케이터 시도
                    try:
                        increase_button = item_element.find_element(*self.QUANTITY_INCREASE)
                    except:
                        # 대체 로케이터들 시도
                        for alt_locator in self.ALT_QUANTITY_INCREASE_LOCATORS:
                            try:
                                increase_button = item_element.find_element(*alt_locator)
                                break
                            except:
                                continue
                    
                    if increase_button:
                        increase_button.click()
                        self._wait_for_cart_update()
                        self.logger.debug(f"Item {item_index} quantity increased")
                        return True
                    else:
                        self.logger.error(f"Increase button not found for item {item_index}")
                        return False
            
            raise ElementNotFoundException(f"cart item at index {item_index}")
            
        except Exception as e:
            self.logger.error(f"Failed to increase item quantity: {str(e)}")
            return False
    
    def decrease_item_quantity(self, item_index: int) -> bool:
        """
        특정 아이템의 수량 1 감소
        
        Args:
            item_index: 아이템 인덱스 (0부터 시작)
            
        Returns:
            수량 감소 성공 여부
        """
        self.logger.debug(f"Decreasing quantity for item {item_index}")
        
        try:
            item_locators = self._find_cart_items()
            
            for locator in item_locators:
                item_elements = self.find_elements(locator)
                
                if item_index < len(item_elements):
                    item_element = item_elements[item_index]
                    
                    # 수량 감소 버튼 찾기
                    decrease_button = None
                    
                    # 기본 로케이터 시도
                    try:
                        decrease_button = item_element.find_element(*self.QUANTITY_DECREASE)
                    except:
                        # 대체 로케이터들 시도
                        for alt_locator in self.ALT_QUANTITY_DECREASE_LOCATORS:
                            try:
                                decrease_button = item_element.find_element(*alt_locator)
                                break
                            except:
                                continue
                    
                    if decrease_button:
                        decrease_button.click()
                        self._wait_for_cart_update()
                        self.logger.debug(f"Item {item_index} quantity decreased")
                        return True
                    else:
                        self.logger.error(f"Decrease button not found for item {item_index}")
                        return False
            
            raise ElementNotFoundException(f"cart item at index {item_index}")
            
        except Exception as e:
            self.logger.error(f"Failed to decrease item quantity: {str(e)}")
            return False
    
    # ==================== 아이템 제거 ====================
    
    def remove_item(self, item_index: int) -> bool:
        """
        특정 아이템을 장바구니에서 제거
        
        Args:
            item_index: 제거할 아이템 인덱스 (0부터 시작)
            
        Returns:
            제거 성공 여부
        """
        self.logger.debug(f"Removing item at index {item_index}")
        
        try:
            item_locators = self._find_cart_items()
            
            for locator in item_locators:
                item_elements = self.find_elements(locator)
                
                if item_index < len(item_elements):
                    item_element = item_elements[item_index]
                    
                    # 제거 버튼 찾기
                    remove_button = None
                    
                    # 기본 로케이터들 시도
                    for remove_locator in [self.REMOVE_ITEM_BUTTON, self.DELETE_ITEM_BUTTON]:
                        try:
                            remove_button = item_element.find_element(*remove_locator)
                            break
                        except:
                            continue
                    
                    # 대체 로케이터들 시도
                    if not remove_button:
                        for alt_locator in self.ALT_REMOVE_ITEM_LOCATORS:
                            try:
                                remove_button = item_element.find_element(*alt_locator)
                                break
                            except:
                                continue
                    
                    if remove_button:
                        remove_button.click()
                        
                        # 확인 대화상자가 있으면 확인
                        try:
                            if self.is_alert_present(timeout=2):
                                self.accept_alert()
                        except:
                            pass
                        
                        self._wait_for_cart_update()
                        self.logger.debug(f"Item {item_index} removed from cart")
                        return True
                    else:
                        self.logger.error(f"Remove button not found for item {item_index}")
                        return False
            
            raise ElementNotFoundException(f"cart item at index {item_index}")
            
        except Exception as e:
            self.logger.error(f"Failed to remove item: {str(e)}")
            return False
    
    def remove_item_by_name(self, item_name: str) -> bool:
        """
        상품명으로 아이템 제거
        
        Args:
            item_name: 제거할 상품명
            
        Returns:
            제거 성공 여부
        """
        self.logger.debug(f"Removing item by name: {item_name}")
        
        try:
            items_info = self.get_cart_items_info()
            
            for item in items_info:
                if item_name.lower() in item['name'].lower():
                    return self.remove_item(item['index'])
            
            self.logger.warning(f"Item '{item_name}' not found in cart")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove item by name: {str(e)}")
            return False
    
    def clear_cart(self) -> bool:
        """
        장바구니 전체 비우기
        
        Returns:
            비우기 성공 여부
        """
        self.logger.debug("Clearing entire cart")
        
        try:
            # 전체 비우기 버튼이 있으면 사용
            if self.is_element_present(self.CLEAR_CART_BUTTON, timeout=2):
                self.click_element(self.CLEAR_CART_BUTTON)
                
                # 확인 대화상자가 있으면 확인
                try:
                    if self.is_alert_present(timeout=2):
                        self.accept_alert()
                except:
                    pass
                
                self._wait_for_cart_update()
                self.logger.debug("Cart cleared using clear button")
                return True
            else:
                # 개별 아이템들을 하나씩 제거
                item_count = self.get_cart_item_count()
                
                for i in range(item_count):
                    # 항상 첫 번째 아이템 제거 (제거 후 인덱스가 변경되므로)
                    if not self.remove_item(0):
                        self.logger.error(f"Failed to remove item at index 0")
                        return False
                
                self.logger.debug("Cart cleared by removing individual items")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear cart: {str(e)}")
            return False
    
    # ==================== 총액 및 요약 정보 ====================
    
    def get_subtotal(self) -> str:
        """
        소계 금액 가져오기
        
        Returns:
            소계 금액 문자열
        """
        try:
            if self.is_element_present(self.SUBTOTAL, timeout=2):
                return self.get_text(self.SUBTOTAL).strip()
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Error getting subtotal: {str(e)}")
            return ""
    
    def get_tax_amount(self) -> str:
        """
        세금 금액 가져오기
        
        Returns:
            세금 금액 문자열
        """
        try:
            if self.is_element_present(self.TAX_AMOUNT, timeout=2):
                return self.get_text(self.TAX_AMOUNT).strip()
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Error getting tax amount: {str(e)}")
            return ""
    
    def get_shipping_cost(self) -> str:
        """
        배송비 가져오기
        
        Returns:
            배송비 문자열
        """
        try:
            if self.is_element_present(self.SHIPPING_COST, timeout=2):
                return self.get_text(self.SHIPPING_COST).strip()
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Error getting shipping cost: {str(e)}")
            return ""
    
    def get_total_amount(self) -> str:
        """
        총 금액 가져오기
        
        Returns:
            총 금액 문자열
        """
        try:
            # 기본 로케이터 시도
            if self.is_element_present(self.TOTAL_AMOUNT, timeout=2):
                return self.get_text(self.TOTAL_AMOUNT).strip()
            
            # 대체 로케이터들 시도
            for locator in self.ALT_TOTAL_AMOUNT_LOCATORS:
                if self.is_element_present(locator, timeout=1):
                    return self.get_text(locator).strip()
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error getting total amount: {str(e)}")
            return ""
    
    def get_cart_summary(self) -> Dict[str, Any]:
        """
        장바구니 요약 정보 가져오기
        
        Returns:
            장바구니 요약 정보 딕셔너리
        """
        summary = {
            'item_count': self.get_cart_item_count(),
            'subtotal': self.get_subtotal(),
            'tax_amount': self.get_tax_amount(),
            'shipping_cost': self.get_shipping_cost(),
            'discount_amount': '',
            'total_amount': self.get_total_amount(),
            'is_empty': self.is_cart_empty()
        }
        
        # 할인 금액 가져오기
        try:
            if self.is_element_present(self.DISCOUNT_AMOUNT, timeout=2):
                summary['discount_amount'] = self.get_text(self.DISCOUNT_AMOUNT).strip()
        except:
            pass
        
        self.logger.debug(f"Cart summary: {summary}")
        return summary
    
    # ==================== 쿠폰 및 할인 ====================
    
    def apply_coupon(self, coupon_code: str) -> bool:
        """
        쿠폰 코드 적용
        
        Args:
            coupon_code: 쿠폰 코드
            
        Returns:
            쿠폰 적용 성공 여부
        """
        self.logger.debug(f"Applying coupon code: {coupon_code}")
        
        try:
            if not self.is_element_present(self.COUPON_INPUT, timeout=2):
                self.logger.warning("Coupon input not available")
                return False
            
            # 쿠폰 코드 입력
            self.input_text(self.COUPON_INPUT, coupon_code, clear_first=True)
            
            # 쿠폰 적용 버튼 클릭
            if self.is_element_present(self.APPLY_COUPON_BUTTON, timeout=2):
                self.click_element(self.APPLY_COUPON_BUTTON)
            else:
                # Enter 키로 적용
                from selenium.webdriver.common.keys import Keys
                self.send_keys(self.COUPON_INPUT, Keys.RETURN)
            
            # 적용 결과 대기
            self._wait_for_cart_update()
            
            # 성공 메시지 확인
            if self.is_element_present(self.SUCCESS_MESSAGE, timeout=3):
                self.logger.debug(f"Coupon '{coupon_code}' applied successfully")
                return True
            elif self.is_element_present(self.ERROR_MESSAGE, timeout=3):
                error_msg = self.get_text(self.ERROR_MESSAGE)
                self.logger.warning(f"Coupon application failed: {error_msg}")
                return False
            else:
                # 할인 금액이 표시되면 성공으로 간주
                if self.is_element_present(self.DISCOUNT_AMOUNT, timeout=2):
                    discount = self.get_text(self.DISCOUNT_AMOUNT)
                    if discount and discount != "$0.00":
                        self.logger.debug(f"Coupon applied, discount: {discount}")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to apply coupon: {str(e)}")
            return False
    
    def remove_coupon(self) -> bool:
        """
        적용된 쿠폰 제거
        
        Returns:
            쿠폰 제거 성공 여부
        """
        self.logger.debug("Removing applied coupon")
        
        try:
            if self.is_element_present(self.REMOVE_COUPON_BUTTON, timeout=2):
                self.click_element(self.REMOVE_COUPON_BUTTON)
                self._wait_for_cart_update()
                self.logger.debug("Coupon removed successfully")
                return True
            else:
                self.logger.warning("Remove coupon button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove coupon: {str(e)}")
            return False
    
    # ==================== 체크아웃 ====================
    
    def proceed_to_checkout(self) -> bool:
        """
        체크아웃으로 진행
        
        Returns:
            체크아웃 진행 성공 여부
        """
        self.logger.debug("Proceeding to checkout")
        
        try:
            # 장바구니가 비어있는지 확인
            if self.is_cart_empty():
                self.logger.warning("Cannot checkout with empty cart")
                return False
            
            # 체크아웃 버튼 찾기 및 클릭
            checkout_button_locator = self._find_checkout_button()
            self.click_element(checkout_button_locator)
            
            # 체크아웃 페이지 로딩 대기
            self.wait(2)  # 페이지 전환 대기
            
            # URL 변경 확인
            current_url = self.get_current_url()
            if 'checkout' in current_url.lower() or 'payment' in current_url.lower():
                self.logger.debug("Successfully proceeded to checkout")
                return True
            else:
                self.logger.warning("Checkout page not loaded")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to proceed to checkout: {str(e)}")
            return False
    
    def continue_shopping(self) -> bool:
        """
        쇼핑 계속하기
        
        Returns:
            쇼핑 계속하기 성공 여부
        """
        self.logger.debug("Continuing shopping")
        
        try:
            if self.is_element_present(self.CONTINUE_SHOPPING_BUTTON, timeout=2):
                self.click_element(self.CONTINUE_SHOPPING_BUTTON)
                self.wait(2)  # 페이지 전환 대기
                self.logger.debug("Continued shopping")
                return True
            else:
                self.logger.warning("Continue shopping button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to continue shopping: {str(e)}")
            return False
    
    # ==================== 유틸리티 메서드 ====================
    
    def _wait_for_cart_update(self) -> None:
        """장바구니 업데이트 완료 대기"""
        # 로딩 인디케이터가 있으면 사라질 때까지 대기
        if self.is_element_present(self.LOADING_INDICATOR, timeout=2):
            self.logger.debug("Waiting for cart update to complete")
            self.wait_for_element_invisible(self.LOADING_INDICATOR, timeout=self.update_timeout)
        
        # 짧은 대기 (JavaScript 처리 시간)
        self.wait(1)
    
    def refresh_cart(self) -> None:
        """장바구니 새로고침"""
        self.logger.debug("Refreshing cart")
        self.refresh_page()
        self.wait_for_cart_page_load()
    
    def take_cart_screenshot(self, filename: str = None) -> str:
        """
        장바구니 페이지 스크린샷 촬영
        
        Args:
            filename: 파일명
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cart_page_{timestamp}.png"
        
        return self.take_screenshot(filename)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"CartPage(url={self.get_current_url()}, items={self.get_cart_item_count()})"