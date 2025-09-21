"""
페이지 객체 통합 테스트

이 모듈은 페이지 객체들 간의 통합 테스트를 제공합니다.
새로운 테스트 유틸리티를 활용한 예제입니다.
"""

import pytest
from unittest.mock import Mock, patch

from tests.utils import (
    PageTestCase,
    assert_element_present,
    assert_element_visible,
    assert_page_loaded,
    assert_url_contains,
    assert_login_successful,
    create_mock_element,
    create_mock_driver
)

from src.pages.login_page import LoginPage
from src.pages.base_page import BasePage


class TestPageIntegration(PageTestCase):
    """페이지 객체 통합 테스트"""
    
    def test_login_page_creation_with_utilities(self):
        """새로운 유틸리티를 사용한 LoginPage 생성 테스트"""
        # PageTestCase에서 제공하는 Mock들 사용
        login_page = LoginPage(self.mock_driver, "http://test.example.com")
        
        # 기본 설정 확인
        assert login_page.driver == self.mock_driver
        assert login_page.base_url == "http://test.example.com"
        
        # Mock 설정 확인
        self.assert_log_message("debug", "LoginPage initialized")
    
    def test_element_interaction_with_assertions(self):
        """커스텀 어설션을 사용한 요소 상호작용 테스트"""
        # Mock 요소 생성
        username_element = self.create_mock_element(
            tag_name="input",
            attributes={"type": "text", "id": "username"}
        )
        
        # 요소 찾기 Mock 설정
        self.setup_element_finding((By.ID, "username"), username_element)
        
        # LoginPage 생성
        login_page = LoginPage(self.mock_driver)
        
        # 사용자명 입력 테스트
        login_page.enter_username("testuser")
        
        # 상호작용 검증
        self.assert_element_interaction(username_element, "clear")
        self.assert_element_interaction(username_element, "send_keys", "testuser")
    
    def test_login_flow_with_performance_assertion(self):
        """성능 어설션을 포함한 로그인 플로우 테스트"""
        # Mock 요소들 설정
        username_element = self.create_mock_element()
        password_element = self.create_mock_element()
        login_button = self.create_mock_element(tag_name="button")
        
        # 요소 찾기 Mock 설정
        self.mock_driver.find_element.side_effect = [
            username_element, password_element, login_button
        ]
        
        # LoginPage 생성
        login_page = LoginPage(self.mock_driver)
        
        # 성능 측정과 함께 로그인 실행
        with self.assert_execution_time(2.0):  # 2초 이내 실행
            with patch.object(login_page, 'wait_for_login_page_load'):
                with patch.object(login_page, 'is_login_successful', return_value=True):
                    result = login_page.login("testuser", "testpass")
        
        assert result is True
    
    def test_multiple_page_navigation(self):
        """여러 페이지 간 네비게이션 테스트"""
        # 여러 페이지 객체 생성
        base_page = BasePage(self.mock_driver)
        login_page = LoginPage(self.mock_driver)
        
        # 네비게이션 시뮬레이션
        self.mock_driver.current_url = "http://test.example.com/login"
        
        # 로그인 페이지로 이동
        with patch.object(login_page, 'wait_for_login_page_load'):
            login_page.navigate_to_login()
        
        # 드라이버 액션 검증
        self.assert_driver_action("get", "http://test.example.com/login")
    
    def test_error_handling_integration(self):
        """에러 처리 통합 테스트"""
        from selenium.common.exceptions import NoSuchElementException
        from src.core.exceptions import ElementNotFoundException
        
        # 요소를 찾을 수 없는 상황 시뮬레이션
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        login_page = LoginPage(self.mock_driver)
        
        # 예외 발생 확인
        with pytest.raises(ElementNotFoundException):
            login_page._find_username_field()
    
    def test_mock_driver_capabilities(self):
        """Mock 드라이버 기능 테스트"""
        # 다양한 브라우저 Mock 테스트
        chrome_driver = create_mock_driver("chrome")
        firefox_driver = create_mock_driver("firefox")
        edge_driver = create_mock_driver("edge")
        
        assert chrome_driver.name == "chrome"
        assert firefox_driver.name == "firefox"
        assert edge_driver.name == "MicrosoftEdge"
        
        # 각 드라이버의 capabilities 확인
        assert chrome_driver.capabilities["browserName"] == "chrome"
        assert firefox_driver.capabilities["browserName"] == "firefox"
        assert edge_driver.capabilities["browserName"] == "MicrosoftEdge"


class TestPageObjectPatterns(PageTestCase):
    """Page Object Pattern 테스트"""
    
    def test_page_object_inheritance(self):
        """페이지 객체 상속 구조 테스트"""
        login_page = LoginPage(self.mock_driver)
        
        # BasePage 메서드 상속 확인
        assert hasattr(login_page, 'find_element')
        assert hasattr(login_page, 'click_element')
        assert hasattr(login_page, 'input_text')
        assert hasattr(login_page, 'take_screenshot')
        
        # LoginPage 특화 메서드 확인
        assert hasattr(login_page, 'login')
        assert hasattr(login_page, 'enter_username')
        assert hasattr(login_page, 'enter_password')
    
    def test_smart_locator_fallback(self):
        """Smart Locator 대체 로케이터 테스트"""
        login_page = LoginPage(self.mock_driver)
        
        # 기본 로케이터 실패, 대체 로케이터 성공 시뮬레이션
        def mock_is_element_present(locator, timeout=2):
            # 첫 번째 호출(기본 로케이터)은 False, 두 번째 호출(대체 로케이터)은 True
            if locator == login_page.USERNAME_INPUT:
                return False
            elif locator == login_page.ALT_USERNAME_LOCATORS[0]:
                return True
            return False
        
        with patch.object(login_page, 'is_element_present', side_effect=mock_is_element_present):
            result = login_page._find_username_field()
            assert result == login_page.ALT_USERNAME_LOCATORS[0]
    
    def test_page_validation_utilities(self):
        """페이지 검증 유틸리티 테스트"""
        login_page = LoginPage(self.mock_driver)
        
        # 모든 요소가 존재하는 경우
        with patch.object(login_page, '_find_username_field', return_value=(By.ID, "username")):
            with patch.object(login_page, '_find_password_field', return_value=(By.ID, "password")):
                with patch.object(login_page, '_find_login_button', return_value=(By.ID, "login-btn")):
                    
                    validation_result = login_page.validate_login_page_elements()
                    
                    assert validation_result['username_field'] is True
                    assert validation_result['password_field'] is True
                    assert validation_result['login_button'] is True
                    assert validation_result['all_elements_present'] is True


@pytest.mark.integration
class TestRealWorldScenarios(PageTestCase):
    """실제 시나리오 통합 테스트"""
    
    def test_complete_login_scenario(self, login_scenarios):
        """완전한 로그인 시나리오 테스트 (픽스처 사용)"""
        login_page = LoginPage(self.mock_driver)
        
        for scenario in login_scenarios:
            with self.subTest(scenario=scenario['name']):
                # Mock 설정
                self.setup_login_scenario_mocks(scenario)
                
                # 로그인 시도
                try:
                    result = login_page.login(
                        scenario['username'], 
                        scenario['password']
                    )
                    assert result == scenario['expected_result']
                except Exception as e:
                    if not scenario['expected_result']:
                        # 실패가 예상된 경우
                        assert 'expected_error' in scenario
                    else:
                        raise
    
    def setup_login_scenario_mocks(self, scenario):
        """로그인 시나리오별 Mock 설정"""
        # 페이지 로딩 Mock
        with patch.object(LoginPage, 'wait_for_login_page_load'):
            pass
        
        # 요소 상호작용 Mock
        username_element = self.create_mock_element()
        password_element = self.create_mock_element()
        login_button = self.create_mock_element()
        
        self.mock_driver.find_element.side_effect = [
            username_element, password_element, login_button
        ]
        
        # 로그인 결과 Mock
        if scenario['expected_result']:
            # 성공 시나리오
            self.mock_driver.current_url = f"http://test.example.com{scenario.get('expected_url', '/dashboard')}"
            with patch.object(LoginPage, 'is_login_successful', return_value=True):
                pass
        else:
            # 실패 시나리오
            self.mock_driver.current_url = "http://test.example.com/login"
            with patch.object(LoginPage, 'is_login_successful', return_value=False):
                with patch.object(LoginPage, 'get_error_message', return_value=scenario.get('expected_error', 'Login failed')):
                    pass
    
    def test_cross_browser_compatibility(self, browser_type):
        """크로스 브라우저 호환성 테스트 (파라미터화)"""
        # 브라우저별 Mock 드라이버 생성
        mock_driver = create_mock_driver(browser_type)
        
        # 브라우저별 설정 적용
        self.setup_mock_config()
        self.mock_config_manager.get_browser_config.return_value = {
            'browser': browser_type,
            'headless': True
        }
        
        # LoginPage 생성 및 테스트
        login_page = LoginPage(mock_driver)
        
        # 브라우저별 특성 확인
        assert mock_driver.capabilities['browserName'] in [browser_type, 'MicrosoftEdge']
    
    def test_performance_benchmarks(self, performance_thresholds):
        """성능 벤치마크 테스트"""
        login_page = LoginPage(self.mock_driver)
        
        # 각 액션별 성능 측정
        with self.measure_time('page_load'):
            with patch.object(login_page, 'navigate_to_login'):
                login_page.navigate_to_login()
        
        with self.measure_time('element_find'):
            with patch.object(login_page, '_find_username_field', return_value=(By.ID, "username")):
                login_page._find_username_field()
        
        # 성능 임계값 검증
        self.assert_performance('page_load', performance_thresholds['page_load'])
        self.assert_performance('element_find', performance_thresholds['element_find'])


# 편의 함수들
def create_integration_test_suite():
    """통합 테스트 스위트 생성"""
    from tests.utils import create_test_suite
    
    return create_test_suite(
        TestPageIntegration,
        TestPageObjectPatterns,
        TestRealWorldScenarios
    )


if __name__ == "__main__":
    # 통합 테스트 실행 예제
    suite = create_integration_test_suite()
    
    import unittest
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)