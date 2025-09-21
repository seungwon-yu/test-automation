"""
드라이버 팩토리 모듈

이 모듈은 다양한 브라우저 드라이버를 생성하고 관리하는 팩토리 클래스를 제공합니다.
Chrome, Firefox, Safari 등 다양한 브라우저를 지원하며, 헤드리스 모드, 윈도우 크기 설정,
프록시 설정 등 다양한 옵션을 제공합니다.
"""

import os
import logging
import time
import threading
from typing import Optional, Dict, Any, Union, List
from enum import Enum
from dataclasses import dataclass, field
from queue import Queue, Empty
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .exceptions import DriverInitializationException, ConfigurationException
from .logging import get_logger


class BrowserType(Enum):
    """지원되는 브라우저 타입"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"


@dataclass
class DriverConfig:
    """드라이버 설정 클래스"""
    browser: BrowserType
    headless: bool = False
    window_size: tuple = (1920, 1080)
    timeout: int = 30
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    download_dir: Optional[str] = None
    disable_images: bool = False
    disable_javascript: bool = False
    incognito: bool = False
    remote_url: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    # 원격 드라이버 추가 설정
    grid_node_max_sessions: int = 5
    grid_session_timeout: int = 300
    docker_network: Optional[str] = None
    docker_volumes: Optional[Dict[str, str]] = None
    docker_environment: Optional[Dict[str, str]] = None


@dataclass
class RemoteDriverConfig:
    """원격 드라이버 전용 설정 클래스"""
    hub_url: str
    browser: BrowserType
    browser_version: str = "latest"
    platform: str = "ANY"
    max_sessions: int = 5
    session_timeout: int = 300
    connection_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: int = 2
    capabilities: Optional[Dict[str, Any]] = field(default_factory=dict)
    docker_config: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DriverPoolConfig:
    """드라이버 풀 설정 클래스"""
    max_pool_size: int = 10
    min_pool_size: int = 2
    idle_timeout: int = 300  # seconds
    max_wait_time: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    auto_cleanup: bool = True


class RemoteDriverManager:
    """
    원격 드라이버 관리 클래스
    
    Selenium Grid 연동 및 Docker 컨테이너 환경에서의 
    드라이버 실행을 지원합니다.
    """
    
    def __init__(self, config: RemoteDriverConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self._active_sessions: Dict[str, webdriver.Remote] = {}
        self._session_lock = threading.Lock()
    
    def create_remote_driver(self, driver_config: DriverConfig) -> webdriver.Remote:
        """
        원격 드라이버 생성 (Selenium Grid 또는 Docker 환경)
        
        Args:
            driver_config: 드라이버 설정
            
        Returns:
            Remote WebDriver 인스턴스
            
        Raises:
            DriverInitializationException: 드라이버 생성 실패 시
        """
        try:
            self.logger.info(f"Creating remote driver for {self.config.browser.value}",
                           hub_url=self.config.hub_url,
                           browser=self.config.browser.value,
                           platform=self.config.platform)
            
            # Desired Capabilities 설정
            capabilities = self._build_capabilities(driver_config)
            
            # 재시도 로직으로 드라이버 생성
            driver = self._create_with_retry(capabilities)
            
            # 세션 관리에 추가
            session_id = driver.session_id
            with self._session_lock:
                self._active_sessions[session_id] = driver
            
            self.logger.info(f"Remote driver created successfully",
                           session_id=session_id,
                           browser=self.config.browser.value)
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create remote driver: {str(e)}")
            raise DriverInitializationException(f"Remote driver creation failed: {str(e)}")
    
    def _build_capabilities(self, driver_config: DriverConfig) -> Dict[str, Any]:
        """Desired Capabilities 구성"""
        # 기본 capabilities
        if self.config.browser == BrowserType.CHROME:
            capabilities = DesiredCapabilities.CHROME.copy()
            capabilities['goog:chromeOptions'] = self._get_chrome_options(driver_config)
        elif self.config.browser == BrowserType.FIREFOX:
            capabilities = DesiredCapabilities.FIREFOX.copy()
            capabilities['moz:firefoxOptions'] = self._get_firefox_options(driver_config)
        elif self.config.browser == BrowserType.SAFARI:
            capabilities = DesiredCapabilities.SAFARI.copy()
        elif self.config.browser == BrowserType.EDGE:
            capabilities = DesiredCapabilities.EDGE.copy()
            capabilities['ms:edgeOptions'] = self._get_edge_options(driver_config)
        else:
            capabilities = {}
        
        # 플랫폼 및 버전 설정
        capabilities['browserName'] = self.config.browser.value
        capabilities['browserVersion'] = self.config.browser_version
        capabilities['platformName'] = self.config.platform
        
        # 세션 설정
        capabilities['se:maxSessions'] = self.config.max_sessions
        capabilities['se:sessionTimeout'] = self.config.session_timeout
        
        # Docker 환경 설정
        if self.config.docker_config:
            capabilities.update(self._build_docker_capabilities())
        
        # 사용자 정의 capabilities 병합
        if self.config.capabilities:
            capabilities.update(self.config.capabilities)
        
        if driver_config.capabilities:
            capabilities.update(driver_config.capabilities)
        
        return capabilities
    
    def _get_chrome_options(self, config: DriverConfig) -> Dict[str, Any]:
        """Chrome 옵션 구성"""
        args = []
        
        if config.headless:
            args.append("--headless")
        
        args.extend([
            f"--window-size={config.window_size[0]},{config.window_size[1]}",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ])
        
        if config.proxy:
            args.append(f"--proxy-server={config.proxy}")
        
        if config.user_agent:
            args.append(f"--user-agent={config.user_agent}")
        
        if config.incognito:
            args.append("--incognito")
        
        options = {"args": args}
        
        # 프리퍼런스 설정
        prefs = {}
        if config.download_dir:
            prefs["download.default_directory"] = config.download_dir
        
        if config.disable_images:
            prefs["profile.managed_default_content_settings.images"] = 2
        
        if config.disable_javascript:
            prefs["profile.managed_default_content_settings.javascript"] = 2
        
        if prefs:
            options["prefs"] = prefs
        
        return options
    
    def _get_firefox_options(self, config: DriverConfig) -> Dict[str, Any]:
        """Firefox 옵션 구성"""
        args = []
        prefs = {}
        
        if config.headless:
            args.append("--headless")
        
        args.extend([
            f"--width={config.window_size[0]}",
            f"--height={config.window_size[1]}"
        ])
        
        if config.incognito:
            args.append("--private")
        
        # 프리퍼런스 설정
        if config.proxy:
            proxy_parts = config.proxy.split(":")
            if len(proxy_parts) == 2:
                prefs["network.proxy.type"] = 1
                prefs["network.proxy.http"] = proxy_parts[0]
                prefs["network.proxy.http_port"] = int(proxy_parts[1])
        
        if config.user_agent:
            prefs["general.useragent.override"] = config.user_agent
        
        if config.download_dir:
            prefs["browser.download.dir"] = config.download_dir
            prefs["browser.download.folderList"] = 2
        
        if config.disable_images:
            prefs["permissions.default.image"] = 2
        
        if config.disable_javascript:
            prefs["javascript.enabled"] = False
        
        options = {"args": args}
        if prefs:
            options["prefs"] = prefs
        
        return options
    
    def _get_edge_options(self, config: DriverConfig) -> Dict[str, Any]:
        """Edge 옵션 구성"""
        args = []
        
        if config.headless:
            args.append("--headless")
        
        args.extend([
            f"--window-size={config.window_size[0]},{config.window_size[1]}",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ])
        
        if config.proxy:
            args.append(f"--proxy-server={config.proxy}")
        
        if config.user_agent:
            args.append(f"--user-agent={config.user_agent}")
        
        if config.incognito:
            args.append("--inprivate")
        
        return {"args": args}
    
    def _build_docker_capabilities(self) -> Dict[str, Any]:
        """Docker 환경 capabilities 구성"""
        docker_caps = {}
        
        if 'network' in self.config.docker_config:
            docker_caps['se:dockerNetwork'] = self.config.docker_config['network']
        
        if 'volumes' in self.config.docker_config:
            docker_caps['se:dockerVolumes'] = self.config.docker_config['volumes']
        
        if 'environment' in self.config.docker_config:
            docker_caps['se:dockerEnvironment'] = self.config.docker_config['environment']
        
        if 'image' in self.config.docker_config:
            docker_caps['se:dockerImage'] = self.config.docker_config['image']
        
        return docker_caps
    
    def _create_with_retry(self, capabilities: Dict[str, Any]) -> webdriver.Remote:
        """재시도 로직으로 드라이버 생성"""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.debug(f"Driver creation attempt {attempt + 1}/{self.config.retry_attempts}")
                
                driver = webdriver.Remote(
                    command_executor=self.config.hub_url,
                    desired_capabilities=capabilities,
                    keep_alive=True
                )
                
                # 연결 테스트
                driver.get("data:,")  # 빈 페이지로 연결 테스트
                
                return driver
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Driver creation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
        
        raise DriverInitializationException(f"Failed to create remote driver after {self.config.retry_attempts} attempts: {str(last_exception)}")
    
    def quit_session(self, session_id: str) -> None:
        """세션 종료"""
        with self._session_lock:
            if session_id in self._active_sessions:
                try:
                    driver = self._active_sessions[session_id]
                    driver.quit()
                    self.logger.info(f"Session {session_id} quit successfully")
                except Exception as e:
                    self.logger.warning(f"Error quitting session {session_id}: {str(e)}")
                finally:
                    del self._active_sessions[session_id]
    
    def quit_all_sessions(self) -> None:
        """모든 활성 세션 종료"""
        with self._session_lock:
            session_ids = list(self._active_sessions.keys())
        
        for session_id in session_ids:
            self.quit_session(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """활성 세션 목록 반환"""
        with self._session_lock:
            return list(self._active_sessions.keys())


class DriverPool:
    """
    드라이버 풀 관리 클래스
    
    드라이버 인스턴스를 풀링하여 재사용하고,
    리소스를 효율적으로 관리합니다.
    """
    
    def __init__(self, factory: 'DriverFactory', config: DriverPoolConfig):
        self.factory = factory
        self.config = config
        self.logger = get_logger(__name__)
        
        self._pool: Queue = Queue(maxsize=config.max_pool_size)
        self._pool_lock = threading.Lock()
        self._active_drivers: Dict[str, Dict[str, Any]] = {}
        self._pool_stats = {
            'created': 0,
            'reused': 0,
            'destroyed': 0,
            'active': 0
        }
        
        # 헬스 체크 스레드 시작
        if config.auto_cleanup:
            self._start_health_check_thread()
    
    @contextmanager
    def get_driver(self, driver_config: DriverConfig):
        """
        컨텍스트 매니저로 드라이버 대여/반납
        
        Args:
            driver_config: 드라이버 설정
            
        Yields:
            WebDriver 인스턴스
        """
        driver = None
        driver_id = None
        
        try:
            driver, driver_id = self._acquire_driver(driver_config)
            yield driver
        finally:
            if driver and driver_id:
                self._release_driver(driver, driver_id)
    
    def _acquire_driver(self, driver_config: DriverConfig) -> tuple:
        """드라이버 획득"""
        try:
            # 풀에서 사용 가능한 드라이버 찾기
            driver = self._pool.get(timeout=self.config.max_wait_time)
            driver_id = id(driver)
            
            # 드라이버 상태 확인
            if self._is_driver_healthy(driver):
                self._pool_stats['reused'] += 1
                self._pool_stats['active'] += 1
                
                with self._pool_lock:
                    self._active_drivers[str(driver_id)] = {
                        'driver': driver,
                        'acquired_at': time.time(),
                        'config': driver_config
                    }
                
                self.logger.debug(f"Reused driver from pool: {driver_id}")
                return driver, str(driver_id)
            else:
                # 비정상 드라이버는 제거하고 새로 생성
                self._destroy_driver(driver)
                
        except Empty:
            # 풀이 비어있으면 새 드라이버 생성
            pass
        
        # 새 드라이버 생성
        driver = self.factory.create_driver(driver_config)
        driver_id = str(id(driver))
        
        self._pool_stats['created'] += 1
        self._pool_stats['active'] += 1
        
        with self._pool_lock:
            self._active_drivers[driver_id] = {
                'driver': driver,
                'acquired_at': time.time(),
                'config': driver_config
            }
        
        self.logger.debug(f"Created new driver: {driver_id}")
        return driver, driver_id
    
    def _release_driver(self, driver: webdriver.Remote, driver_id: str) -> None:
        """드라이버 반납"""
        try:
            with self._pool_lock:
                if driver_id in self._active_drivers:
                    del self._active_drivers[driver_id]
                    self._pool_stats['active'] -= 1
            
            # 드라이버 상태 확인 후 풀에 반납 또는 제거
            if self._is_driver_healthy(driver):
                try:
                    self._pool.put_nowait(driver)
                    self.logger.debug(f"Returned driver to pool: {driver_id}")
                except:
                    # 풀이 가득 찬 경우 드라이버 제거
                    self._destroy_driver(driver)
            else:
                self._destroy_driver(driver)
                
        except Exception as e:
            self.logger.warning(f"Error releasing driver {driver_id}: {str(e)}")
            self._destroy_driver(driver)
    
    def _is_driver_healthy(self, driver: webdriver.Remote) -> bool:
        """드라이버 상태 확인"""
        try:
            # 간단한 상태 확인
            driver.current_url
            return True
        except Exception:
            return False
    
    def _destroy_driver(self, driver: webdriver.Remote) -> None:
        """드라이버 제거"""
        try:
            driver.quit()
            self._pool_stats['destroyed'] += 1
            self.logger.debug("Driver destroyed")
        except Exception as e:
            self.logger.warning(f"Error destroying driver: {str(e)}")
    
    def _start_health_check_thread(self) -> None:
        """헬스 체크 스레드 시작"""
        def health_check():
            while True:
                try:
                    time.sleep(self.config.health_check_interval)
                    self._cleanup_idle_drivers()
                except Exception as e:
                    self.logger.error(f"Health check error: {str(e)}")
        
        thread = threading.Thread(target=health_check, daemon=True)
        thread.start()
        self.logger.info("Driver pool health check thread started")
    
    def _cleanup_idle_drivers(self) -> None:
        """유휴 드라이버 정리"""
        current_time = time.time()
        idle_drivers = []
        
        # 풀에서 유휴 드라이버 확인
        temp_drivers = []
        while not self._pool.empty():
            try:
                driver = self._pool.get_nowait()
                if self._is_driver_healthy(driver):
                    temp_drivers.append(driver)
                else:
                    idle_drivers.append(driver)
            except Empty:
                break
        
        # 정상 드라이버는 다시 풀에 추가
        for driver in temp_drivers:
            try:
                self._pool.put_nowait(driver)
            except:
                idle_drivers.append(driver)
        
        # 유휴 드라이버 제거
        for driver in idle_drivers:
            self._destroy_driver(driver)
        
        if idle_drivers:
            self.logger.info(f"Cleaned up {len(idle_drivers)} idle drivers")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """풀 통계 정보 반환"""
        with self._pool_lock:
            return {
                **self._pool_stats,
                'pool_size': self._pool.qsize(),
                'active_drivers': len(self._active_drivers)
            }
    
    def shutdown(self) -> None:
        """풀 종료 및 모든 드라이버 정리"""
        self.logger.info("Shutting down driver pool")
        
        # 활성 드라이버 정리
        with self._pool_lock:
            active_drivers = list(self._active_drivers.values())
        
        for driver_info in active_drivers:
            self._destroy_driver(driver_info['driver'])
        
        # 풀의 드라이버 정리
        while not self._pool.empty():
            try:
                driver = self._pool.get_nowait()
                self._destroy_driver(driver)
            except Empty:
                break
        
        self.logger.info("Driver pool shutdown complete")


class DriverFactory:
    """
    브라우저 드라이버 생성을 위한 팩토리 클래스
    
    다양한 브라우저 타입과 설정 옵션을 지원하며,
    webdriver-manager를 통한 자동 드라이버 다운로드 기능을 제공합니다.
    원격 드라이버 및 드라이버 풀링도 지원합니다.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._driver_cache = {}
        self._remote_managers: Dict[str, RemoteDriverManager] = {}
        self._driver_pools: Dict[str, DriverPool] = {}
    
    def create_driver(self, config: DriverConfig) -> webdriver.Remote:
        """
        설정에 따라 적절한 브라우저 드라이버를 생성합니다.
        
        Args:
            config: 드라이버 설정 객체
            
        Returns:
            WebDriver 인스턴스
            
        Raises:
            DriverInitializationException: 드라이버 초기화 실패 시
            ConfigurationException: 잘못된 설정값 시
        """
        try:
            self.logger.info(f"Creating {config.browser.value} driver", 
                           browser=config.browser.value, 
                           headless=config.headless)
            
            # 원격 드라이버 생성
            if config.remote_url:
                return self._create_remote_driver(config)
            
            # 로컬 드라이버 생성
            if config.browser == BrowserType.CHROME:
                return self._create_chrome_driver(config)
            elif config.browser == BrowserType.FIREFOX:
                return self._create_firefox_driver(config)
            elif config.browser == BrowserType.SAFARI:
                return self._create_safari_driver(config)
            elif config.browser == BrowserType.EDGE:
                return self._create_edge_driver(config)
            else:
                raise ConfigurationException(f"Unsupported browser: {config.browser}")
                
        except Exception as e:
            self.logger.error(f"Failed to create driver: {str(e)}", 
                            browser=config.browser.value, 
                            error=str(e))
            raise DriverInitializationException(f"Failed to create {config.browser.value} driver: {str(e)}")
    
    def _create_chrome_driver(self, config: DriverConfig) -> webdriver.Chrome:
        """Chrome 드라이버 생성"""
        options = ChromeOptions()
        
        # 기본 옵션 설정
        if config.headless:
            options.add_argument("--headless")
        
        options.add_argument(f"--window-size={config.window_size[0]},{config.window_size[1]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # 프록시 설정
        if config.proxy:
            options.add_argument(f"--proxy-server={config.proxy}")
        
        # 사용자 에이전트 설정
        if config.user_agent:
            options.add_argument(f"--user-agent={config.user_agent}")
        
        # 다운로드 디렉토리 설정
        if config.download_dir:
            prefs = {"download.default_directory": config.download_dir}
            options.add_experimental_option("prefs", prefs)
        
        # 이미지 비활성화
        if config.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        # JavaScript 비활성화
        if config.disable_javascript:
            prefs = {"profile.managed_default_content_settings.javascript": 2}
            options.add_experimental_option("prefs", prefs)
        
        # 시크릿 모드
        if config.incognito:
            options.add_argument("--incognito")
        
        # 서비스 생성 (자동 드라이버 다운로드)
        service = ChromeService(ChromeDriverManager().install())
        
        return webdriver.Chrome(service=service, options=options)
    
    def _create_firefox_driver(self, config: DriverConfig) -> webdriver.Firefox:
        """Firefox 드라이버 생성"""
        options = FirefoxOptions()
        
        # 기본 옵션 설정
        if config.headless:
            options.add_argument("--headless")
        
        options.add_argument(f"--width={config.window_size[0]}")
        options.add_argument(f"--height={config.window_size[1]}")
        
        # 프록시 설정
        if config.proxy:
            proxy_parts = config.proxy.split(":")
            if len(proxy_parts) == 2:
                options.set_preference("network.proxy.type", 1)
                options.set_preference("network.proxy.http", proxy_parts[0])
                options.set_preference("network.proxy.http_port", int(proxy_parts[1]))
        
        # 사용자 에이전트 설정
        if config.user_agent:
            options.set_preference("general.useragent.override", config.user_agent)
        
        # 다운로드 디렉토리 설정
        if config.download_dir:
            options.set_preference("browser.download.dir", config.download_dir)
            options.set_preference("browser.download.folderList", 2)
        
        # 이미지 비활성화
        if config.disable_images:
            options.set_preference("permissions.default.image", 2)
        
        # JavaScript 비활성화
        if config.disable_javascript:
            options.set_preference("javascript.enabled", False)
        
        # 시크릿 모드
        if config.incognito:
            options.add_argument("--private")
        
        # 서비스 생성 (자동 드라이버 다운로드)
        service = FirefoxService(GeckoDriverManager().install())
        
        return webdriver.Firefox(service=service, options=options)
    
    def _create_safari_driver(self, config: DriverConfig) -> webdriver.Safari:
        """Safari 드라이버 생성 (macOS 전용)"""
        if os.name != 'posix':
            raise DriverInitializationException("Safari driver is only supported on macOS")
        
        options = SafariOptions()
        
        # Safari는 제한적인 옵션만 지원
        service = SafariService()
        
        return webdriver.Safari(service=service, options=options)
    
    def _create_edge_driver(self, config: DriverConfig) -> webdriver.Edge:
        """Edge 드라이버 생성"""
        options = EdgeOptions()
        
        # 기본 옵션 설정
        if config.headless:
            options.add_argument("--headless")
        
        options.add_argument(f"--window-size={config.window_size[0]},{config.window_size[1]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # 프록시 설정
        if config.proxy:
            options.add_argument(f"--proxy-server={config.proxy}")
        
        # 사용자 에이전트 설정
        if config.user_agent:
            options.add_argument(f"--user-agent={config.user_agent}")
        
        # 시크릿 모드
        if config.incognito:
            options.add_argument("--inprivate")
        
        # 서비스 생성 (자동 드라이버 다운로드)
        service = EdgeService(EdgeChromiumDriverManager().install())
        
        return webdriver.Edge(service=service, options=options)
    
    def _create_remote_driver(self, config: DriverConfig) -> webdriver.Remote:
        """원격 드라이버 생성 (기본 구현 - 호환성 유지)"""
        if not config.remote_url:
            raise ConfigurationException("Remote URL is required for remote driver")
        
        # RemoteDriverManager 사용
        remote_config = RemoteDriverConfig(
            hub_url=config.remote_url,
            browser=config.browser,
            max_sessions=config.grid_node_max_sessions,
            session_timeout=config.grid_session_timeout
        )
        
        manager_key = f"{config.remote_url}_{config.browser.value}"
        if manager_key not in self._remote_managers:
            self._remote_managers[manager_key] = RemoteDriverManager(remote_config)
        
        return self._remote_managers[manager_key].create_remote_driver(config)
    
    def create_remote_driver_advanced(self, remote_config: RemoteDriverConfig, driver_config: DriverConfig) -> webdriver.Remote:
        """
        고급 원격 드라이버 생성
        
        Args:
            remote_config: 원격 드라이버 설정
            driver_config: 기본 드라이버 설정
            
        Returns:
            Remote WebDriver 인스턴스
        """
        manager_key = f"{remote_config.hub_url}_{remote_config.browser.value}"
        if manager_key not in self._remote_managers:
            self._remote_managers[manager_key] = RemoteDriverManager(remote_config)
        
        return self._remote_managers[manager_key].create_remote_driver(driver_config)
    
    def create_driver_pool(self, pool_config: DriverPoolConfig, pool_name: str = "default") -> DriverPool:
        """
        드라이버 풀 생성
        
        Args:
            pool_config: 풀 설정
            pool_name: 풀 이름
            
        Returns:
            DriverPool 인스턴스
        """
        if pool_name in self._driver_pools:
            return self._driver_pools[pool_name]
        
        pool = DriverPool(self, pool_config)
        self._driver_pools[pool_name] = pool
        
        self.logger.info(f"Created driver pool: {pool_name}")
        return pool
    
    def get_driver_pool(self, pool_name: str = "default") -> Optional[DriverPool]:
        """드라이버 풀 반환"""
        return self._driver_pools.get(pool_name)
    
    def shutdown_all_pools(self) -> None:
        """모든 드라이버 풀 종료"""
        for pool_name, pool in self._driver_pools.items():
            pool.shutdown()
        self._driver_pools.clear()
    
    def shutdown_all_remote_managers(self) -> None:
        """모든 원격 드라이버 매니저 종료"""
        for manager_key, manager in self._remote_managers.items():
            manager.quit_all_sessions()
        self._remote_managers.clear()
    
    @staticmethod
    def create_config(browser: str, **kwargs) -> DriverConfig:
        """
        문자열 브라우저 이름으로부터 DriverConfig 생성
        
        Args:
            browser: 브라우저 이름 (chrome, firefox, safari, edge)
            **kwargs: 추가 설정 옵션
            
        Returns:
            DriverConfig 객체
        """
        try:
            browser_type = BrowserType(browser.lower())
        except ValueError:
            raise ConfigurationException(f"Unsupported browser: {browser}")
        
        return DriverConfig(browser=browser_type, **kwargs)
    
    def quit_driver(self, driver: webdriver.Remote) -> None:
        """
        드라이버를 안전하게 종료합니다.
        
        Args:
            driver: 종료할 WebDriver 인스턴스
        """
        try:
            if driver:
                driver.quit()
                self.logger.info("Driver quit successfully")
        except Exception as e:
            self.logger.warning(f"Error while quitting driver: {str(e)}")


# 편의 함수들
def create_chrome_driver(headless: bool = False, window_size: tuple = (1920, 1080)) -> webdriver.Chrome:
    """Chrome 드라이버 생성 편의 함수"""
    factory = DriverFactory()
    config = DriverConfig(
        browser=BrowserType.CHROME,
        headless=headless,
        window_size=window_size
    )
    return factory.create_driver(config)


def create_firefox_driver(headless: bool = False, window_size: tuple = (1920, 1080)) -> webdriver.Firefox:
    """Firefox 드라이버 생성 편의 함수"""
    factory = DriverFactory()
    config = DriverConfig(
        browser=BrowserType.FIREFOX,
        headless=headless,
        window_size=window_size
    )
    return factory.create_driver(config)


def create_driver_from_config(config_dict: Dict[str, Any]) -> webdriver.Remote:
    """설정 딕셔너리로부터 드라이버 생성"""
    factory = DriverFactory()
    
    browser = config_dict.pop('browser', 'chrome')
    config = DriverFactory.create_config(browser, **config_dict)
    
    return factory.create_driver(config)


def create_remote_driver(hub_url: str, browser: str = "chrome", **kwargs) -> webdriver.Remote:
    """원격 드라이버 생성 편의 함수"""
    factory = DriverFactory()
    
    # RemoteDriverConfig 생성
    remote_config = RemoteDriverConfig(
        hub_url=hub_url,
        browser=BrowserType(browser.lower()),
        **{k: v for k, v in kwargs.items() if k in ['browser_version', 'platform', 'max_sessions', 'session_timeout', 'connection_timeout', 'retry_attempts', 'retry_delay', 'capabilities', 'docker_config']}
    )
    
    # DriverConfig 생성
    driver_config = DriverFactory.create_config(
        browser,
        **{k: v for k, v in kwargs.items() if k not in ['browser_version', 'platform', 'max_sessions', 'session_timeout', 'connection_timeout', 'retry_attempts', 'retry_delay', 'capabilities', 'docker_config']}
    )
    
    return factory.create_remote_driver_advanced(remote_config, driver_config)


def create_docker_driver(hub_url: str, browser: str = "chrome", docker_image: str = None, **kwargs) -> webdriver.Remote:
    """Docker 환경에서 드라이버 생성 편의 함수"""
    docker_config = {
        'image': docker_image or f"selenium/standalone-{browser}:latest"
    }
    
    # Docker 관련 설정 추출
    if 'docker_network' in kwargs:
        docker_config['network'] = kwargs.pop('docker_network')
    
    if 'docker_volumes' in kwargs:
        docker_config['volumes'] = kwargs.pop('docker_volumes')
    
    if 'docker_environment' in kwargs:
        docker_config['environment'] = kwargs.pop('docker_environment')
    
    kwargs['docker_config'] = docker_config
    
    return create_remote_driver(hub_url, browser, **kwargs)


def create_grid_driver(hub_url: str, browser: str = "chrome", platform: str = "ANY", browser_version: str = "latest", **kwargs) -> webdriver.Remote:
    """Selenium Grid 드라이버 생성 편의 함수"""
    return create_remote_driver(
        hub_url=hub_url,
        browser=browser,
        platform=platform,
        browser_version=browser_version,
        **kwargs
    )