"""
데이터 모델 클래스들의 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.core.models import (
    TestResult, TestConfig, PerformanceMetrics, BrowserConfig, TestSummary,
    TestStatus, BrowserType,
    create_test_result, create_browser_config, create_test_config
)


class TestPerformanceMetrics:
    """PerformanceMetrics 클래스 테스트"""
    
    def test_valid_performance_metrics(self):
        """정상적인 성능 메트릭 생성 테스트"""
        metrics = PerformanceMetrics(
            page_load_time=2.5,
            dom_content_loaded=1.8,
            first_contentful_paint=1.2,
            largest_contentful_paint=2.1,
            cumulative_layout_shift=0.05,
            time_to_interactive=3.0
        )
        
        assert metrics.page_load_time == 2.5
        assert metrics.dom_content_loaded == 1.8
        assert metrics.cumulative_layout_shift == 0.05
    
    def test_default_values(self):
        """기본값 테스트"""
        metrics = PerformanceMetrics()
        
        assert metrics.page_load_time == 0.0
        assert metrics.dom_content_loaded == 0.0
        assert metrics.cumulative_layout_shift == 0.0
    
    def test_negative_page_load_time_raises_error(self):
        """음수 페이지 로딩 시간 검증"""
        with pytest.raises(ValueError, match="페이지 로딩 시간은 0 이상이어야 합니다"):
            PerformanceMetrics(page_load_time=-1.0)
    
    def test_negative_cls_raises_error(self):
        """음수 CLS 검증"""
        with pytest.raises(ValueError, match="CLS는 0 이상이어야 합니다"):
            PerformanceMetrics(cumulative_layout_shift=-0.1)


class TestTestResult:
    """TestResult 클래스 테스트"""
    
    def test_valid_test_result(self):
        """정상적인 테스트 결과 생성 테스트"""
        result = TestResult(
            test_name="test_login",
            status=TestStatus.PASSED,
            duration=5.2,
            browser="chrome"
        )
        
        assert result.test_name == "test_login"
        assert result.status == TestStatus.PASSED
        assert result.duration == 5.2
        assert result.browser == "chrome"
        assert isinstance(result.timestamp, datetime)
        assert result.is_success is True
        assert result.is_failure is False
    
    def test_failed_test_result(self):
        """실패한 테스트 결과 테스트"""
        result = TestResult(
            test_name="test_payment",
            status=TestStatus.FAILED,
            duration=3.1,
            browser="firefox",
            error_message="Element not found"
        )
        
        assert result.status == TestStatus.FAILED
        assert result.error_message == "Element not found"
        assert result.is_success is False
        assert result.is_failure is True
    
    def test_empty_test_name_raises_error(self):
        """빈 테스트 이름 검증"""
        with pytest.raises(ValueError, match="테스트 이름은 비어있을 수 없습니다"):
            TestResult(
                test_name="",
                status=TestStatus.PASSED,
                duration=1.0,
                browser="chrome"
            )
    
    def test_negative_duration_raises_error(self):
        """음수 실행 시간 검증"""
        with pytest.raises(ValueError, match="테스트 실행 시간은 0 이상이어야 합니다"):
            TestResult(
                test_name="test_example",
                status=TestStatus.PASSED,
                duration=-1.0,
                browser="chrome"
            )
    
    def test_empty_browser_raises_error(self):
        """빈 브라우저 정보 검증"""
        with pytest.raises(ValueError, match="브라우저 정보는 비어있을 수 없습니다"):
            TestResult(
                test_name="test_example",
                status=TestStatus.PASSED,
                duration=1.0,
                browser=""
            )
    
    def test_with_performance_metrics(self):
        """성능 메트릭이 포함된 테스트 결과"""
        metrics = PerformanceMetrics(page_load_time=2.5)
        result = TestResult(
            test_name="test_performance",
            status=TestStatus.PASSED,
            duration=3.0,
            browser="chrome",
            performance_metrics=metrics
        )
        
        assert result.performance_metrics is not None
        assert result.performance_metrics.page_load_time == 2.5


class TestBrowserConfig:
    """BrowserConfig 클래스 테스트"""
    
    def test_valid_browser_config(self):
        """정상적인 브라우저 설정 생성 테스트"""
        config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            headless=True,
            window_width=1920,
            window_height=1080
        )
        
        assert config.browser_type == BrowserType.CHROME.value
        assert config.headless is True
        assert config.window_width == 1920
        assert config.window_height == 1080
        assert config.implicit_wait == 10  # 기본값
    
    def test_default_values(self):
        """기본값 테스트"""
        config = BrowserConfig(browser_type=BrowserType.FIREFOX)
        
        assert config.headless is True
        assert config.window_width == 1920
        assert config.window_height == 1080
        assert config.implicit_wait == 10
        assert config.page_load_timeout == 30
    
    def test_invalid_window_size_raises_error(self):
        """잘못된 윈도우 크기 검증"""
        with pytest.raises(ValidationError):
            BrowserConfig(
                browser_type=BrowserType.CHROME,
                window_width=500  # 최소값 800보다 작음
            )
    
    def test_invalid_proxy_url_raises_error(self):
        """잘못된 프록시 URL 검증"""
        with pytest.raises(ValidationError, match="프록시 URL은 http://"):
            BrowserConfig(
                browser_type=BrowserType.CHROME,
                proxy="invalid-proxy-url"
            )
    
    def test_valid_proxy_url(self):
        """정상적인 프록시 URL 테스트"""
        config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            proxy="http://proxy.example.com:8080"
        )
        
        assert config.proxy == "http://proxy.example.com:8080"


class TestTestConfig:
    """TestConfig 클래스 테스트"""
    
    def test_valid_test_config(self):
        """정상적인 테스트 설정 생성 테스트"""
        browser_config = BrowserConfig(browser_type=BrowserType.CHROME)
        config = TestConfig(
            base_url="https://example.com",
            environment="staging",
            browser_config=browser_config,
            parallel_workers=2
        )
        
        assert config.base_url == "https://example.com"
        assert config.environment == "staging"
        assert config.parallel_workers == 2
        assert config.screenshot_on_failure is True  # 기본값
    
    def test_invalid_base_url_raises_error(self):
        """잘못된 base URL 검증"""
        browser_config = BrowserConfig(browser_type=BrowserType.CHROME)
        
        with pytest.raises(ValidationError):
            TestConfig(
                base_url="invalid-url",
                browser_config=browser_config
            )
    
    def test_invalid_environment_raises_error(self):
        """잘못된 환경 설정 검증"""
        browser_config = BrowserConfig(browser_type=BrowserType.CHROME)
        
        with pytest.raises(ValidationError):
            TestConfig(
                base_url="https://example.com",
                environment="invalid-env",
                browser_config=browser_config
            )
    
    def test_invalid_report_format_raises_error(self):
        """잘못된 리포트 형식 검증"""
        browser_config = BrowserConfig(browser_type=BrowserType.CHROME)
        
        with pytest.raises(ValidationError, match="지원하지 않는 리포트 형식"):
            TestConfig(
                base_url="https://example.com",
                browser_config=browser_config,
                report_formats=["invalid-format"]
            )
    
    def test_valid_report_formats(self):
        """정상적인 리포트 형식 테스트"""
        browser_config = BrowserConfig(browser_type=BrowserType.CHROME)
        config = TestConfig(
            base_url="https://example.com",
            browser_config=browser_config,
            report_formats=["html", "json", "allure"]
        )
        
        assert "html" in config.report_formats
        assert "json" in config.report_formats
        assert "allure" in config.report_formats


class TestTestSummary:
    """TestSummary 클래스 테스트"""
    
    def test_valid_test_summary(self):
        """정상적인 테스트 요약 생성 테스트"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        summary = TestSummary(
            total_tests=10,
            passed_tests=8,
            failed_tests=1,
            skipped_tests=1,
            error_tests=0,
            total_duration=300.0,
            start_time=start_time,
            end_time=end_time,
            environment="staging",
            browser="chrome"
        )
        
        assert summary.total_tests == 10
        assert summary.passed_tests == 8
        assert summary.success_rate == 80.0
        assert summary.failure_rate == 10.0
    
    def test_zero_tests_summary(self):
        """테스트가 없는 경우의 요약"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        summary = TestSummary(
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            error_tests=0,
            total_duration=0.0,
            start_time=start_time,
            end_time=end_time,
            environment="development",
            browser="firefox"
        )
        
        assert summary.success_rate == 0.0
        assert summary.failure_rate == 0.0
    
    def test_negative_total_tests_raises_error(self):
        """음수 총 테스트 수 검증"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        with pytest.raises(ValueError, match="총 테스트 수는 0 이상이어야 합니다"):
            TestSummary(
                total_tests=-1,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                total_duration=0.0,
                start_time=start_time,
                end_time=end_time,
                environment="development",
                browser="chrome"
            )
    
    def test_invalid_time_range_raises_error(self):
        """잘못된 시간 범위 검증"""
        start_time = datetime.now()
        end_time = start_time - timedelta(seconds=1)  # 종료 시간이 시작 시간보다 빠름
        
        with pytest.raises(ValueError, match="종료 시간은 시작 시간보다 늦어야 합니다"):
            TestSummary(
                total_tests=1,
                passed_tests=1,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                total_duration=1.0,
                start_time=start_time,
                end_time=end_time,
                environment="development",
                browser="chrome"
            )


class TestHelperFunctions:
    """헬퍼 함수들 테스트"""
    
    def test_create_test_result(self):
        """create_test_result 헬퍼 함수 테스트"""
        result = create_test_result(
            test_name="test_helper",
            status=TestStatus.PASSED,
            duration=2.0,
            browser="chrome",
            error_message="No error"
        )
        
        assert isinstance(result, TestResult)
        assert result.test_name == "test_helper"
        assert result.error_message == "No error"
    
    def test_create_browser_config(self):
        """create_browser_config 헬퍼 함수 테스트"""
        config = create_browser_config(
            browser_type=BrowserType.FIREFOX,
            headless=False,
            window_width=1366
        )
        
        assert isinstance(config, BrowserConfig)
        assert config.browser_type == BrowserType.FIREFOX.value
        assert config.headless is False
        assert config.window_width == 1366
    
    def test_create_test_config(self):
        """create_test_config 헬퍼 함수 테스트"""
        browser_config = create_browser_config(BrowserType.CHROME)
        config = create_test_config(
            base_url="https://test.example.com",
            browser_config=browser_config,
            environment="production"
        )
        
        assert isinstance(config, TestConfig)
        assert config.base_url == "https://test.example.com"
        assert config.environment == "production"
        assert config.browser_config.browser_type == BrowserType.CHROME.value