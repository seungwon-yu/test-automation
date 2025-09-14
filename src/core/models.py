"""
데이터 모델 클래스들
테스트 결과, 설정, 성능 메트릭 등을 관리하는 데이터클래스들을 정의합니다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, Field


class TestStatus(Enum):
    """테스트 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class BrowserType(Enum):
    """지원하는 브라우저 타입"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    page_load_time: float = 0.0
    dom_content_loaded: float = 0.0
    first_contentful_paint: float = 0.0
    largest_contentful_paint: float = 0.0
    cumulative_layout_shift: float = 0.0
    time_to_interactive: float = 0.0
    
    def __post_init__(self):
        """데이터 검증"""
        if self.page_load_time < 0:
            raise ValueError("페이지 로딩 시간은 0 이상이어야 합니다")
        if self.cumulative_layout_shift < 0:
            raise ValueError("CLS는 0 이상이어야 합니다")


@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    test_name: str
    status: TestStatus
    duration: float
    browser: str
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    test_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.test_name.strip():
            raise ValueError("테스트 이름은 비어있을 수 없습니다")
        if self.duration < 0:
            raise ValueError("테스트 실행 시간은 0 이상이어야 합니다")
        if not self.browser.strip():
            raise ValueError("브라우저 정보는 비어있을 수 없습니다")
    
    @property
    def is_success(self) -> bool:
        """테스트 성공 여부"""
        return self.status == TestStatus.PASSED
    
    @property
    def is_failure(self) -> bool:
        """테스트 실패 여부"""
        return self.status in [TestStatus.FAILED, TestStatus.ERROR]


class BrowserConfig(BaseModel):
    """브라우저 설정 클래스 (Pydantic 모델)"""
    browser_type: BrowserType
    headless: bool = True
    window_width: int = Field(default=1920, ge=800, le=3840)
    window_height: int = Field(default=1080, ge=600, le=2160)
    implicit_wait: int = Field(default=10, ge=1, le=60)
    page_load_timeout: int = Field(default=30, ge=5, le=120)
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    download_dir: Optional[str] = None
    
    @validator('proxy')
    def validate_proxy(cls, v):
        """프록시 URL 검증"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('프록시 URL은 http:// 또는 https://로 시작해야 합니다')
        return v
    
    class Config:
        use_enum_values = True


class TestConfig(BaseModel):
    """테스트 설정 클래스 (Pydantic 모델)"""
    base_url: str = Field(..., pattern=r'^https?://.+')
    environment: str = Field(default="development", pattern=r'^(development|staging|production)$')
    browser_config: BrowserConfig
    parallel_workers: int = Field(default=1, ge=1, le=10)
    screenshot_on_failure: bool = True
    performance_monitoring: bool = False
    retry_count: int = Field(default=0, ge=0, le=5)
    test_data_cleanup: bool = True
    report_formats: List[str] = Field(default=["html"], min_items=1)
    
    @validator('report_formats')
    def validate_report_formats(cls, v):
        """리포트 형식 검증"""
        valid_formats = ['html', 'json', 'allure', 'junit']
        for format_type in v:
            if format_type not in valid_formats:
                raise ValueError(f'지원하지 않는 리포트 형식: {format_type}')
        return v
    
    class Config:
        use_enum_values = True


@dataclass
class TestSummary:
    """테스트 실행 요약 데이터 클래스"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    start_time: datetime
    end_time: datetime
    environment: str
    browser: str
    
    def __post_init__(self):
        """데이터 검증"""
        if self.total_tests < 0:
            raise ValueError("총 테스트 수는 0 이상이어야 합니다")
        if self.end_time < self.start_time:
            raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다")
    
    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def failure_rate(self) -> float:
        """실패율 계산"""
        if self.total_tests == 0:
            return 0.0
        return ((self.failed_tests + self.error_tests) / self.total_tests) * 100


# 유틸리티 함수들
def create_test_result(test_name: str, status: TestStatus, duration: float, 
                      browser: str, **kwargs) -> TestResult:
    """TestResult 객체 생성 헬퍼 함수"""
    return TestResult(
        test_name=test_name,
        status=status,
        duration=duration,
        browser=browser,
        **kwargs
    )


def create_browser_config(browser_type: BrowserType, **kwargs) -> BrowserConfig:
    """BrowserConfig 객체 생성 헬퍼 함수"""
    return BrowserConfig(browser_type=browser_type, **kwargs)


def create_test_config(base_url: str, browser_config: BrowserConfig, **kwargs) -> TestConfig:
    """TestConfig 객체 생성 헬퍼 함수"""
    return TestConfig(base_url=base_url, browser_config=browser_config, **kwargs)