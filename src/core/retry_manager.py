"""
Smart Retry 및 Self-healing 관리 시스템

이 모듈은 웹 자동화 테스트에서 발생하는 일시적 실패에 대한 
지능적인 재시도 로직과 자동 복구 메커니즘을 제공합니다.
"""

import time
import random
import threading
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from collections import defaultdict, deque
import statistics

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

from .exceptions import TestFrameworkException
from .logging import get_logger


class RetryStrategy(Enum):
    """재시도 전략 타입"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE = "adaptive"


class FailureType(Enum):
    """실패 유형 분류"""
    STALE_ELEMENT = "stale_element"
    ELEMENT_NOT_INTERACTABLE = "element_not_interactable"
    ELEMENT_CLICK_INTERCEPTED = "element_click_intercepted"
    TIMEOUT = "timeout"
    NO_SUCH_ELEMENT = "no_such_element"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """재시도 설정 클래스"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    backoff_multiplier: float = 2.0
    timeout: float = 10.0
    
    # Self-healing 설정
    enable_self_healing: bool = True
    learning_enabled: bool = True
    adaptive_timeout: bool = True
    
    # 특정 예외에 대한 재시도 여부
    retry_on_stale_element: bool = True
    retry_on_timeout: bool = True
    retry_on_click_intercepted: bool = True
    retry_on_not_interactable: bool = True


@dataclass
class FailurePattern:
    """실패 패턴 정보"""
    failure_type: FailureType
    locator: tuple
    action: str
    timestamp: float
    retry_count: int
    success_delay: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptiveMetrics:
    """적응형 메트릭"""
    success_delays: deque = field(default_factory=lambda: deque(maxlen=100))
    failure_counts: Dict[FailureType, int] = field(default_factory=lambda: defaultdict(int))
    success_rate: float = 1.0
    avg_success_delay: float = 1.0
    recommended_timeout: float = 10.0


class FailurePatternLearner:
    """
    실패 패턴 학습 및 분석 클래스
    
    테스트 실행 중 발생하는 실패 패턴을 학습하여
    향후 유사한 상황에서 더 효과적인 재시도 전략을 제안합니다.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._patterns: List[FailurePattern] = []
        self._metrics: Dict[str, AdaptiveMetrics] = defaultdict(AdaptiveMetrics)
        self._lock = threading.Lock()
    
    def record_failure(self, failure_type: FailureType, locator: tuple, 
                      action: str, retry_count: int, context: Dict[str, Any] = None) -> None:
        """실패 패턴 기록"""
        pattern = FailurePattern(
            failure_type=failure_type,
            locator=locator,
            action=action,
            timestamp=time.time(),
            retry_count=retry_count,
            context=context or {}
        )
        
        with self._lock:
            self._patterns.append(pattern)
            key = self._get_pattern_key(locator, action)
            self._metrics[key].failure_counts[failure_type] += 1
        
        self.logger.debug(f"Recorded failure pattern: {failure_type.value} for {action} on {locator}")
    
    def record_success(self, locator: tuple, action: str, delay: float) -> None:
        """성공 패턴 기록"""
        key = self._get_pattern_key(locator, action)
        
        with self._lock:
            metrics = self._metrics[key]
            metrics.success_delays.append(delay)
            
            # 성공률 계산
            total_failures = sum(metrics.failure_counts.values())
            total_attempts = len(metrics.success_delays) + total_failures
            metrics.success_rate = len(metrics.success_delays) / max(total_attempts, 1)
            
            # 평균 성공 지연시간 계산
            if metrics.success_delays:
                metrics.avg_success_delay = statistics.mean(metrics.success_delays)
                # 권장 타임아웃 계산 (평균 + 2 * 표준편차)
                if len(metrics.success_delays) > 1:
                    std_dev = statistics.stdev(metrics.success_delays)
                    metrics.recommended_timeout = metrics.avg_success_delay + (2 * std_dev)
        
        self.logger.debug(f"Recorded success pattern: {action} on {locator} with delay {delay:.2f}s")
    
    def get_recommended_config(self, locator: tuple, action: str) -> RetryConfig:
        """학습된 패턴을 바탕으로 권장 설정 반환"""
        key = self._get_pattern_key(locator, action)
        
        with self._lock:
            metrics = self._metrics.get(key, AdaptiveMetrics())
        
        config = RetryConfig()
        
        # 성공률에 따른 최대 재시도 횟수 조정
        if metrics.success_rate < 0.5:
            config.max_attempts = 5
        elif metrics.success_rate < 0.8:
            config.max_attempts = 3
        else:
            config.max_attempts = 2
        
        # 평균 성공 지연시간에 따른 기본 지연시간 조정
        config.base_delay = max(0.5, metrics.avg_success_delay * 0.5)
        config.timeout = max(5.0, metrics.recommended_timeout)
        
        # 실패 유형에 따른 전략 조정
        dominant_failure = self._get_dominant_failure_type(metrics.failure_counts)
        if dominant_failure == FailureType.STALE_ELEMENT:
            config.strategy = RetryStrategy.FIXED_DELAY
            config.base_delay = 0.5
        elif dominant_failure == FailureType.TIMEOUT:
            config.strategy = RetryStrategy.EXPONENTIAL_BACKOFF
            config.base_delay = 2.0
        
        return config
    
    def _get_pattern_key(self, locator: tuple, action: str) -> str:
        """패턴 키 생성"""
        return f"{action}:{locator[0]}:{locator[1]}"
    
    def _get_dominant_failure_type(self, failure_counts: Dict[FailureType, int]) -> FailureType:
        """가장 빈번한 실패 유형 반환"""
        if not failure_counts:
            return FailureType.UNKNOWN
        
        return max(failure_counts.items(), key=lambda x: x[1])[0]
    
    def get_statistics(self) -> Dict[str, Any]:
        """학습 통계 정보 반환"""
        with self._lock:
            total_patterns = len(self._patterns)
            failure_type_counts = defaultdict(int)
            
            for pattern in self._patterns:
                failure_type_counts[pattern.failure_type] += 1
            
            return {
                'total_patterns': total_patterns,
                'failure_type_distribution': dict(failure_type_counts),
                'tracked_elements': len(self._metrics),
                'avg_success_rate': statistics.mean([m.success_rate for m in self._metrics.values()]) if self._metrics else 0.0
            }


class SmartRetryManager:
    """
    지능적 재시도 관리자
    
    웹 요소 상호작용에서 발생하는 다양한 예외에 대해
    적응형 재시도 로직과 자동 복구 메커니즘을 제공합니다.
    """
    
    def __init__(self, driver: WebDriver, config: RetryConfig = None):
        self.driver = driver
        self.config = config or RetryConfig()
        self.logger = get_logger(__name__)
        self.learner = FailurePatternLearner() if config and config.learning_enabled else None
        
        # 예외 타입별 처리 매핑
        self._exception_handlers = {
            StaleElementReferenceException: self._handle_stale_element,
            ElementNotInteractableException: self._handle_not_interactable,
            ElementClickInterceptedException: self._handle_click_intercepted,
            TimeoutException: self._handle_timeout,
            NoSuchElementException: self._handle_no_such_element,
        }
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        재시도 로직을 적용하여 함수 실행
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
            
        Returns:
            함수 실행 결과
            
        Raises:
            AutomationTestException: 모든 재시도 실패 시
        """
        locator = kwargs.get('locator', ('unknown', 'unknown'))
        action = func.__name__
        
        # 학습된 패턴이 있다면 설정 조정
        if self.learner and self.config.learning_enabled:
            learned_config = self.learner.get_recommended_config(locator, action)
            config = self._merge_configs(self.config, learned_config)
        else:
            config = self.config
        
        last_exception = None
        start_time = time.time()
        
        for attempt in range(config.max_attempts):
            try:
                self.logger.debug(f"Executing {action} (attempt {attempt + 1}/{config.max_attempts})")
                
                result = func(*args, **kwargs)
                
                # 성공 시 학습 데이터 기록
                if self.learner:
                    delay = time.time() - start_time
                    self.learner.record_success(locator, action, delay)
                
                return result
                
            except Exception as e:
                last_exception = e
                failure_type = self._classify_failure(e)
                
                self.logger.warning(f"Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
                
                # 학습 데이터 기록
                if self.learner:
                    self.learner.record_failure(failure_type, locator, action, attempt + 1)
                
                # 재시도 가능한 예외인지 확인
                if not self._should_retry(e, config):
                    break
                
                # 마지막 시도가 아니라면 자동 복구 시도
                if attempt < config.max_attempts - 1:
                    if config.enable_self_healing:
                        self._attempt_self_healing(e, locator, action)
                    
                    # 지연 시간 계산 및 대기
                    delay = self._calculate_delay(attempt, config)
                    self.logger.debug(f"Waiting {delay:.2f}s before retry")
                    time.sleep(delay)
        
        # 모든 재시도 실패
        raise TestFrameworkException(
            f"Failed to execute {action} after {config.max_attempts} attempts. "
            f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
        )
    
    def _classify_failure(self, exception: Exception) -> FailureType:
        """예외를 실패 유형으로 분류"""
        if isinstance(exception, StaleElementReferenceException):
            return FailureType.STALE_ELEMENT
        elif isinstance(exception, ElementNotInteractableException):
            return FailureType.ELEMENT_NOT_INTERACTABLE
        elif isinstance(exception, ElementClickInterceptedException):
            return FailureType.ELEMENT_CLICK_INTERCEPTED
        elif isinstance(exception, TimeoutException):
            return FailureType.TIMEOUT
        elif isinstance(exception, NoSuchElementException):
            return FailureType.NO_SUCH_ELEMENT
        elif isinstance(exception, WebDriverException):
            return FailureType.NETWORK_ERROR
        else:
            return FailureType.UNKNOWN
    
    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """예외에 대해 재시도할지 결정"""
        if isinstance(exception, StaleElementReferenceException):
            return config.retry_on_stale_element
        elif isinstance(exception, TimeoutException):
            return config.retry_on_timeout
        elif isinstance(exception, ElementClickInterceptedException):
            return config.retry_on_click_intercepted
        elif isinstance(exception, ElementNotInteractableException):
            return config.retry_on_not_interactable
        else:
            return True  # 기본적으로 재시도
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """재시도 지연 시간 계산"""
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
        elif config.strategy == RetryStrategy.ADAPTIVE:
            # 적응형: 최근 성공 패턴을 기반으로 조정
            delay = config.base_delay * (1.5 ** attempt)
        else:
            delay = config.base_delay
        
        # 최대 지연 시간 제한
        delay = min(delay, config.max_delay)
        
        # 지터 추가 (랜덤 요소)
        if config.jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0.1, delay)  # 최소 0.1초
    
    def _attempt_self_healing(self, exception: Exception, locator: tuple, action: str) -> None:
        """자동 복구 시도"""
        handler = self._exception_handlers.get(type(exception))
        if handler:
            try:
                handler(exception, locator, action)
            except Exception as e:
                self.logger.warning(f"Self-healing failed: {str(e)}")
    
    def _handle_stale_element(self, exception: Exception, locator: tuple, action: str) -> None:
        """StaleElementException 자동 복구"""
        self.logger.info("Attempting to recover from stale element")
        
        # 페이지 새로고침 또는 요소 재검색
        try:
            # 잠시 대기 후 요소 재검색 시도
            time.sleep(0.5)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.info("Successfully recovered from stale element")
        except Exception:
            self.logger.warning("Failed to recover from stale element")
    
    def _handle_not_interactable(self, exception: Exception, locator: tuple, action: str) -> None:
        """ElementNotInteractableException 자동 복구"""
        self.logger.info("Attempting to recover from non-interactable element")
        
        try:
            # 요소가 상호작용 가능해질 때까지 대기
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(locator)
            )
            self.logger.info("Element became interactable")
        except Exception:
            # 스크롤하여 요소를 뷰포트로 이동
            try:
                element = self.driver.find_element(*locator)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                self.logger.info("Scrolled element into view")
            except Exception:
                self.logger.warning("Failed to make element interactable")
    
    def _handle_click_intercepted(self, exception: Exception, locator: tuple, action: str) -> None:
        """ElementClickInterceptedException 자동 복구"""
        self.logger.info("Attempting to recover from click interception")
        
        try:
            # 오버레이나 모달 닫기 시도
            self._close_overlays()
            
            # 요소를 뷰포트 중앙으로 스크롤
            element = self.driver.find_element(*locator)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", 
                element
            )
            time.sleep(0.5)
            
            self.logger.info("Attempted to clear click interception")
        except Exception:
            self.logger.warning("Failed to recover from click interception")
    
    def _handle_timeout(self, exception: Exception, locator: tuple, action: str) -> None:
        """TimeoutException 자동 복구"""
        self.logger.info("Attempting to recover from timeout")
        
        try:
            # 페이지 로딩 완료 대기
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 추가 대기 시간
            time.sleep(1.0)
            self.logger.info("Page loading completed")
        except Exception:
            self.logger.warning("Failed to recover from timeout")
    
    def _handle_no_such_element(self, exception: Exception, locator: tuple, action: str) -> None:
        """NoSuchElementException 자동 복구"""
        self.logger.info("Attempting to recover from missing element")
        
        try:
            # 페이지 새로고침
            self.driver.refresh()
            
            # 요소가 나타날 때까지 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.info("Element found after page refresh")
        except Exception:
            self.logger.warning("Failed to recover missing element")
    
    def _close_overlays(self) -> None:
        """오버레이나 모달 닫기 시도"""
        overlay_selectors = [
            "//button[contains(@class, 'close')]",
            "//button[contains(@class, 'modal-close')]",
            "//div[contains(@class, 'overlay')]//button",
            "//div[contains(@class, 'popup')]//button[contains(text(), '닫기')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Close')]"
        ]
        
        for selector in overlay_selectors:
            try:
                close_button = self.driver.find_element(By.XPATH, selector)
                if close_button.is_displayed():
                    close_button.click()
                    time.sleep(0.5)
                    self.logger.debug(f"Closed overlay using selector: {selector}")
                    break
            except Exception:
                continue
    
    def _merge_configs(self, base_config: RetryConfig, learned_config: RetryConfig) -> RetryConfig:
        """기본 설정과 학습된 설정을 병합"""
        merged = RetryConfig()
        
        # 학습된 설정을 우선하되, 기본 설정의 제한을 준수
        merged.max_attempts = min(learned_config.max_attempts, base_config.max_attempts + 2)
        merged.base_delay = max(base_config.base_delay * 0.5, learned_config.base_delay)
        merged.timeout = min(learned_config.timeout, base_config.timeout * 2)
        merged.strategy = learned_config.strategy
        
        # 나머지는 기본 설정 사용
        merged.max_delay = base_config.max_delay
        merged.jitter = base_config.jitter
        merged.backoff_multiplier = base_config.backoff_multiplier
        merged.enable_self_healing = base_config.enable_self_healing
        merged.learning_enabled = base_config.learning_enabled
        merged.adaptive_timeout = base_config.adaptive_timeout
        
        return merged


def smart_retry(config: RetryConfig = None):
    """
    Smart Retry 데코레이터
    
    웹 요소 상호작용 메서드에 적용하여 자동 재시도 기능을 추가합니다.
    
    Args:
        config: 재시도 설정 (None이면 기본 설정 사용)
    
    Example:
        @smart_retry(RetryConfig(max_attempts=5))
        def click_element(self, locator):
            element = self.driver.find_element(*locator)
            element.click()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # self가 driver 속성을 가지고 있다고 가정
            if not hasattr(self, 'driver'):
                raise AttributeError("Object must have 'driver' attribute for smart_retry")
            
            retry_manager = SmartRetryManager(self.driver, config)
            
            # locator 정보를 kwargs에 추가 (학습을 위해)
            if args and len(args) > 0 and isinstance(args[0], tuple) and 'locator' not in kwargs:
                kwargs['locator'] = args[0]
            
            return retry_manager.execute_with_retry(func, self, *args, **kwargs)
        
        return wrapper
    return decorator


class DynamicWaitManager:
    """
    동적 대기 시간 관리자
    
    페이지 로딩 상태와 네트워크 조건을 분석하여
    최적의 대기 시간을 동적으로 조정합니다.
    """
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = get_logger(__name__)
        self._performance_history = deque(maxlen=50)
        self._base_timeout = 10.0
    
    def smart_wait_for_element(self, locator: tuple, timeout: float = None) -> WebElement:
        """
        지능적 요소 대기
        
        Args:
            locator: 요소 로케이터
            timeout: 최대 대기 시간 (None이면 동적 계산)
            
        Returns:
            WebElement 인스턴스
        """
        if timeout is None:
            timeout = self._calculate_dynamic_timeout()
        
        start_time = time.time()
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            
            # 성능 기록
            elapsed = time.time() - start_time
            self._record_performance(elapsed, True)
            
            return element
            
        except TimeoutException:
            elapsed = time.time() - start_time
            self._record_performance(elapsed, False)
            raise
    
    def _calculate_dynamic_timeout(self) -> float:
        """동적 타임아웃 계산"""
        if not self._performance_history:
            return self._base_timeout
        
        # 최근 성능 데이터 분석
        recent_times = [p['elapsed'] for p in self._performance_history if p['success']]
        
        if recent_times:
            avg_time = statistics.mean(recent_times)
            # 평균 시간의 2-3배를 타임아웃으로 설정
            dynamic_timeout = avg_time * 2.5
            
            # 최소/최대 제한
            return max(5.0, min(dynamic_timeout, 30.0))
        
        return self._base_timeout
    
    def _record_performance(self, elapsed: float, success: bool) -> None:
        """성능 데이터 기록"""
        self._performance_history.append({
            'elapsed': elapsed,
            'success': success,
            'timestamp': time.time()
        })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        if not self._performance_history:
            return {}
        
        success_times = [p['elapsed'] for p in self._performance_history if p['success']]
        total_attempts = len(self._performance_history)
        success_rate = len(success_times) / total_attempts if total_attempts > 0 else 0
        
        stats = {
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'avg_success_time': statistics.mean(success_times) if success_times else 0,
            'recommended_timeout': self._calculate_dynamic_timeout()
        }
        
        if len(success_times) > 1:
            stats['success_time_std'] = statistics.stdev(success_times)
        
        return stats