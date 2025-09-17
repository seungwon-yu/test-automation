"""
예외 처리 클래스들의 단위 테스트
"""

import pytest
from unittest.mock import Mock

from src.core.exceptions import (
    TestFrameworkException, DriverException, DriverInitializationException,
    DriverTimeoutException, PageObjectException, ElementNotFoundException,
    ElementNotInteractableException, PageLoadTimeoutException,
    ConfigurationException, InvalidConfigurationException, MissingConfigurationException,
    TestDataException, TestDataGenerationException, TestDataCleanupException,
    ReportGenerationException, ReportTemplateException,
    APIException, APITimeoutException, APIResponseException,
    handle_driver_exception, handle_element_exception,
    create_context_dict, format_exception_message
)


class TestTestFrameworkException:
    """TestFrameworkException 기본 예외 클래스 테스트"""
    
    def test_basic_exception(self):
        """기본 예외 생성 테스트"""
        exception = TestFrameworkException("테스트 오류")
        
        assert str(exception) == "테스트 오류"
        assert exception.message == "테스트 오류"
        assert exception.error_code is None
        assert exception.context == {}
    
    def test_exception_with_error_code(self):
        """에러 코드가 있는 예외 테스트"""
        exception = TestFrameworkException("테스트 오류", error_code="TEST_001")
        
        assert str(exception) == "[TEST_001] 테스트 오류"
        assert exception.error_code == "TEST_001"
    
    def test_exception_with_context(self):
        """컨텍스트가 있는 예외 테스트"""
        context = {"test_name": "test_login", "browser": "chrome"}
        exception = TestFrameworkException("테스트 오류", context=context)
        
        assert exception.context == context
    
    def test_to_dict(self):
        """예외 정보를 딕셔너리로 변환 테스트"""
        context = {"key": "value"}
        exception = TestFrameworkException("테스트 오류", "ERR_001", context)
        
        result = exception.to_dict()
        
        assert result["exception_type"] == "TestFrameworkException"
        assert result["message"] == "테스트 오류"
        assert result["error_code"] == "ERR_001"
        assert result["context"] == context


class TestDriverException:
    """DriverException 클래스 테스트"""
    
    def test_driver_initialization_exception(self):
        """드라이버 초기화 예외 테스트"""
        exception = DriverInitializationException("chrome", "드라이버 파일을 찾을 수 없음")
        
        assert "chrome 드라이버 초기화 실패" in str(exception)
        assert exception.error_code == "DRIVER_INIT_FAILED"
        assert exception.context["browser"] == "chrome"
    
    def test_driver_timeout_exception(self):
        """드라이버 타임아웃 예외 테스트"""
        exception = DriverTimeoutException("페이지 로딩", 30)
        
        assert "드라이버 작업 타임아웃: 페이지 로딩 (30초)" in str(exception)
        assert exception.error_code == "DRIVER_TIMEOUT"
        assert exception.context["operation"] == "페이지 로딩"
        assert exception.context["timeout"] == 30
    
    def test_driver_exception_with_version(self):
        """드라이버 버전 정보가 있는 예외 테스트"""
        exception = DriverException("버전 호환성 오류", 
                                  browser="firefox", 
                                  driver_version="0.32.0")
        
        assert exception.context["browser"] == "firefox"
        assert exception.context["driver_version"] == "0.32.0"


class TestPageObjectException:
    """PageObjectException 클래스 테스트"""
    
    def test_element_not_found_exception(self):
        """요소를 찾을 수 없는 예외 테스트"""
        exception = ElementNotFoundException("//input[@id='username']", 
                                           page_name="LoginPage", 
                                           timeout=10)
        
        assert "요소를 찾을 수 없습니다" in str(exception)
        assert "대기시간: 10초" in str(exception)
        assert exception.error_code == "ELEMENT_NOT_FOUND"
        assert exception.context["page_name"] == "LoginPage"
        assert exception.context["locator"] == "//input[@id='username']"
        assert exception.context["timeout"] == 10
    
    def test_element_not_interactable_exception(self):
        """요소와 상호작용할 수 없는 예외 테스트"""
        exception = ElementNotInteractableException("//button[@id='submit']", 
                                                   "click", 
                                                   page_name="LoginPage")
        
        assert "요소와 상호작용할 수 없습니다" in str(exception)
        assert "액션: click" in str(exception)
        assert exception.error_code == "ELEMENT_NOT_INTERACTABLE"
        assert exception.context["action"] == "click"
    
    def test_page_load_timeout_exception(self):
        """페이지 로딩 타임아웃 예외 테스트"""
        exception = PageLoadTimeoutException("https://example.com", 30, "HomePage")
        
        assert "페이지 로딩 타임아웃" in str(exception)
        assert "https://example.com" in str(exception)
        assert "(30초)" in str(exception)
        assert exception.error_code == "PAGE_LOAD_TIMEOUT"
        assert exception.context["url"] == "https://example.com"


class TestConfigurationException:
    """ConfigurationException 클래스 테스트"""
    
    def test_invalid_configuration_exception(self):
        """잘못된 설정 예외 테스트"""
        exception = InvalidConfigurationException("timeout", -1, "음수 값은 허용되지 않음")
        
        assert "잘못된 설정값: timeout=-1" in str(exception)
        assert "음수 값은 허용되지 않음" in str(exception)
        assert exception.error_code == "INVALID_CONFIG"
        assert exception.context["config_key"] == "timeout"
        assert exception.context["value"] == -1
    
    def test_missing_configuration_exception(self):
        """필수 설정 누락 예외 테스트"""
        exception = MissingConfigurationException("base_url", "config.yml")
        
        assert "필수 설정이 누락되었습니다: base_url" in str(exception)
        assert "파일: config.yml" in str(exception)
        assert exception.error_code == "MISSING_CONFIG"
        assert exception.context["config_key"] == "base_url"
        assert exception.context["config_file"] == "config.yml"


class TestTestDataException:
    """TestDataException 클래스 테스트"""
    
    def test_test_data_generation_exception(self):
        """테스트 데이터 생성 실패 예외 테스트"""
        exception = TestDataGenerationException("user_data", "데이터베이스 연결 실패")
        
        assert "테스트 데이터 생성 실패: user_data" in str(exception)
        assert "데이터베이스 연결 실패" in str(exception)
        assert exception.error_code == "TEST_DATA_GENERATION_FAILED"
        assert exception.context["data_type"] == "user_data"
        assert exception.context["operation"] == "generation"
    
    def test_test_data_cleanup_exception(self):
        """테스트 데이터 정리 실패 예외 테스트"""
        exception = TestDataCleanupException("temp_files", "권한 부족")
        
        assert "테스트 데이터 정리 실패: temp_files" in str(exception)
        assert "권한 부족" in str(exception)
        assert exception.error_code == "TEST_DATA_CLEANUP_FAILED"
        assert exception.context["operation"] == "cleanup"


class TestReportGenerationException:
    """ReportGenerationException 클래스 테스트"""
    
    def test_report_template_exception(self):
        """리포트 템플릿 예외 테스트"""
        exception = ReportTemplateException("html_template.jinja2", "템플릿 파일을 찾을 수 없음")
        
        assert "리포트 템플릿 오류: html_template.jinja2" in str(exception)
        assert "템플릿 파일을 찾을 수 없음" in str(exception)
        assert exception.error_code == "REPORT_TEMPLATE_ERROR"
        assert exception.context["template_name"] == "html_template.jinja2"


class TestAPIException:
    """APIException 클래스 테스트"""
    
    def test_api_timeout_exception(self):
        """API 타임아웃 예외 테스트"""
        exception = APITimeoutException("/api/users", 30)
        
        assert "API 요청 타임아웃: /api/users (30초)" in str(exception)
        assert exception.error_code == "API_TIMEOUT"
        assert exception.context["endpoint"] == "/api/users"
        assert exception.context["timeout"] == 30
    
    def test_api_response_exception(self):
        """API 응답 오류 예외 테스트"""
        exception = APIResponseException("/api/login", 401, "Unauthorized")
        
        assert "API 응답 오류: /api/login (상태코드: 401)" in str(exception)
        assert exception.error_code == "API_RESPONSE_ERROR"
        assert exception.context["endpoint"] == "/api/login"
        assert exception.context["status_code"] == 401
        assert exception.context["response_text"] == "Unauthorized"


class TestExceptionDecorators:
    """예외 처리 데코레이터 테스트"""
    
    def test_handle_driver_exception_decorator(self):
        """드라이버 예외 처리 데코레이터 테스트"""
        
        # WebDriverException 클래스를 시뮬레이션
        class MockWebDriverException(Exception):
            pass
        
        @handle_driver_exception
        def mock_driver_function():
            raise MockWebDriverException("WebDriver error")
        
        with pytest.raises(DriverException, match="드라이버 오류"):
            mock_driver_function()
    
    def test_handle_element_exception_decorator_not_found(self):
        """요소 찾기 예외 처리 데코레이터 테스트"""
        
        @handle_element_exception
        def mock_element_function():
            raise Exception("no such element")
        
        with pytest.raises(ElementNotFoundException):
            mock_element_function()
    
    def test_handle_element_exception_decorator_not_interactable(self):
        """요소 상호작용 예외 처리 데코레이터 테스트"""
        
        @handle_element_exception
        def mock_element_function():
            raise Exception("element not interactable")
        
        with pytest.raises(ElementNotInteractableException):
            mock_element_function()
    
    def test_handle_element_exception_decorator_passthrough(self):
        """다른 예외는 그대로 전달하는지 테스트"""
        
        @handle_element_exception
        def mock_element_function():
            raise ValueError("다른 종류의 오류")
        
        with pytest.raises(ValueError, match="다른 종류의 오류"):
            mock_element_function()


class TestUtilityFunctions:
    """유틸리티 함수들 테스트"""
    
    def test_create_context_dict(self):
        """컨텍스트 딕셔너리 생성 함수 테스트"""
        result = create_context_dict(
            test_name="test_login",
            browser="chrome",
            timeout=None,  # None 값은 제외되어야 함
            page_url="https://example.com"
        )
        
        expected = {
            "test_name": "test_login",
            "browser": "chrome",
            "page_url": "https://example.com"
        }
        
        assert result == expected
        assert "timeout" not in result
    
    def test_format_exception_message_without_context(self):
        """컨텍스트 없는 예외 메시지 포맷팅 테스트"""
        exception = TestFrameworkException("테스트 오류", "ERR_001")
        
        result = format_exception_message(exception)
        
        assert result == "[ERR_001] 테스트 오류"
    
    def test_format_exception_message_with_context(self):
        """컨텍스트 있는 예외 메시지 포맷팅 테스트"""
        context = {"browser": "chrome", "timeout": 30}
        exception = TestFrameworkException("테스트 오류", "ERR_001", context)
        
        result = format_exception_message(exception)
        
        assert "[ERR_001] 테스트 오류" in result
        assert "[Context:" in result
        assert "browser=chrome" in result
        assert "timeout=30" in result
    
    def test_exception_inheritance(self):
        """예외 클래스 상속 관계 테스트"""
        driver_exception = DriverException("드라이버 오류")
        element_exception = ElementNotFoundException("//input")
        config_exception = InvalidConfigurationException("key", "value", "reason")
        
        # 모든 커스텀 예외는 TestFrameworkException을 상속해야 함
        assert isinstance(driver_exception, TestFrameworkException)
        assert isinstance(element_exception, TestFrameworkException)
        assert isinstance(config_exception, TestFrameworkException)
        
        # 구체적인 상속 관계도 확인
        assert isinstance(element_exception, PageObjectException)
        assert isinstance(config_exception, ConfigurationException)
    
    def test_exception_context_preservation(self):
        """예외 컨텍스트 정보 보존 테스트"""
        original_context = {"key1": "value1", "key2": "value2"}
        exception = TestFrameworkException("오류", context=original_context)
        
        # 컨텍스트가 변경되지 않아야 함
        assert exception.context == original_context
        assert exception.context is not original_context  # 복사본이어야 함
        
        # 원본 컨텍스트를 변경해도 예외의 컨텍스트는 영향받지 않아야 함
        original_context["key3"] = "value3"
        assert "key3" not in exception.context
    
    def test_nested_exception_handling(self):
        """중첩된 예외 처리 테스트"""
        try:
            try:
                raise ValueError("원본 오류")
            except ValueError as e:
                raise DriverException("드라이버 오류 발생") from e
        except DriverException as de:
            assert str(de) == "드라이버 오류 발생"
            assert isinstance(de.__cause__, ValueError)
            assert str(de.__cause__) == "원본 오류"