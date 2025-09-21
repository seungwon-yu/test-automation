"""
테스트 픽스처들

이 모듈은 테스트에서 사용할 수 있는 다양한 픽스처와 샘플 데이터를 제공합니다.
"""

import pytest
from typing import Dict, Any, List
from pathlib import Path
from unittest.mock import Mock

from .mock_helpers import MockDriverFactory, MockConfigManager, MockLogger


# ==================== 기본 픽스처들 ====================

@pytest.fixture
def sample_test_config() -> Dict[str, Any]:
    """샘플 테스트 설정"""
    return {
        'browser': {
            'default': 'chrome',
            'headless': True,
            'window_size': '1920x1080',
            'timeout': 30,
            'page_load_timeout': 30,
            'implicit_wait': 10
        },
        'test': {
            'base_url': 'http://test.example.com',
            'parallel_workers': 4,
            'screenshot_on_failure': True,
            'retry_attempts': 3,
            'retry_delay': 1.0
        },
        'reporting': {
            'html_report': True,
            'allure_report': False,
            'output_dir': 'reports',
            'screenshot_dir': 'screenshots'
        },
        'logging': {
            'level': 'INFO',
            'file_logging': True,
            'console_logging': True,
            'log_dir': 'logs'
        }
    }


@pytest.fixture
def sample_driver_config() -> Dict[str, Any]:
    """샘플 드라이버 설정"""
    return {
        'browser': 'chrome',
        'headless': True,
        'window_size': (1920, 1080),
        'timeout': 30,
        'page_load_timeout': 30,
        'implicit_wait': 10,
        'options': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions'
        ],
        'capabilities': {
            'acceptInsecureCerts': True,
            'unhandledPromptBehavior': 'accept'
        }
    }


@pytest.fixture
def sample_page_elements() -> Dict[str, tuple]:
    """샘플 페이지 요소 로케이터들"""
    from selenium.webdriver.common.by import By
    
    return {
        'login_form': {
            'username': (By.ID, 'username'),
            'password': (By.ID, 'password'),
            'login_button': (By.ID, 'login-btn'),
            'remember_me': (By.ID, 'remember-me'),
            'forgot_password': (By.LINK_TEXT, 'Forgot Password?')
        },
        'navigation': {
            'home': (By.LINK_TEXT, 'Home'),
            'products': (By.LINK_TEXT, 'Products'),
            'cart': (By.ID, 'cart-icon'),
            'profile': (By.CLASS_NAME, 'user-profile'),
            'logout': (By.LINK_TEXT, 'Logout')
        },
        'search': {
            'search_box': (By.NAME, 'search'),
            'search_button': (By.CSS_SELECTOR, 'button[type="submit"]'),
            'results_container': (By.CLASS_NAME, 'search-results'),
            'no_results': (By.CLASS_NAME, 'no-results')
        },
        'product': {
            'title': (By.H1, 'product-title'),
            'price': (By.CLASS_NAME, 'price'),
            'add_to_cart': (By.ID, 'add-to-cart'),
            'quantity': (By.NAME, 'quantity'),
            'description': (By.CLASS_NAME, 'description')
        }
    }


@pytest.fixture
def sample_test_data() -> Dict[str, Any]:
    """샘플 테스트 데이터"""
    return {
        'users': {
            'valid_user': {
                'username': 'testuser@example.com',
                'password': 'TestPassword123!',
                'first_name': 'Test',
                'last_name': 'User'
            },
            'invalid_user': {
                'username': 'invalid@example.com',
                'password': 'wrongpassword'
            },
            'admin_user': {
                'username': 'admin@example.com',
                'password': 'AdminPassword123!',
                'role': 'administrator'
            }
        },
        'products': {
            'laptop': {
                'name': 'Test Laptop',
                'price': 999.99,
                'category': 'Electronics',
                'sku': 'LAP-001'
            },
            'book': {
                'name': 'Test Book',
                'price': 29.99,
                'category': 'Books',
                'sku': 'BOO-001'
            }
        },
        'search_terms': [
            'laptop',
            'book',
            'electronics',
            'nonexistent_product'
        ]
    }


# ==================== Mock 픽스처들 ====================

@pytest.fixture
def mock_driver():
    """Mock WebDriver 픽스처"""
    return MockDriverFactory.create_chrome_driver()


@pytest.fixture
def mock_firefox_driver():
    """Mock Firefox WebDriver 픽스처"""
    return MockDriverFactory.create_firefox_driver()


@pytest.fixture
def mock_edge_driver():
    """Mock Edge WebDriver 픽스처"""
    return MockDriverFactory.create_edge_driver()


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager 픽스처"""
    return MockConfigManager.create_config_manager()


@pytest.fixture
def mock_logger():
    """Mock Logger 픽스처"""
    return MockLogger.create_logger()


# ==================== 파일 시스템 픽스처들 ====================

@pytest.fixture
def temp_directory(tmp_path):
    """임시 디렉토리 픽스처"""
    return tmp_path


@pytest.fixture
def temp_config_file(tmp_path, sample_test_config):
    """임시 설정 파일 픽스처"""
    import yaml
    
    config_file = tmp_path / "test_config.yml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_test_config, f)
    
    return config_file


@pytest.fixture
def temp_screenshot_dir(tmp_path):
    """임시 스크린샷 디렉토리 픽스처"""
    screenshot_dir = tmp_path / "screenshots"
    screenshot_dir.mkdir()
    return screenshot_dir


@pytest.fixture
def temp_report_dir(tmp_path):
    """임시 리포트 디렉토리 픽스처"""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return report_dir


# ==================== 환경 픽스처들 ====================

@pytest.fixture
def clean_environment():
    """깨끗한 환경 변수 픽스처"""
    import os
    original_env = os.environ.copy()
    
    # 테스트 관련 환경 변수 정리
    test_env_vars = [
        'TEST_ENV',
        'BASE_URL',
        'BROWSER',
        'HEADLESS',
        'TIMEOUT'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # 환경 변수 복원
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_environment(clean_environment):
    """테스트 환경 변수 설정 픽스처"""
    import os
    
    os.environ['TEST_ENV'] = 'test'
    os.environ['BASE_URL'] = 'http://test.example.com'
    os.environ['BROWSER'] = 'chrome'
    os.environ['HEADLESS'] = 'true'
    os.environ['TIMEOUT'] = '30'
    
    yield


# ==================== 성능 테스트 픽스처들 ====================

@pytest.fixture
def performance_thresholds():
    """성능 임계값 픽스처"""
    return {
        'page_load': 3.0,  # 3초
        'element_find': 1.0,  # 1초
        'click_action': 0.5,  # 0.5초
        'form_fill': 2.0,  # 2초
        'navigation': 2.0  # 2초
    }


# ==================== 데이터베이스 픽스처들 ====================

@pytest.fixture
def mock_database():
    """Mock 데이터베이스 픽스처"""
    class MockDatabase:
        def __init__(self):
            self.data = {}
            self.connected = False
        
        def connect(self):
            self.connected = True
        
        def disconnect(self):
            self.connected = False
        
        def insert(self, table, data):
            if table not in self.data:
                self.data[table] = []
            self.data[table].append(data)
        
        def select(self, table, condition=None):
            if table not in self.data:
                return []
            
            if condition is None:
                return self.data[table]
            
            return [item for item in self.data[table] if condition(item)]
        
        def delete(self, table, condition=None):
            if table not in self.data:
                return
            
            if condition is None:
                self.data[table] = []
            else:
                self.data[table] = [item for item in self.data[table] if not condition(item)]
    
    return MockDatabase()


# ==================== API 테스트 픽스처들 ====================

@pytest.fixture
def mock_api_responses():
    """Mock API 응답 픽스처"""
    return {
        'login_success': {
            'status_code': 200,
            'json': {
                'success': True,
                'token': 'test-token-123',
                'user': {
                    'id': 1,
                    'username': 'testuser',
                    'email': 'testuser@example.com'
                }
            }
        },
        'login_failure': {
            'status_code': 401,
            'json': {
                'success': False,
                'error': 'Invalid credentials'
            }
        },
        'product_list': {
            'status_code': 200,
            'json': {
                'products': [
                    {'id': 1, 'name': 'Laptop', 'price': 999.99},
                    {'id': 2, 'name': 'Book', 'price': 29.99}
                ],
                'total': 2
            }
        },
        'server_error': {
            'status_code': 500,
            'json': {
                'error': 'Internal server error'
            }
        }
    }


# ==================== 브라우저 특화 픽스처들 ====================

@pytest.fixture(params=['chrome', 'firefox', 'edge'])
def browser_type(request):
    """브라우저 타입 파라미터 픽스처"""
    return request.param


@pytest.fixture
def browser_options():
    """브라우저 옵션 픽스처"""
    return {
        'chrome': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions',
            '--disable-web-security'
        ],
        'firefox': [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ],
        'edge': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    }


# ==================== 테스트 시나리오 픽스처들 ====================

@pytest.fixture
def login_scenarios():
    """로그인 테스트 시나리오 픽스처"""
    return [
        {
            'name': 'valid_login',
            'username': 'testuser@example.com',
            'password': 'TestPassword123!',
            'expected_result': True,
            'expected_url': '/dashboard'
        },
        {
            'name': 'invalid_username',
            'username': 'invalid@example.com',
            'password': 'TestPassword123!',
            'expected_result': False,
            'expected_error': 'Invalid username'
        },
        {
            'name': 'invalid_password',
            'username': 'testuser@example.com',
            'password': 'wrongpassword',
            'expected_result': False,
            'expected_error': 'Invalid password'
        },
        {
            'name': 'empty_fields',
            'username': '',
            'password': '',
            'expected_result': False,
            'expected_error': 'Username and password are required'
        }
    ]


@pytest.fixture
def search_scenarios():
    """검색 테스트 시나리오 픽스처"""
    return [
        {
            'name': 'valid_search',
            'query': 'laptop',
            'expected_results': True,
            'min_results': 1
        },
        {
            'name': 'no_results',
            'query': 'nonexistent_product_xyz',
            'expected_results': False,
            'expected_message': 'No results found'
        },
        {
            'name': 'empty_search',
            'query': '',
            'expected_results': False,
            'expected_error': 'Please enter a search term'
        },
        {
            'name': 'special_characters',
            'query': '!@#$%^&*()',
            'expected_results': False,
            'expected_message': 'No results found'
        }
    ]


# ==================== 유틸리티 픽스처들 ====================

@pytest.fixture
def test_timer():
    """테스트 실행 시간 측정 픽스처"""
    import time
    
    class TestTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    timer = TestTimer()
    timer.start()
    
    yield timer
    
    timer.stop()


@pytest.fixture
def screenshot_capture():
    """스크린샷 캡처 Mock 픽스처"""
    class MockScreenshotCapture:
        def __init__(self):
            self.screenshots = []
        
        def capture(self, filename):
            self.screenshots.append(filename)
            return f"/fake/path/{filename}"
        
        def get_screenshots(self):
            return self.screenshots.copy()
        
        def clear(self):
            self.screenshots.clear()
    
    return MockScreenshotCapture()


# ==================== 조건부 픽스처들 ====================

@pytest.fixture
def skip_if_no_display():
    """디스플레이가 없으면 테스트 스킵"""
    import os
    if not os.environ.get('DISPLAY') and os.name != 'nt':
        pytest.skip("No display available")


@pytest.fixture
def skip_if_ci():
    """CI 환경에서 테스트 스킵"""
    import os
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
        pytest.skip("Skipping in CI environment")


# ==================== 마커 기반 픽스처들 ====================

@pytest.fixture(autouse=True)
def setup_test_markers(request):
    """테스트 마커에 따른 자동 설정"""
    # slow 마커가 있는 테스트의 타임아웃 증가
    if request.node.get_closest_marker("slow"):
        import pytest
        pytest.timeout = 60  # 60초 타임아웃
    
    # integration 마커가 있는 테스트의 특별 설정
    if request.node.get_closest_marker("integration"):
        # 통합 테스트 전용 설정
        pass
    
    # performance 마커가 있는 테스트의 성능 모니터링 활성화
    if request.node.get_closest_marker("performance"):
        # 성능 모니터링 활성화
        pass