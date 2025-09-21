"""
Smart Retry 및 Self-healing 시스템 단위 테스트

이 모듈은 retry_manager.py의 모든 클래스와 기능들에 대한
포괄적인 단위 테스트를 제공합니다.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from collections import deque

from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

from src.core.retry_manager import (
    RetryStrategy,
    FailureType,
    RetryConfig,
    FailurePattern,
    AdaptiveMetrics,
    FailurePatternLearner,
    SmartRetryManager,
    DynamicWaitManager,
    smart_retry
)
from src.core.exceptions import TestFrameworkException


class TestRetryConfig:
    """RetryConfig 데이터클래스 테스트"""
    
    def test_retry_config_default_values(self):
        """기본값 확인"""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.jitter is True
        assert config.backoff_multiplier == 2.0
        assert config.timeout == 10.0
        assert config.enable_self_healing is True
        assert config.learning_enabled is True
        assert config.adaptive_timeout is True
        assert config.retry_on_stale_element is True
        assert config.retry_on_timeout is True
        assert config.retry_on_click_intercepted is True
        assert config.retry_on_not_interactable is True
    
    def test_retry_config_custom_values(self):
        """사용자 정의 값 설정"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            strategy=RetryStrategy.FIXED_DELAY,
            jitter=False,
            backoff_multiplier=3.0,
            timeout=20.0,
            enable_self_healing=False,
            learning_enabled=False,
            adaptive_timeout=False,
            retry_on_stale_element=False
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.strategy == RetryStrategy.FIXED_DELAY
        assert config.jitter is False
        assert config.backoff_multiplier == 3.0
        assert config.timeout == 20.0
        assert config.enable_self_healing is False
        assert config.learning_enabled is False
        assert config.adaptive_timeout is False
        assert config.retry_on_stale_element is False


class TestFailurePattern:
    """FailurePattern 데이터클래스 테스트"""
    
    def test_failure_pattern_creation(self):
        """FailurePattern 생성 테스트"""
        pattern = FailurePattern(
            failure_type=FailureType.STALE_ELEMENT,
            locator=(By.ID, "test-element"),
            action="click",
            timestamp=time.time(),
            retry_count=2,
            success_delay=1.5,
            context={"page": "login"}
        )
        
        assert pattern.failure_type == FailureType.STALE_ELEMENT
        assert pattern.locator == (By.ID, "test-element")
        assert pattern.action == "click"
        assert pattern.retry_count == 2
        assert pattern.success_delay == 1.5
        assert pattern.context == {"page": "login"}


class TestAdaptiveMetrics:
    """AdaptiveMetrics 데이터클래스 테스트"""
    
    def test_adaptive_metrics_default_values(self):
        """기본값 확인"""
        metrics = AdaptiveMetrics()
        
        assert isinstance(metrics.success_delays, deque)
        assert metrics.success_delays.maxlen == 100
        assert isinstance(metrics.failure_counts, dict)
        assert metrics.success_rate == 1.0
        assert metrics.avg_success_delay == 1.0
        assert metrics.recommended_timeout == 10.0


class TestFailurePatternLearner:
    """FailurePatternLearner 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.learner = FailurePatternLearner()
    
    def test_learner_initialization(self):
        """학습자 초기화 테스트"""
        assert hasattr(self.learner, 'logger')
        assert hasattr(self.learner, '_patterns')
        assert hasattr(self.learner, '_metrics')
        assert hasattr(self.learner, '_lock')
        assert len(self.learner._patterns) == 0
        assert len(self.learner._metrics) == 0
    
    def test_record_failure(self):
        """실패 패턴 기록 테스트"""
        locator = (By.ID, "test-element")
        action = "click"
        
        self.learner.record_failure(
            FailureType.STALE_ELEMENT,
            locator,
            action,
            retry_count=1,
            context={"page": "login"}
        )
        
        assert len(self.learner._patterns) == 1
        pattern = self.learner._patterns[0]
        assert pattern.failure_type == FailureType.STALE_ELEMENT
        assert pattern.locator == locator
        assert pattern.action == action
        assert pattern.retry_count == 1
        assert pattern.context == {"page": "login"}
        
        # 메트릭 업데이트 확인
        key = self.learner._get_pattern_key(locator, action)
        assert key in self.learner._metrics
        assert self.learner._metrics[key].failure_counts[FailureType.STALE_ELEMENT] == 1
    
    def test_record_success(self):
        """성공 패턴 기록 테스트"""
        locator = (By.ID, "test-element")
        action = "click"
        delay = 1.5
        
        self.learner.record_success(locator, action, delay)
        
        key = self.learner._get_pattern_key(locator, action)
        metrics = self.learner._metrics[key]
        
        assert len(metrics.success_delays) == 1
        assert metrics.success_delays[0] == delay
        assert metrics.avg_success_delay == delay
        assert metrics.success_rate == 1.0
    
    def test_get_recommended_config_no_data(self):
        """데이터가 없을 때 권장 설정 테스트"""
        locator = (By.ID, "unknown-element")
        action = "click"
        
        config = self.learner.get_recommended_config(locator, action)
        
        # 기본 설정이 반환되어야 함
        assert isinstance(config, RetryConfig)
        assert config.max_attempts == 2  # 높은 성공률 기본값
        assert config.base_delay >= 0.5
    
    def test_get_recommended_config_with_data(self):
        """데이터가 있을 때 권장 설정 테스트"""
        locator = (By.ID, "test-element")
        action = "click"
        
        # 실패 패턴 기록
        self.learner.record_failure(FailureType.STALE_ELEMENT, locator, action, 1)
        self.learner.record_failure(FailureType.STALE_ELEMENT, locator, action, 2)
        
        # 성공 패턴 기록
        self.learner.record_success(locator, action, 2.0)
        
        config = self.learner.get_recommended_config(locator, action)
        
        # 낮은 성공률로 인해 재시도 횟수 증가
        assert config.max_attempts >= 3
        assert config.strategy == RetryStrategy.FIXED_DELAY  # STALE_ELEMENT 우세
    
    def test_get_pattern_key(self):
        """패턴 키 생성 테스트"""
        locator = (By.ID, "test-element")
        action = "click"
        
        key = self.learner._get_pattern_key(locator, action)
        
        assert key == "click:id:test-element"
    
    def test_get_dominant_failure_type(self):
        """우세 실패 유형 확인 테스트"""
        failure_counts = {
            FailureType.STALE_ELEMENT: 5,
            FailureType.TIMEOUT: 2,
            FailureType.ELEMENT_NOT_INTERACTABLE: 1
        }
        
        dominant = self.learner._get_dominant_failure_type(failure_counts)
        
        assert dominant == FailureType.STALE_ELEMENT
    
    def test_get_dominant_failure_type_empty(self):
        """빈 실패 카운트에서 우세 유형 테스트"""
        failure_counts = {}
        
        dominant = self.learner._get_dominant_failure_type(failure_counts)
        
        assert dominant == FailureType.UNKNOWN
    
    def test_get_statistics(self):
        """통계 정보 반환 테스트"""
        locator = (By.ID, "test-element")
        action = "click"
        
        # 데이터 추가
        self.learner.record_failure(FailureType.STALE_ELEMENT, locator, action, 1)
        self.learner.record_success(locator, action, 1.0)
        
        stats = self.learner.get_statistics()
        
        assert stats['total_patterns'] == 1
        assert stats['failure_type_distribution'][FailureType.STALE_ELEMENT] == 1
        assert stats['tracked_elements'] == 1
        assert stats['avg_success_rate'] == 0.5  # 1 성공, 1 실패


class TestSmartRetryManager:
    """SmartRetryManager 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.config = RetryConfig(max_attempts=3, base_delay=0.1)  # 빠른 테스트를 위해 짧은 지연
        self.manager = SmartRetryManager(self.mock_driver, self.config)
    
    def test_manager_initialization(self):
        """매니저 초기화 테스트"""
        assert self.manager.driver == self.mock_driver
        assert self.manager.config == self.config
        assert hasattr(self.manager, 'logger')
        assert hasattr(self.manager, '_exception_handlers')
    
    def test_execute_with_retry_success_first_attempt(self):
        """첫 번째 시도에서 성공하는 경우 테스트"""
        mock_func = Mock(return_value="success")
        
        result = self.manager.execute_with_retry(mock_func, "arg1", kwarg1="value1")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_execute_with_retry_success_after_retries(self):
        """재시도 후 성공하는 경우 테스트"""
        mock_func = Mock()
        mock_func.side_effect = [
            StaleElementReferenceException("Stale element"),
            StaleElementReferenceException("Stale element"),
            "success"
        ]
        
        result = self.manager.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_execute_with_retry_all_attempts_fail(self):
        """모든 시도가 실패하는 경우 테스트"""
        mock_func = Mock()
        mock_func.side_effect = StaleElementReferenceException("Persistent failure")
        
        with pytest.raises(TestFrameworkException) as exc_info:
            self.manager.execute_with_retry(mock_func)
        
        assert "Failed to execute" in str(exc_info.value)
        assert mock_func.call_count == 3
    
    def test_classify_failure_stale_element(self):
        """StaleElementException 분류 테스트"""
        exception = StaleElementReferenceException("Stale element")
        
        failure_type = self.manager._classify_failure(exception)
        
        assert failure_type == FailureType.STALE_ELEMENT
    
    def test_classify_failure_timeout(self):
        """TimeoutException 분류 테스트"""
        exception = TimeoutException("Timeout occurred")
        
        failure_type = self.manager._classify_failure(exception)
        
        assert failure_type == FailureType.TIMEOUT
    
    def test_classify_failure_unknown(self):
        """알 수 없는 예외 분류 테스트"""
        exception = ValueError("Unknown error")
        
        failure_type = self.manager._classify_failure(exception)
        
        assert failure_type == FailureType.UNKNOWN
    
    def test_should_retry_stale_element_enabled(self):
        """StaleElement 재시도 활성화 테스트"""
        config = RetryConfig(retry_on_stale_element=True)
        exception = StaleElementReferenceException("Stale element")
        
        should_retry = self.manager._should_retry(exception, config)
        
        assert should_retry is True
    
    def test_should_retry_stale_element_disabled(self):
        """StaleElement 재시도 비활성화 테스트"""
        config = RetryConfig(retry_on_stale_element=False)
        exception = StaleElementReferenceException("Stale element")
        
        should_retry = self.manager._should_retry(exception, config)
        
        assert should_retry is False
    
    def test_calculate_delay_fixed(self):
        """고정 지연 시간 계산 테스트"""
        config = RetryConfig(strategy=RetryStrategy.FIXED_DELAY, base_delay=1.0, jitter=False)
        
        delay1 = self.manager._calculate_delay(0, config)
        delay2 = self.manager._calculate_delay(1, config)
        delay3 = self.manager._calculate_delay(2, config)
        
        assert delay1 == 1.0
        assert delay2 == 1.0
        assert delay3 == 1.0
    
    def test_calculate_delay_exponential(self):
        """지수 백오프 지연 시간 계산 테스트"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False
        )
        
        delay0 = self.manager._calculate_delay(0, config)
        delay1 = self.manager._calculate_delay(1, config)
        delay2 = self.manager._calculate_delay(2, config)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0
    
    def test_calculate_delay_linear(self):
        """선형 백오프 지연 시간 계산 테스트"""
        config = RetryConfig(strategy=RetryStrategy.LINEAR_BACKOFF, base_delay=1.0, jitter=False)
        
        delay0 = self.manager._calculate_delay(0, config)
        delay1 = self.manager._calculate_delay(1, config)
        delay2 = self.manager._calculate_delay(2, config)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 3.0
    
    def test_calculate_delay_max_limit(self):
        """최대 지연 시간 제한 테스트"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=10.0,
            max_delay=5.0,
            jitter=False
        )
        
        delay = self.manager._calculate_delay(5, config)  # 큰 시도 횟수
        
        assert delay == 5.0  # max_delay로 제한됨
    
    def test_calculate_delay_with_jitter(self):
        """지터가 있는 지연 시간 계산 테스트"""
        config = RetryConfig(strategy=RetryStrategy.FIXED_DELAY, base_delay=1.0, jitter=True)
        
        delays = [self.manager._calculate_delay(0, config) for _ in range(10)]
        
        # 지터로 인해 값들이 다양해야 함
        assert len(set(delays)) > 1
        # 모든 값이 합리적인 범위 내에 있어야 함
        assert all(0.8 <= delay <= 1.2 for delay in delays)
    
    @patch('src.core.retry_manager.WebDriverWait')
    def test_handle_stale_element(self, mock_wait):
        """StaleElement 자동 복구 테스트"""
        locator = (By.ID, "test-element")
        exception = StaleElementReferenceException("Stale element")
        
        # WebDriverWait이 성공한다고 가정
        mock_wait.return_value.until.return_value = True
        
        # 예외가 발생하지 않아야 함
        self.manager._handle_stale_element(exception, locator, "click")
        
        mock_wait.assert_called_once()
    
    @patch('src.core.retry_manager.WebDriverWait')
    def test_handle_not_interactable(self, mock_wait):
        """ElementNotInteractable 자동 복구 테스트"""
        locator = (By.ID, "test-element")
        exception = ElementNotInteractableException("Not interactable")
        
        mock_wait.return_value.until.return_value = True
        
        self.manager._handle_not_interactable(exception, locator, "click")
        
        mock_wait.assert_called_once()
    
    def test_handle_click_intercepted(self):
        """ClickIntercepted 자동 복구 테스트"""
        locator = (By.ID, "test-element")
        exception = ElementClickInterceptedException("Click intercepted")
        
        mock_element = Mock()
        self.mock_driver.find_element.return_value = mock_element
        
        # 예외가 발생하지 않아야 함
        self.manager._handle_click_intercepted(exception, locator, "click")
        
        self.mock_driver.find_element.assert_called_with(*locator)
        self.mock_driver.execute_script.assert_called()
    
    @patch('src.core.retry_manager.WebDriverWait')
    def test_handle_timeout(self, mock_wait):
        """Timeout 자동 복구 테스트"""
        locator = (By.ID, "test-element")
        exception = TimeoutException("Timeout occurred")
        
        mock_wait.return_value.until.return_value = True
        
        self.manager._handle_timeout(exception, locator, "click")
        
        mock_wait.assert_called_once()
    
    def test_close_overlays(self):
        """오버레이 닫기 테스트"""
        mock_close_button = Mock()
        mock_close_button.is_displayed.return_value = True
        
        # 첫 번째 셀렉터에서 버튼을 찾는다고 가정
        self.mock_driver.find_element.side_effect = [mock_close_button]
        
        self.manager._close_overlays()
        
        mock_close_button.click.assert_called_once()
    
    def test_merge_configs(self):
        """설정 병합 테스트"""
        base_config = RetryConfig(max_attempts=3, base_delay=1.0, timeout=10.0)
        learned_config = RetryConfig(max_attempts=5, base_delay=2.0, timeout=20.0)
        
        merged = self.manager._merge_configs(base_config, learned_config)
        
        # 학습된 설정이 적용되되 제한 내에서
        assert merged.max_attempts == 5  # min(5, 3+2)
        assert merged.base_delay >= 0.5  # max(1.0*0.5, 2.0)
        assert merged.timeout == 20.0  # min(20.0, 10.0*2)


class TestSmartRetryDecorator:
    """smart_retry 데코레이터 테스트"""
    
    def test_decorator_basic_usage(self):
        """기본 데코레이터 사용 테스트"""
        
        class TestClass:
            def __init__(self):
                self.driver = Mock()
            
            @smart_retry()
            def test_method(self, locator):
                return "success"
        
        test_obj = TestClass()
        result = test_obj.test_method((By.ID, "test"))
        
        assert result == "success"
    
    def test_decorator_with_config(self):
        """설정이 있는 데코레이터 테스트"""
        config = RetryConfig(max_attempts=5)
        
        class TestClass:
            def __init__(self):
                self.driver = Mock()
            
            @smart_retry(config)
            def test_method(self, locator):
                return "success"
        
        test_obj = TestClass()
        result = test_obj.test_method((By.ID, "test"))
        
        assert result == "success"
    
    def test_decorator_no_driver_attribute(self):
        """driver 속성이 없는 경우 테스트"""
        
        class TestClass:
            @smart_retry()
            def test_method(self, locator):
                return "success"
        
        test_obj = TestClass()
        
        with pytest.raises(AttributeError) as exc_info:
            test_obj.test_method((By.ID, "test"))
        
        assert "must have 'driver' attribute" in str(exc_info.value)


class TestDynamicWaitManager:
    """DynamicWaitManager 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.manager = DynamicWaitManager(self.mock_driver)
    
    def test_manager_initialization(self):
        """매니저 초기화 테스트"""
        assert self.manager.driver == self.mock_driver
        assert hasattr(self.manager, 'logger')
        assert hasattr(self.manager, '_performance_history')
        assert hasattr(self.manager, '_base_timeout')
        assert self.manager._base_timeout == 10.0
    
    @patch('src.core.retry_manager.WebDriverWait')
    def test_smart_wait_for_element_success(self, mock_wait):
        """요소 대기 성공 테스트"""
        mock_element = Mock()
        mock_wait.return_value.until.return_value = mock_element
        
        locator = (By.ID, "test-element")
        result = self.manager.smart_wait_for_element(locator, timeout=5.0)
        
        assert result == mock_element
        mock_wait.assert_called_once_with(self.mock_driver, 5.0)
        
        # 성능 기록 확인
        assert len(self.manager._performance_history) == 1
        assert self.manager._performance_history[0]['success'] is True
    
    @patch('src.core.retry_manager.WebDriverWait')
    def test_smart_wait_for_element_timeout(self, mock_wait):
        """요소 대기 타임아웃 테스트"""
        mock_wait.return_value.until.side_effect = TimeoutException("Timeout")
        
        locator = (By.ID, "test-element")
        
        with pytest.raises(TimeoutException):
            self.manager.smart_wait_for_element(locator, timeout=5.0)
        
        # 실패 기록 확인
        assert len(self.manager._performance_history) == 1
        assert self.manager._performance_history[0]['success'] is False
    
    def test_calculate_dynamic_timeout_no_history(self):
        """히스토리가 없을 때 동적 타임아웃 계산"""
        timeout = self.manager._calculate_dynamic_timeout()
        
        assert timeout == self.manager._base_timeout
    
    def test_calculate_dynamic_timeout_with_history(self):
        """히스토리가 있을 때 동적 타임아웃 계산"""
        # 성공 기록 추가
        self.manager._record_performance(2.0, True)
        self.manager._record_performance(3.0, True)
        self.manager._record_performance(1.0, True)
        
        timeout = self.manager._calculate_dynamic_timeout()
        
        # 평균 2.0초의 2.5배 = 5.0초
        assert timeout == 5.0
    
    def test_calculate_dynamic_timeout_limits(self):
        """동적 타임아웃 최소/최대 제한 테스트"""
        # 매우 짧은 시간들
        self.manager._record_performance(0.1, True)
        self.manager._record_performance(0.2, True)
        
        timeout = self.manager._calculate_dynamic_timeout()
        assert timeout >= 5.0  # 최소 제한
        
        # 매우 긴 시간들
        self.manager._performance_history.clear()
        self.manager._record_performance(20.0, True)
        self.manager._record_performance(25.0, True)
        
        timeout = self.manager._calculate_dynamic_timeout()
        assert timeout <= 30.0  # 최대 제한
    
    def test_record_performance(self):
        """성능 기록 테스트"""
        self.manager._record_performance(1.5, True)
        
        assert len(self.manager._performance_history) == 1
        record = self.manager._performance_history[0]
        assert record['elapsed'] == 1.5
        assert record['success'] is True
        assert 'timestamp' in record
    
    def test_get_performance_stats_empty(self):
        """빈 성능 히스토리 통계 테스트"""
        stats = self.manager.get_performance_stats()
        
        assert stats == {}
    
    def test_get_performance_stats_with_data(self):
        """데이터가 있는 성능 통계 테스트"""
        # 성공과 실패 기록 추가
        self.manager._record_performance(1.0, True)
        self.manager._record_performance(2.0, True)
        self.manager._record_performance(3.0, False)  # 실패
        
        stats = self.manager.get_performance_stats()
        
        assert stats['total_attempts'] == 3
        assert stats['success_rate'] == 2/3  # 2 성공, 1 실패
        assert stats['avg_success_time'] == 1.5  # (1.0 + 2.0) / 2
        assert 'recommended_timeout' in stats
        assert 'success_time_std' in stats


class TestEnums:
    """Enum 클래스들 테스트"""
    
    def test_retry_strategy_values(self):
        """RetryStrategy enum 값 테스트"""
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"
        assert RetryStrategy.ADAPTIVE.value == "adaptive"
    
    def test_failure_type_values(self):
        """FailureType enum 값 테스트"""
        assert FailureType.STALE_ELEMENT.value == "stale_element"
        assert FailureType.ELEMENT_NOT_INTERACTABLE.value == "element_not_interactable"
        assert FailureType.ELEMENT_CLICK_INTERCEPTED.value == "element_click_intercepted"
        assert FailureType.TIMEOUT.value == "timeout"
        assert FailureType.NO_SUCH_ELEMENT.value == "no_such_element"
        assert FailureType.NETWORK_ERROR.value == "network_error"
        assert FailureType.UNKNOWN.value == "unknown"


class TestIntegration:
    """통합 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_driver = Mock()
        self.config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            learning_enabled=True,
            enable_self_healing=True
        )
    
    def test_full_retry_cycle_with_learning(self):
        """학습 기능을 포함한 전체 재시도 사이클 테스트"""
        manager = SmartRetryManager(self.mock_driver, self.config)
        
        # 실패 후 성공하는 함수 모의
        mock_func = Mock()
        mock_func.side_effect = [
            StaleElementReferenceException("First failure"),
            "success"
        ]
        
        locator = (By.ID, "test-element")
        result = manager.execute_with_retry(
            mock_func, 
            locator=locator
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
        
        # 학습자가 패턴을 기록했는지 확인
        if manager.learner:
            assert len(manager.learner._patterns) == 1
            assert len(manager.learner._metrics) == 1
    
    def test_adaptive_config_recommendation(self):
        """적응형 설정 권장 테스트"""
        learner = FailurePatternLearner()
        locator = (By.ID, "problematic-element")
        action = "click"
        
        # 여러 실패 패턴 기록
        for _ in range(5):
            learner.record_failure(FailureType.STALE_ELEMENT, locator, action, 1)
        
        # 몇 번의 성공 기록
        learner.record_success(locator, action, 2.0)
        learner.record_success(locator, action, 3.0)
        
        config = learner.get_recommended_config(locator, action)
        
        # 낮은 성공률로 인해 더 많은 재시도 허용
        assert config.max_attempts >= 3
        # STALE_ELEMENT가 우세하므로 FIXED_DELAY 전략
        assert config.strategy == RetryStrategy.FIXED_DELAY
        # 성공 시간을 반영한 타임아웃 조정
        assert config.timeout >= 5.0