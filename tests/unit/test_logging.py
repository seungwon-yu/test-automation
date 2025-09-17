"""
구조화된 로깅 시스템의 단위 테스트
"""

import pytest
import json
import logging
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.core.logging import (
    LogLevel, LogContext, StructuredFormatter, ConsoleFormatter,
    TestLogger, get_logger, setup_logging,
    debug, info, warning, error, critical
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
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("critical") == LogLevel.CRITICAL
    
    def test_from_string_invalid(self):
        """잘못된 문자열로부터 LogLevel 생성 테스트"""
        assert LogLevel.from_string("invalid") == LogLevel.INFO
        assert LogLevel.from_string("") == LogLevel.INFO
        assert LogLevel.from_string("TRACE") == LogLevel.INFO


class TestLogContext:
    """LogContext 클래스 테스트"""
    
    def test_set_and_get_context(self):
        """컨텍스트 설정 및 조회 테스트"""
        context = LogContext()
        
        context.set_context(test_name="test_login", browser="chrome")
        result = context.get_context()
        
        assert result["test_name"] == "test_login"
        assert result["browser"] == "chrome"
    
    def test_update_context(self):
        """컨텍스트 업데이트 테스트"""
        context = LogContext()
        
        context.set_context(test_name="test_login")
        context.set_context(browser="chrome", timeout=30)
        result = context.get_context()
        
        assert result["test_name"] == "test_login"
        assert result["browser"] == "chrome"
        assert result["timeout"] == 30
    
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
    
    def test_empty_context_manager(self):
        """빈 컨텍스트에서 컨텍스트 매니저 테스트"""
        context = LogContext()
        
        with context.context(temp_key="temp_value"):
            result = context.get_context()
            assert result["temp_key"] == "temp_value"
        
        result = context.get_context()
        assert result == {}


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
    
    def test_formatting_with_exception(self):
        """예외 정보가 포함된 포맷팅 테스트"""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"
        assert "traceback" in log_data["exception"]
    
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
    
    def test_formatting_with_extra_attributes(self):
        """추가 속성이 포함된 포맷팅 테스트"""
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
        record.custom_attr = "custom_value"
        record.test_id = 12345
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "extra" in log_data
        assert log_data["extra"]["custom_attr"] == "custom_value"
        assert log_data["extra"]["test_id"] == 12345


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
    
    def test_console_formatting_with_context(self):
        """컨텍스트가 포함된 콘솔 포맷팅 테스트"""
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
        record.context = {"test_name": "test_login", "step": "click_button"}
        
        result = formatter.format(record)
        
        assert "test_name=test_login" in result
        assert "step=click_button" in result
    
    def test_console_formatting_with_exception(self):
        """예외가 포함된 콘솔 포맷팅 테스트"""
        formatter = ConsoleFormatter(use_colors=False)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        result = formatter.format(record)
        
        assert "Error occurred" in result
        assert "ValueError" in result
        assert "Test exception" in result


class TestTestLogger:
    """TestLogger 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.logger = TestLogger("test_logger")
        # 기본 핸들러 제거 (테스트 출력 방지)
        self.logger.remove_handler('console')
    
    def create_mock_handler(self):
        """Mock 핸들러 생성 헬퍼"""
        mock_handler = Mock(spec=logging.Handler)
        mock_handler.level = logging.DEBUG
        return mock_handler
    
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
        mock_handler = self.create_mock_handler()
        
        self.logger.add_handler("test_handler", mock_handler)
        assert "test_handler" in self.logger._handlers
        
        self.logger.remove_handler("test_handler")
        assert "test_handler" not in self.logger._handlers
    
    def test_add_file_handler(self):
        """파일 핸들러 추가 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            self.logger.add_file_handler(log_file, LogLevel.INFO, structured=True)
            
            # 핸들러가 추가되었는지 확인
            assert f"file_test" in self.logger._handlers
            
            # 파일 핸들러 정리
            self.logger.remove_handler("file_test")
    
    def test_basic_logging_methods(self):
        """기본 로깅 메서드 테스트"""
        mock_handler = self.create_mock_handler()
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        # 핸들러가 호출되었는지 확인
        assert mock_handler.handle.call_count == 5
    
    def test_logging_with_context(self):
        """컨텍스트와 함께 로깅 테스트"""
        mock_handler = self.create_mock_handler()
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.context.set_context(test_name="test_login")
        self.logger.info("Test message", browser="chrome")
        
        # 핸들러가 호출되었는지 확인
        mock_handler.handle.assert_called_once()
        
        # 로그 레코드에 컨텍스트가 포함되었는지 확인
        call_args = mock_handler.handle.call_args[0][0]
        assert hasattr(call_args, 'context')
        assert call_args.context['test_name'] == "test_login"
        assert call_args.context['browser'] == "chrome"
    
    def test_log_test_start_end(self):
        """테스트 시작/종료 로깅 테스트"""
        mock_handler = self.create_mock_handler()
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.log_test_start("test_login", "LoginTest")
        self.logger.log_test_end("test_login", "PASSED", 1.5)
        
        assert mock_handler.handle.call_count == 2
        
        # 첫 번째 호출 (시작)
        start_record = mock_handler.handle.call_args_list[0][0][0]
        assert "테스트 시작" in start_record.getMessage()
        assert start_record.context['event'] == 'test_start'
        
        # 두 번째 호출 (종료)
        end_record = mock_handler.handle.call_args_list[1][0][0]
        assert "테스트 종료" in end_record.getMessage()
        assert end_record.context['event'] == 'test_end'
        assert end_record.context['result'] == 'PASSED'
        assert end_record.context['duration'] == 1.5
    
    def test_log_step(self):
        """스텝 로깅 테스트"""
        mock_handler = self.create_mock_handler()
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.log_step("click_login_button", "action", element="#login-btn")
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "스텝 실행" in record.getMessage()
        assert record.context['step_name'] == "click_login_button"
        assert record.context['step_type'] == "action"
        assert record.context['element'] == "#login-btn"
    
    def test_log_assertion(self):
        """어서션 로깅 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        # 성공한 어서션
        self.logger.log_assertion("equals", "expected", "expected", True)
        
        # 실패한 어서션
        self.logger.log_assertion("equals", "expected", "actual", False)
        
        assert mock_handler.handle.call_count == 2
        
        # 성공한 어서션 확인
        success_record = mock_handler.handle.call_args_list[0][0][0]
        assert "어서션 equals: 성공" in success_record.getMessage()
        assert success_record.context['result'] is True
        
        # 실패한 어서션 확인
        fail_record = mock_handler.handle.call_args_list[1][0][0]
        assert "어서션 equals: 실패" in fail_record.getMessage()
        assert fail_record.context['result'] is False
    
    def test_log_page_action(self):
        """페이지 액션 로깅 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.log_page_action("LoginPage", "click", "#submit-btn")
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "페이지 액션: LoginPage.click on #submit-btn" in record.getMessage()
        assert record.context['page_name'] == "LoginPage"
        assert record.context['action'] == "click"
        assert record.context['element'] == "#submit-btn"
    
    def test_log_driver_action(self):
        """드라이버 액션 로깅 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        self.logger.log_driver_action("navigate", browser="chrome")
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "드라이버 액션: navigate" in record.getMessage()
        assert record.context['action'] == "navigate"
        assert record.context['browser'] == "chrome"
    
    def test_log_exception_framework(self):
        """프레임워크 예외 로깅 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        exception = TestFrameworkException(
            "Test error",
            error_code="TEST_001"
        )
        
        self.logger.log_exception(exception)
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "프레임워크 예외 발생" in record.getMessage()
        assert record.context['error_code'] == "TEST_001"
    
    def test_log_exception_general(self):
        """일반 예외 로깅 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        exception = ValueError("General error")
        
        self.logger.log_exception(exception)
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "예외 발생: General error" in record.getMessage()
    
    def test_test_context_manager_success(self):
        """테스트 컨텍스트 매니저 성공 케이스"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        with self.logger.test_context("test_login", "LoginTest"):
            pass  # 성공적으로 완료
        
        assert mock_handler.handle.call_count == 2
        
        # 시작 로그
        start_record = mock_handler.handle.call_args_list[0][0][0]
        assert "테스트 시작" in start_record.getMessage()
        
        # 종료 로그
        end_record = mock_handler.handle.call_args_list[1][0][0]
        assert "테스트 종료" in end_record.getMessage()
        assert end_record.context['result'] == 'PASSED'
    
    def test_test_context_manager_failure(self):
        """테스트 컨텍스트 매니저 실패 케이스"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        with pytest.raises(ValueError):
            with self.logger.test_context("test_login", "LoginTest"):
                raise ValueError("Test failed")
        
        assert mock_handler.handle.call_count == 3  # 시작, 종료, 예외
        
        # 종료 로그
        end_record = mock_handler.handle.call_args_list[1][0][0]
        assert end_record.context['result'] == 'FAILED'
        
        # 예외 로그
        exception_record = mock_handler.handle.call_args_list[2][0][0]
        assert "예외 발생" in exception_record.getMessage()
    
    def test_step_context_manager(self):
        """스텝 컨텍스트 매니저 테스트"""
        mock_handler = Mock(spec=logging.Handler)
        self.logger.add_handler("mock", mock_handler)
        
        with self.logger.step_context("click_button", "action"):
            pass
        
        mock_handler.handle.assert_called_once()
        record = mock_handler.handle.call_args[0][0]
        
        assert "스텝 실행: click_button" in record.getMessage()
        assert record.context['step_name'] == "click_button"
        assert record.context['step_type'] == "action"


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
    
    def test_setup_logging(self):
        """setup_logging 함수 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = setup_logging(
                log_dir=temp_dir,
                log_level=LogLevel.DEBUG,
                enable_file_logging=True,
                enable_structured_logging=True
            )
            
            assert isinstance(logger, TestLogger)
            assert logger.logger.level == logging.DEBUG
            
            # 파일 핸들러가 추가되었는지 확인
            handler_names = list(logger._handlers.keys())
            assert any("file_test_" in name for name in handler_names)
            assert any("error_file" in name for name in handler_names)
    
    @patch('src.core.logging.get_logger')
    def test_global_logging_functions(self, mock_get_logger):
        """전역 로깅 함수들 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        debug("Debug message", key="value")
        info("Info message", key="value")
        warning("Warning message", key="value")
        error("Error message", key="value")
        critical("Critical message", key="value")
        
        mock_logger.debug.assert_called_once_with("Debug message", key="value")
        mock_logger.info.assert_called_once_with("Info message", key="value")
        mock_logger.warning.assert_called_once_with("Warning message", key="value")
        mock_logger.error.assert_called_once_with("Error message", exception=None, key="value")
        mock_logger.critical.assert_called_once_with("Critical message", exception=None, key="value")


class TestIntegration:
    """통합 테스트"""
    
    def test_end_to_end_logging_flow(self):
        """전체 로깅 플로우 통합 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 로깅 시스템 설정
            logger = setup_logging(
                log_dir=temp_dir,
                log_level=LogLevel.DEBUG,
                enable_file_logging=True,
                enable_structured_logging=True
            )
            
            # 테스트 실행 시뮬레이션
            with logger.test_context("integration_test", "IntegrationTest"):
                logger.log_driver_action("initialize", browser="chrome")
                
                with logger.step_context("navigate_to_page"):
                    logger.log_page_action("HomePage", "navigate", url="https://example.com")
                
                with logger.step_context("perform_login"):
                    logger.log_page_action("LoginPage", "input", "#username")
                    logger.log_page_action("LoginPage", "input", "#password")
                    logger.log_page_action("LoginPage", "click", "#submit")
                
                logger.log_assertion("text_equals", "Welcome", "Welcome", True)
            
            # 로그 파일이 생성되었는지 확인
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) >= 2  # 일반 로그 + 에러 로그
            
            # 로그 파일 내용 확인
            for log_file in log_files:
                if log_file.stat().st_size > 0:  # 파일에 내용이 있는 경우
                    content = log_file.read_text(encoding='utf-8')
                    assert len(content) > 0
    
    def test_concurrent_logging(self):
        """동시 로깅 테스트"""
        import threading
        import time
        
        logger = TestLogger("concurrent_test")
        results = []
        
        def log_worker(worker_id):
            with logger.test_context(f"test_{worker_id}", "ConcurrentTest"):
                for i in range(5):
                    logger.info(f"Worker {worker_id} - Message {i}")
                    time.sleep(0.01)  # 짧은 대기
                results.append(worker_id)
        
        # 여러 스레드에서 동시 로깅
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 모든 워커가 완료되었는지 확인
        assert len(results) == 3
        assert set(results) == {0, 1, 2}