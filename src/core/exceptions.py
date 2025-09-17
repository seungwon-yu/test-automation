"""
예외 처리 클래스들
테스트 자동화 프레임워크에서 발생할 수 있는 다양한 예외들을 정의합니다.
"""

from typing import Optional, Dict, Any


class TestFrameworkException(Exception):
    """테스트 프레임워크 기본 예외 클래스"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.context = context.copy() if context else {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        error_info = f"[{self.error_code}] " if self.error_code else ""
        return f"{error_info}{self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """예외 정보를 딕셔너리로 변환"""
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class DriverException(TestFrameworkException):
    """드라이버 관련 예외"""
    
    def __init__(self, message: str, browser: Optional[str] = None, 
                 driver_version: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if browser:
            context['browser'] = browser
        if driver_version:
            context['driver_version'] = driver_version
        
        super().__init__(message, kwargs.get('error_code'), context)


class DriverInitializationException(DriverException):
    """드라이버 초기화 실패 예외"""
    
    def __init__(self, browser: str, reason: str, **kwargs):
        message = f"{browser} 드라이버 초기화 실패: {reason}"
        super().__init__(message, browser=browser, 
                        error_code="DRIVER_INIT_FAILED", **kwargs)


class DriverTimeoutException(DriverException):
    """드라이버 타임아웃 예외"""
    
    def __init__(self, operation: str, timeout: int, **kwargs):
        message = f"드라이버 작업 타임아웃: {operation} ({timeout}초)"
        context = kwargs.get('context', {})
        context.update({'operation': operation, 'timeout': timeout})
        super().__init__(message, error_code="DRIVER_TIMEOUT", 
                        context=context, **kwargs)


class PageObjectException(TestFrameworkException):
    """페이지 객체 관련 예외"""
    
    def __init__(self, message: str, page_name: Optional[str] = None, 
                 element_locator: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if page_name:
            context['page_name'] = page_name
        if element_locator:
            context['element_locator'] = element_locator
        
        super().__init__(message, kwargs.get('error_code'), context)


class ElementNotFoundException(PageObjectException):
    """요소를 찾을 수 없는 예외"""
    
    def __init__(self, locator: str, page_name: Optional[str] = None, 
                 timeout: Optional[int] = None, **kwargs):
        message = f"요소를 찾을 수 없습니다: {locator}"
        if timeout:
            message += f" (대기시간: {timeout}초)"
        
        context = kwargs.get('context', {})
        context.update({'locator': locator, 'timeout': timeout})
        
        super().__init__(message, page_name=page_name, 
                        element_locator=locator, 
                        error_code="ELEMENT_NOT_FOUND", 
                        context=context, **kwargs)


class ElementNotInteractableException(PageObjectException):
    """요소와 상호작용할 수 없는 예외"""
    
    def __init__(self, locator: str, action: str, page_name: Optional[str] = None, **kwargs):
        message = f"요소와 상호작용할 수 없습니다: {locator} (액션: {action})"
        context = kwargs.get('context', {})
        context.update({'locator': locator, 'action': action})
        
        super().__init__(message, page_name=page_name, 
                        element_locator=locator,
                        error_code="ELEMENT_NOT_INTERACTABLE",
                        context=context, **kwargs)


class PageLoadTimeoutException(PageObjectException):
    """페이지 로딩 타임아웃 예외"""
    
    def __init__(self, url: str, timeout: int, page_name: Optional[str] = None, **kwargs):
        message = f"페이지 로딩 타임아웃: {url} ({timeout}초)"
        context = kwargs.get('context', {})
        context.update({'url': url, 'timeout': timeout})
        
        super().__init__(message, page_name=page_name,
                        error_code="PAGE_LOAD_TIMEOUT",
                        context=context, **kwargs)


class ConfigurationException(TestFrameworkException):
    """설정 관련 예외"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 config_file: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        if config_file:
            context['config_file'] = config_file
        
        super().__init__(message, kwargs.get('error_code'), context)


class InvalidConfigurationException(ConfigurationException):
    """잘못된 설정 예외"""
    
    def __init__(self, config_key: str, value: Any, reason: str, **kwargs):
        message = f"잘못된 설정값: {config_key}={value} ({reason})"
        super().__init__(message, config_key=config_key,
                        error_code="INVALID_CONFIG",
                        context={'value': value, 'reason': reason}, **kwargs)


class MissingConfigurationException(ConfigurationException):
    """필수 설정 누락 예외"""
    
    def __init__(self, config_key: str, config_file: Optional[str] = None, **kwargs):
        message = f"필수 설정이 누락되었습니다: {config_key}"
        if config_file:
            message += f" (파일: {config_file})"
        
        super().__init__(message, config_key=config_key, 
                        config_file=config_file,
                        error_code="MISSING_CONFIG", **kwargs)


class TestDataException(TestFrameworkException):
    """테스트 데��터 관련 예외"""
    
    def __init__(self, message: str, data_type: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if data_type:
            context['data_type'] = data_type
        if operation:
            context['operation'] = operation
        
        super().__init__(message, kwargs.get('error_code'), context)


class TestDataGenerationException(TestDataException):
    """테스트 데이터 생성 실패 예외"""
    
    def __init__(self, data_type: str, reason: str, **kwargs):
        message = f"테스트 데이터 생성 실패: {data_type} ({reason})"
        super().__init__(message, data_type=data_type, operation="generation",
                        error_code="TEST_DATA_GENERATION_FAILED",
                        context={'reason': reason}, **kwargs)


class TestDataCleanupException(TestDataException):
    """테스트 데이터 정리 실패 예외"""
    
    def __init__(self, data_type: str, reason: str, **kwargs):
        message = f"테스트 데이터 정리 실패: {data_type} ({reason})"
        super().__init__(message, data_type=data_type, operation="cleanup",
                        error_code="TEST_DATA_CLEANUP_FAILED",
                        context={'reason': reason}, **kwargs)


class ReportGenerationException(TestFrameworkException):
    """리포트 생성 관련 예외"""
    
    def __init__(self, message: str, report_type: Optional[str] = None, 
                 output_path: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if report_type:
            context['report_type'] = report_type
        if output_path:
            context['output_path'] = output_path
        
        super().__init__(message, kwargs.get('error_code'), context)


class ReportTemplateException(ReportGenerationException):
    """리포트 템플릿 관련 예외"""
    
    def __init__(self, template_name: str, reason: str, **kwargs):
        message = f"리포트 템플릿 오류: {template_name} ({reason})"
        super().__init__(message, error_code="REPORT_TEMPLATE_ERROR",
                        context={'template_name': template_name, 'reason': reason}, **kwargs)


class APIException(TestFrameworkException):
    """API 테스트 관련 예외"""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, 
                 status_code: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        if endpoint:
            context['endpoint'] = endpoint
        if status_code:
            context['status_code'] = status_code
        
        super().__init__(message, kwargs.get('error_code'), context)


class APITimeoutException(APIException):
    """API 타임아웃 예외"""
    
    def __init__(self, endpoint: str, timeout: int, **kwargs):
        message = f"API 요청 타임아웃: {endpoint} ({timeout}초)"
        super().__init__(message, endpoint=endpoint,
                        error_code="API_TIMEOUT",
                        context={'timeout': timeout}, **kwargs)


class APIResponseException(APIException):
    """API 응답 오류 예외"""
    
    def __init__(self, endpoint: str, status_code: int, response_text: str, **kwargs):
        message = f"API 응답 오류: {endpoint} (상태코드: {status_code})"
        super().__init__(message, endpoint=endpoint, status_code=status_code,
                        error_code="API_RESPONSE_ERROR",
                        context={'response_text': response_text}, **kwargs)


# 예외 처리 유틸리티 함수들
def handle_driver_exception(func):
    """드라이버 관련 예외를 처리하는 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "WebDriver" in str(type(e)) or "WebDriver" in e.__class__.__name__:
                raise DriverException(f"드라이버 오류: {str(e)}")
            raise
    return wrapper


def handle_element_exception(func):
    """요소 관련 예외를 처리하는 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if "no such element" in error_msg or "element not found" in error_msg:
                raise ElementNotFoundException("요소를 찾을 수 없습니다")
            elif "element not interactable" in error_msg:
                raise ElementNotInteractableException("요소와 상호작용할 수 없습니다", "unknown")
            raise
    return wrapper


def create_context_dict(**kwargs) -> Dict[str, Any]:
    """컨텍스트 딕셔너리 생성 헬퍼 함수"""
    return {k: v for k, v in kwargs.items() if v is not None}


def format_exception_message(exception: TestFrameworkException) -> str:
    """예외 메시지를 포맷팅하는 함수"""
    message = str(exception)
    if exception.context:
        context_str = ", ".join([f"{k}={v}" for k, v in exception.context.items()])
        message += f" [Context: {context_str}]"
    return message