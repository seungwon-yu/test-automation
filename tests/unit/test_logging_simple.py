"""
구조화된 로깅 시스템의 단위 테스트 (간소화 버전)
"""

import pytest
import json
import logging
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path

from src.core.logging import (
    LogLevel, LogContext, StructuredFormatter, ConsoleFormatter,
    TestLogger, get_logger, setup_logging
)
from src.core.exceptions import TestFrameworkException


class TestLogLevel:
    """LogLevel Enum 테스트"""
    
    def test_log_level_values(self):
        """로그 레벨 값 테스트"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
    
    def test_from_string_valid(self):
        """유효한 문자열로부터 LogLevel 생성 테스트"""
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("Warning") == LogLevel.WARNING
    
    def test_from_string_invalid(self):
        """잘못된 문자열로부터 LogLevel 생성 테스트"""
        assert LogLevel.from_string("invalid") == LogLevel.INFO
        assert LogLevel.from_string("") == LogLevel.INFO


class TestLogContext:
    """LogContext 클래스 테스트"""
    
    def test_set_and_get_context(self):
        """컨텍스트 설정 및 조회 테스트"""
        context = LogContext()
        
        context.set_context(test_name="test_login", browser="chrome")
        result = context.get_context()
        
        assert result["test_name"] == "test_login"
        assert result["browser"] == "chrome"
    
    def test_clear_context(self):
        """컨텍스트 초기화 테스트"""
        context = LogContext()
        
        context.set_context(test_name="test_login")
        context.clear_context()
        result = context.get_context()
        
        assert result == {}
    
    def test_context_manager(self):
        """컨텍스트 매니저 테스트"""
        context = LogContext()
        
        context.set_context(global_key="global_value")
        
        with context.context(temp_key="temp_value"):
            result = context.get_context()
            assert result["global_key"] == "global_value"
            assert result["temp_key"] == "temp_value"
        
        # 컨텍스트 매니저 종료 후 원래 상태로 복원
        result = context.get_context()
        assert result["global_key"] == "global_value"
        assert "temp_key" not in result


class TestStructuredFormatter:
    """StructuredFormatter 클래스 테스트"""
    
    def test_basic_formatting(self):
        """기본 포맷팅 테스트"""
        formatter = StructuredFormatter()
        
        # LogRecord 생성
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test"
        assert log_data["line"] == 10
        assert "timestamp" in log_data
    
    def test_formatting_with_context(self):
        """컨텍스트 정보가 포함된 포맷팅 테스트"""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"test_name": "test_login", "browser": "chrome"}
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "context" in log_data
        assert log_data["context"]["test_name"] == "test_login"
        assert log_data["context"]["browser"] == "chrome"


class TestConsoleFormatter:
    """ConsoleFormatter 클래스 테스트"""
    
    def test_basic_console_formatting(self):
        """기본 콘솔 포맷팅 테스트"""
        formatter = ConsoleFormatter(use_colors=False)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        assert "INFO" in result
        assert "test_logger" in result
        assert "Test message" in result
        assert "[" in result  # 타임스탬프 브래킷


class TestTestLogger:
    """TestLogger 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.logger = TestLogger("test_logger")
        # 기본 핸들러 제거 (테스트 출력 방지)
        self.logger.remove_handler('console')
    
    def test_logger_initialization(self):
        """로거 초기화 테스트"""
        logger = TestLogger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger.logger.name == "test_logger"
        assert isinstance(logger.context, LogContext)
    
    def test_set_level(self):
        """로그 레벨 설정 테스트"""
        self.logger.set_level(LogLevel.ERROR)
        assert self.logger.logger.level == logging.ERROR
        
        self.logger.set_level("DEBUG")
        assert self.logger.logger.level == logging.DEBUG
    
    def test_add_and_remove_handler(self):
        """핸들러 추가 및 제거 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        
        self.logger.add_handler("test_handler", mock_handler)
        assert "test_handler" in self.logger._handlers
        
        self.logger.remove_handler("test_handler")
        assert "test_handler" not in self.logger._handlers
    
    def test_basic_logging_methods(self):
        """기본 로깅 메서드 테스트"""
        # 실제 핸들러 사용 (출력 없이)
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        self.logger.add_handler("test", handler)
        
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        output = stream.getvalue()
        assert "Debug message" in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output
        assert "Critical message" in output
    
    def test_log_test_start_end(self):
        """테스트 시작/종료 로깅 테스트"""
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        self.logger.add_handler("test", handler)
        
        self.logger.log_test_start("test_login", "LoginTest")
        self.logger.log_test_end("test_login", "PASSED", 1.5)
        
        output = stream.getvalue()
        assert "테스트 시작: test_login" in output
        assert "테스트 종료: test_login - PASSED" in output
    
    def test_log_exception_framework(self):
        """프레임워크 예외 로깅 테스트"""
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        self.logger.add_handler("test", handler)
        
        exception = TestFrameworkException("Test error", error_code="TEST_001")
        self.logger.log_exception(exception)
        
        output = stream.getvalue()
        assert "프레임워크 예외 발생: Test error" in output
    
    def test_test_context_manager_success(self):
        """테스트 컨텍스트 매니저 성공 케이스"""
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        self.logger.add_handler("test", handler)
        
        with self.logger.test_context("test_login", "LoginTest"):
            pass  # 성공적으로 완료
        
        output = stream.getvalue()
        assert "테스트 시작: test_login" in output
        assert "테스트 종료: test_login - PASSED" in output
    
    def test_test_context_manager_failure(self):
        """테스트 컨텍스트 매니저 실패 케이스"""
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        self.logger.add_handler("test", handler)
        
        with pytest.raises(ValueError):
            with self.logger.test_context("test_login", "LoginTest"):
                raise ValueError("Test failed")
        
        output = stream.getvalue()
        assert "테스트 시작: test_login" in output
        assert "테스트 종료: test_login - FAILED" in output
        assert "예외 발생: Test failed" in output


class TestGlobalFunctions:
    """전역 함수들 테스트"""
    
    def test_get_logger_singleton(self):
        """get_logger 싱글톤 테스트"""
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
    
    def test_get_logger_with_name(self):
        """이름을 지정한 get_logger 테스트"""
        logger1 = get_logger("custom_logger")
        logger2 = get_logger("custom_logger")
        
        assert logger1 is logger2
        assert logger1.name == "custom_logger"
    
    def test_setup_logging_basic(self):
        """setup_logging 기본 테스트"""
        logger = setup_logging(
            log_dir="test_logs",
            log_level=LogLevel.DEBUG,
            enable_file_logging=False,  # 파일 로깅 비활성화
            enable_structured_logging=True
        )
        
        assert isinstance(logger, TestLogger)
        assert logger.logger.level == logging.DEBUG


class TestIntegration:
    """통합 테스트"""
    
    def test_basic_logging_flow(self):
        """기본 로깅 플로우 테스트"""
        logger = TestLogger("integration_test")
        logger.remove_handler('console')  # 콘솔 출력 제거
        
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        logger.add_handler("test", handler)
        
        # 테스트 실행 시뮬레이션
        with logger.test_context("integration_test", "IntegrationTest"):
            logger.log_driver_action("initialize", browser="chrome")
            
            with logger.step_context("navigate_to_page"):
                logger.log_page_action("HomePage", "navigate", url="https://example.com")
            
            logger.log_assertion("text_equals", "Welcome", "Welcome", True)
        
        output = stream.getvalue()
        
        # 로그 내용 확인
        assert "테스트 시작: integration_test" in output
        assert "드라이버 액션: initialize" in output
        assert "스텝 실행: navigate_to_page" in output
        assert "페이지 액션: HomePage.navigate" in output
        assert "어서션 text_equals: 성공" in output
        assert "테스트 종료: integration_test - PASSED" in output