"""
PaymentPage 클래스 단위 테스트

이 모듈은 PaymentPage 클래스의 핵심 기능에 대한
단위 테스트를 제공합니다.
"""

import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from src.pages.payment_page import PaymentPage
from src.core.exceptions import (
    ElementNotFoundException,
    PageLoadTimeoutException
)


class TestPaymentPage:
    """PaymentPage 클래스 테스트"""
    
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
                    self.payment_page = PaymentPage(self.mock_driver, "http://test.com")
    
    def test_payment_page_initialization(self):
        """PaymentPage 초기화 테스트"""
        assert self.payment_page.driver == self.mock_driver
        assert self.payment_page.base_url == "http://test.com"
        assert self.payment_page.payment_timeout == 30
        assert self.payment_page.validation_timeout == 5
        assert hasattr(self.payment_page, 'logger')
    
    def test_navigate_to_payment_default_url(self):
        """기본 URL로 결제 페이지 이동 테스트"""
        with patch.object(self.payment_page, 'navigate_to') as mock_navigate:
            with patch.object(self.payment_page, 'wait_for_payment_page_load'):
                self.payment_page.navigate_to_payment()
        
        mock_navigate.assert_called_once_with("http://test.com/checkout")
    
    def test_fill_shipping_info_success(self):
        """배송 정보 입력 성공 테스트"""
        shipping_info = {
            'first_name': '홍',
            'last_name': '길동',
            'address': '서울시 강남구',
            'city': '서울',
            'zip': '12345'
        }
        
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, '_find_field_with_alternatives', side_effect=lambda name, default, alt: default):
                with patch.object(self.payment_page, 'input_text') as mock_input:
                    result = self.payment_page.fill_shipping_info(shipping_info)
        
        assert result is True
        assert mock_input.call_count == 5  # 5개 필드 입력
    
    def test_select_payment_method_credit_card(self):
        """신용카드 결제 방법 선택 테스트"""
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, 'click_element') as mock_click:
                result = self.payment_page.select_payment_method('credit_card')
        
        mock_click.assert_called_once_with(self.payment_page.CREDIT_CARD_OPTION)
        assert result is True
    
    def test_fill_credit_card_info_success(self):
        """신용카드 정보 입력 성공 테스트"""
        card_info = {
            'number': '1234567890123456',
            'holder_name': '홍길동',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }
        
        mock_month_element = Mock()
        mock_month_element.tag_name = 'select'
        mock_year_element = Mock()
        mock_year_element.tag_name = 'select'
        
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, '_find_field_with_alternatives', side_effect=lambda name, default, alt: default):
                with patch.object(self.payment_page, 'input_text'):
                    with patch.object(self.payment_page, 'find_element', side_effect=[mock_month_element, mock_year_element]):
                        with patch.object(self.payment_page, 'select_dropdown_by_value') as mock_select:
                            result = self.payment_page.fill_credit_card_info(card_info)
        
        assert result is True
        assert mock_select.call_count == 2  # 월, 년도 선택
    
    def test_apply_promo_code_success(self):
        """프로모션 코드 적용 성공 테스트"""
        with patch.object(self.payment_page, 'is_element_present', side_effect=[True, True, True]):  # input, button, discount
            with patch.object(self.payment_page, 'input_text'):
                with patch.object(self.payment_page, 'click_element'):
                    with patch.object(self.payment_page, '_wait_for_payment_update'):
                        with patch.object(self.payment_page, 'get_text', return_value="$10.00"):
                            result = self.payment_page.apply_promo_code("SAVE10")
        
        assert result is True
    
    def test_place_order_success(self):
        """주문하기 성공 테스트"""
        with patch.object(self.payment_page, '_find_place_order_button', return_value=(By.CSS_SELECTOR, ".place-order")):
            with patch.object(self.payment_page, 'click_element'):
                with patch.object(self.payment_page, '_wait_for_payment_processing'):
                    with patch.object(self.payment_page, 'is_payment_successful', return_value=True):
                        result = self.payment_page.place_order()
        
        assert result is True
    
    def test_place_order_failure(self):
        """주문하기 실패 테스트"""
        with patch.object(self.payment_page, '_find_place_order_button', return_value=(By.CSS_SELECTOR, ".place-order")):
            with patch.object(self.payment_page, 'click_element'):
                with patch.object(self.payment_page, '_wait_for_payment_processing'):
                    with patch.object(self.payment_page, 'is_payment_successful', return_value=False):
                        with patch.object(self.payment_page, 'is_element_present', return_value=True):
                            with patch.object(self.payment_page, 'get_text', return_value="Payment failed"):
                                result = self.payment_page.place_order()
        
        assert result is False
    
    def test_is_payment_successful_by_url(self):
        """URL로 결제 성공 확인 테스트"""
        with patch.object(self.payment_page, 'get_current_url', return_value="http://test.com/confirmation"):
            result = self.payment_page.is_payment_successful()
        
        assert result is True
    
    def test_is_payment_successful_by_element(self):
        """요소로 결제 성공 확인 테스트"""
        with patch.object(self.payment_page, 'get_current_url', return_value="http://test.com/checkout"):
            with patch.object(self.payment_page, 'is_element_present', return_value=True):
                result = self.payment_page.is_payment_successful()
        
        assert result is True
    
    def test_get_order_number(self):
        """주문 번호 가져오기 테스트"""
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, 'get_text', return_value="Order #ORD123456"):
                result = self.payment_page.get_order_number()
        
        assert result == "ORD123456"
    
    def test_get_order_summary(self):
        """주문 요약 정보 가져오기 테스트"""
        mock_item_element = Mock()
        mock_item_element.find_element.side_effect = [
            Mock(text="Test Product"),  # name
            Mock(text="2"),  # quantity
            Mock(text="$19.99")  # price
        ]
        
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, 'find_elements', return_value=[mock_item_element]):
                with patch.object(self.payment_page, 'get_text', side_effect=["$39.98", "$4.00", "$5.00", "$48.98"]):
                    result = self.payment_page.get_order_summary()
        
        assert len(result['items']) == 1
        assert result['items'][0]['name'] == "Test Product"
        assert result['subtotal'] == "$39.98"
        assert result['total'] == "$48.98"
    
    def test_set_billing_same_as_shipping(self):
        """청구지 주소를 배송지와 동일하게 설정 테스트"""
        mock_checkbox = Mock()
        mock_checkbox.is_selected.return_value = False
        
        with patch.object(self.payment_page, 'is_element_present', return_value=True):
            with patch.object(self.payment_page, 'find_element', return_value=mock_checkbox):
                with patch.object(self.payment_page, 'click_element') as mock_click:
                    result = self.payment_page.set_billing_same_as_shipping(True)
        
        mock_click.assert_called_once()
        assert result is True