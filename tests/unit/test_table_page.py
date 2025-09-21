"""
CartPage 클래스 단위 테스트

이 모듈은 CartPage 클래스의 핵심 기능에 대한
단위 테스트를 제공합니다.
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from src.pages.cart_page import CartPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestCartPage:
    """CartPage 클래스 테스트"""
    
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
                    self.cart_page = CartPage(self.mock_driver, "http://test.com")
    
    def test_cart_page_initialization(self):
        """CartPage 초기화 테스트"""
        assert self.cart_page.driver == self.mock_driver
        assert self.cart_page.base_url == "http://test.com"
        assert self.cart_page.update_timeout == 10
        assert self.cart_page.checkout_timeout == 15
        assert hasattr(self.cart_page, 'logger')
    
    def test_navigate_to_cart_default_url(self):
        """기본 URL로 장바구니 페이지 이동 테스트"""
        with patch.object(self.cart_page, 'navigate_to') as mock_navigate:
            with patch.object(self.cart_page, 'wait_for_cart_page_load'):
                self.cart_page.navigate_to_cart()
        
        mock_navigate.assert_called_once_with("http://test.com/cart")
    
    def test_is_cart_empty_true(self):
        """장바구니 비어있음 확인 - 비어있음"""
        with patch.object(self.cart_page, 'is_element_present', return_value=True):
            result = self.cart_page.is_cart_empty()
        
        assert result is True
    
    def test_is_cart_empty_false(self):
        """장바구니 비어있음 확인 - 아이템 있음"""
        with patch.object(self.cart_page, 'is_element_present', return_value=False):
            with patch.object(self.cart_page, 'get_cart_item_count', return_value=2):
                result = self.cart_page.is_cart_empty()
        
        assert result is False
    
    def test_get_cart_item_count(self):
        """장바구니 아이템 개수 가져오기 테스트"""
        mock_elements = [Mock(), Mock(), Mock()]
        
        with patch.object(self.cart_page, 'is_element_present', return_value=False):  # no count element
            with patch.object(self.cart_page, '_find_cart_items', return_value=[(By.CSS_SELECTOR, ".item")]):
                with patch.object(self.cart_page, 'find_elements', return_value=mock_elements):
                    result = self.cart_page.get_cart_item_count()
        
        assert result == 3
    
    def test_update_item_quantity_success(self):
        """아이템 수량 변경 성공 테스트"""
        mock_item_element = Mock()
        mock_quantity_input = Mock()
        mock_item_element.find_element.return_value = mock_quantity_input
        
        with patch.object(self.cart_page, '_find_cart_items', return_value=[(By.CSS_SELECTOR, ".item")]):
            with patch.object(self.cart_page, 'find_elements', return_value=[mock_item_element]):
                with patch.object(self.cart_page, '_wait_for_cart_update'):
                    result = self.cart_page.update_item_quantity(0, 5)
        
        mock_quantity_input.clear.assert_called_once()
        mock_quantity_input.send_keys.assert_called_once_with("5")
        assert result is True
    
    def test_remove_item_success(self):
        """아이템 제거 성공 테스트"""
        mock_item_element = Mock()
        mock_remove_button = Mock()
        mock_item_element.find_element.return_value = mock_remove_button
        
        with patch.object(self.cart_page, '_find_cart_items', return_value=[(By.CSS_SELECTOR, ".item")]):
            with patch.object(self.cart_page, 'find_elements', return_value=[mock_item_element]):
                with patch.object(self.cart_page, 'is_alert_present', return_value=False):
                    with patch.object(self.cart_page, '_wait_for_cart_update'):
                        result = self.cart_page.remove_item(0)
        
        mock_remove_button.click.assert_called_once()
        assert result is True
    
    def test_get_total_amount(self):
        """총 금액 가져오기 테스트"""
        with patch.object(self.cart_page, 'is_element_present', return_value=True):
            with patch.object(self.cart_page, 'get_text', return_value="$99.99"):
                result = self.cart_page.get_total_amount()
        
        assert result == "$99.99"
    
    def test_apply_coupon_success(self):
        """쿠폰 적용 성공 테스트"""
        # is_element_present 호출 순서: input, button, success_msg, error_msg, discount
        with patch.object(self.cart_page, 'is_element_present', side_effect=[True, True, False, False, True]):
            with patch.object(self.cart_page, 'input_text'):
                with patch.object(self.cart_page, 'click_element'):
                    with patch.object(self.cart_page, '_wait_for_cart_update'):
                        with patch.object(self.cart_page, 'get_text', return_value="$10.00"):
                            result = self.cart_page.apply_coupon("SAVE10")
        
        assert result is True
    
    def test_proceed_to_checkout_success(self):
        """체크아웃 진행 성공 테스트"""
        with patch.object(self.cart_page, 'is_cart_empty', return_value=False):
            with patch.object(self.cart_page, '_find_checkout_button', return_value=(By.CSS_SELECTOR, ".checkout")):
                with patch.object(self.cart_page, 'click_element'):
                    with patch.object(self.cart_page, 'wait'):
                        with patch.object(self.cart_page, 'get_current_url', return_value="http://test.com/checkout"):
                            result = self.cart_page.proceed_to_checkout()
        
        assert result is True
    
    def test_proceed_to_checkout_empty_cart(self):
        """빈 장바구니로 체크아웃 시도 테스트"""
        with patch.object(self.cart_page, 'is_cart_empty', return_value=True):
            result = self.cart_page.proceed_to_checkout()
        
        assert result is False
    
    def test_get_cart_summary(self):
        """장바구니 요약 정보 가져오기 테스트"""
        with patch.object(self.cart_page, 'get_cart_item_count', return_value=3):
            with patch.object(self.cart_page, 'get_subtotal', return_value="$89.99"):
                with patch.object(self.cart_page, 'get_tax_amount', return_value="$9.00"):
                    with patch.object(self.cart_page, 'get_shipping_cost', return_value="$5.00"):
                        with patch.object(self.cart_page, 'get_total_amount', return_value="$99.99"):
                            with patch.object(self.cart_page, 'is_cart_empty', return_value=False):
                                result = self.cart_page.get_cart_summary()
        
        assert result['item_count'] == 3
        assert result['subtotal'] == "$89.99"
        assert result['tax_amount'] == "$9.00"
        assert result['shipping_cost'] == "$5.00"
        assert result['total_amount'] == "$99.99"
        assert result['is_empty'] is False