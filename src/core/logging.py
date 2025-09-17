"""
구조화된 로깅 시스템
테스트 실행 과정에서 발생하는 모든 이벤트를 체계적으로 기록하는 로깅 시스템입니다.
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path
import threading
from contextlib import contextmanager

from .exceptions import TestFrameworkException


class LogLevel(Enum):
    """로그 레벨 정의"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """문자열로부터 LogLevel 생성"""
        try:
            return cls(level_str.upper())
        except ValueError:
            return cls.INFO


class LogContext:
    """로그 컨텍스트 관리 클래스"""
    
    def __init__(self):
        self._context = threading.local()
    
    def set_context(self, **kwargs):
        """컨텍스트 설정"""
        if not hasattr(self._context, 'data'):
            self._context.data = {}
        self._context.data.update(kwargs)
    
    def get_context(self) -> Dict[str, Any]:
        """현재 컨텍스트 반환"""
        if not hasattr(self._context, 'data'):
            return {}
        return self._context.data.copy()
    
    def clear_context(self):
        """컨텍스트 초기화"""
        if hasattr(self._context, 'data'):
            self._context.data.clear()
    
    @contextmanager
    def context(self, **kwargs):
        """임시 컨텍스트 매니저"""
        old_context = self.get_context()
        try:
            self.set_context(**kwargs)
            yield
        finally:
            self.clear_context()
            self.set_context(**old_context)


class StructuredFormatter(logging.Formatter):
    """구조화된 로그 포맷터"""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 구조화된 형태로 포맷"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # 추가 속성들 포함
        extra_attrs = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                extra_attrs[key] = value
        
        if extra_attrs:
            log_data['extra'] = extra_attrs
        
        # 컨텍스트 정보 추가
        if self.include_context and hasattr(record, 'context'):
            log_data['context'] = record.context
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """콘솔용 컬러 포맷터"""
    
    # ANSI 컬러 코드
    COLORS = {
        'DEBUG': '\033[36m',      # 청록색
        'INFO': '\033[32m',       # 녹색
        'WARNING': '\033[33m',    # 노란색
        'ERROR': '\033[31m',      # 빨간색
        'CRITICAL': '\033[35m',   # 자주색
        'RESET': '\033[0m'        # 리셋
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """콘솔용 포맷"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        level = record.levelname
        
        if self.use_colors:
            color = self.COLORS.get(level, '')
            reset = self.COLORS['RESET']
            level = f"{color}{level}{reset}"
        
        message = record.getMessage()
        
        # 기본 포맷
        formatted = f"[{timestamp}] {level:8} | {record.name:15} | {message}"
        
        # 컨텍스트 정보 추가
        if hasattr(record, 'context') and record.context:
            context_str = " | ".join([f"{k}={v}" for k, v in record.context.items()])
            formatted += f" | {context_str}"
        
        # 예외 정보 추가
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class TestLogger:
    """메인 테스트 로거 클래스"""
    
    def __init__(self, name: str = "TestFramework"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.context = LogContext()
        self._handlers = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """기본 핸들러 설정"""
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ConsoleFormatter())
        console_handler.setLevel(logging.INFO)
        self.add_handler('console', console_handler)
    
    def add_handler(self, name: str, handler: logging.Handler):
        """핸들러 추가"""
        if name in self._handlers:
            self.logger.removeHandler(self._handlers[name])
        
        self._handlers[name] = handler
        self.logger.addHandler(handler)
    
    def remove_handler(self, name: str):
        """핸들러 제거"""
        if name in self._handlers:
            self.logger.removeHandler(self._handlers[name])
            del self._handlers[name]
    
    def set_level(self, level: Union[LogLevel, str]):
        """로그 레벨 설정"""
        if isinstance(level, str):
            level = LogLevel.from_string(level)
        
        log_level = getattr(logging, level.value)
        self.logger.setLevel(log_level)
    
    def add_file_handler(self, file_path: str, level: LogLevel = LogLevel.DEBUG, 
                        structured: bool = True):
        """파일 핸들러 추가"""
        # 디렉토리 생성
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        file_handler.setLevel(getattr(logging, level.value))
        self.add_handler(f'file_{Path(file_path).stem}', file_handler)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """컨텍스트와 함께 로그 기록"""
        # 현재 컨텍스트 가져오기
        context = self.context.get_context()
        context.update(kwargs)
        
        # LogRecord에 컨텍스트 추가
        extra = {'context': context} if context else {}
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """정보 로그"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """에러 로그"""
        if exception:
            self.logger.error(message, exc_info=exception, extra={'context': kwargs})
        else:
            self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """치명적 에러 로그"""
        if exception:
            self.logger.critical(message, exc_info=exception, extra={'context': kwargs})
        else:
            self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def log_test_start(self, test_name: str, test_class: str = None, **kwargs):
        """테스트 시작 로그"""
        context = {'test_name': test_name, 'event': 'test_start'}
        if test_class:
            context['test_class'] = test_class
        context.update(kwargs)
        
        self.info(f"테스트 시작: {test_name}", **context)
    
    def log_test_end(self, test_name: str, result: str, duration: float = None, **kwargs):
        """테스트 종료 로그"""
        context = {
            'test_name': test_name, 
            'event': 'test_end', 
            'result': result
        }
        if duration is not None:
            context['duration'] = duration
        context.update(kwargs)
        
        level_method = self.info if result == 'PASSED' else self.error
        level_method(f"테스트 종료: {test_name} - {result}", **context)
    
    def log_step(self, step_name: str, step_type: str = 'action', **kwargs):
        """테스트 스텝 로그"""
        context = {
            'step_name': step_name,
            'step_type': step_type,
            'event': 'test_step'
        }
        context.update(kwargs)
        
        self.info(f"스텝 실행: {step_name}", **context)
    
    def log_assertion(self, assertion_type: str, expected: Any, actual: Any, 
                     result: bool, **kwargs):
        """어서션 로그"""
        context = {
            'assertion_type': assertion_type,
            'expected': str(expected),
            'actual': str(actual),
            'result': result,
            'event': 'assertion'
        }
        context.update(kwargs)
        
        message = f"어서션 {assertion_type}: {'성공' if result else '실패'}"
        level_method = self.info if result else self.error
        level_method(message, **context)
    
    def log_page_action(self, page_name: str, action: str, element: str = None, **kwargs):
        """페이지 액션 로그"""
        context = {
            'page_name': page_name,
            'action': action,
            'event': 'page_action'
        }
        if element:
            context['element'] = element
        context.update(kwargs)
        
        message = f"페이지 액션: {page_name}.{action}"
        if element:
            message += f" on {element}"
        
        self.info(message, **context)
    
    def log_driver_action(self, action: str, browser: str = None, **kwargs):
        """드라이버 액션 로그"""
        context = {
            'action': action,
            'event': 'driver_action'
        }
        if browser:
            context['browser'] = browser
        context.update(kwargs)
        
        self.info(f"드라이버 액션: {action}", **context)
    
    def log_exception(self, exception: Exception, context_info: Dict[str, Any] = None):
        """예외 로그"""
        context = {'event': 'exception'}
        if context_info:
            context.update(context_info)
        
        if isinstance(exception, TestFrameworkException):
            # 프레임워크 예외인 경우 구조화된 정보 사용
            context.update({
                'error_code': exception.error_code,
                'exception_context': exception.context
            })
            
            self.error(f"프레임워크 예외 발생: {exception.message}", 
                      exception=exception, **context)
        else:
            # 일반 예외
            self.error(f"예외 발생: {str(exception)}", exception=exception, **context)
    
    @contextmanager
    def test_context(self, test_name: str, test_class: str = None, **kwargs):
        """테스트 컨텍스트 매니저"""
        context = {'test_name': test_name}
        if test_class:
            context['test_class'] = test_class
        context.update(kwargs)
        
        with self.context.context(**context):
            start_time = datetime.now()
            self.log_test_start(test_name, test_class, **kwargs)
            
            try:
                yield
                duration = (datetime.now() - start_time).total_seconds()
                self.log_test_end(test_name, 'PASSED', duration)
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                self.log_test_end(test_name, 'FAILED', duration)
                self.log_exception(e)
                raise
    
    @contextmanager
    def step_context(self, step_name: str, step_type: str = 'action', **kwargs):
        """스텝 컨텍스트 매니저"""
        context = {'step_name': step_name, 'step_type': step_type}
        context.update(kwargs)
        
        with self.context.context(**context):
            self.log_step(step_name, step_type, **kwargs)
            yield


# 전역 로거 인스턴스
_default_logger = None


def get_logger(name: str = None) -> TestLogger:
    """기본 로거 인스턴스 반환"""
    global _default_logger
    
    if _default_logger is None or (name and _default_logger.name != name):
        _default_logger = TestLogger(name or "TestFramework")
    
    return _default_logger


def setup_logging(log_dir: str = "logs", log_level: LogLevel = LogLevel.INFO,
                 enable_file_logging: bool = True, enable_structured_logging: bool = True):
    """로깅 시스템 초기 설정"""
    logger = get_logger()
    logger.set_level(log_level)
    
    if enable_file_logging:
        # 일반 로그 파일
        log_file = os.path.join(log_dir, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logger.add_file_handler(log_file, LogLevel.DEBUG, structured=enable_structured_logging)
        
        # 에러 전용 로그 파일
        error_log_file = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter() if enable_structured_logging 
                                 else logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.add_handler('error_file', error_handler)
    
    return logger


# 편의 함수들
def debug(message: str, **kwargs):
    """전역 디버그 로그"""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """전역 정보 로그"""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs):
    """전역 경고 로그"""
    get_logger().warning(message, **kwargs)


def error(message: str, exception: Optional[Exception] = None, **kwargs):
    """전역 에러 로그"""
    get_logger().error(message, exception=exception, **kwargs)


def critical(message: str, exception: Optional[Exception] = None, **kwargs):
    """전역 치명적 에러 로그"""
    get_logger().critical(message, exception=exception, **kwargs)