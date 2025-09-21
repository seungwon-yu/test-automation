"""
드라이버 팩토리 모듈

이 모듈은 다양한 브라우저 드라이버를 생성하고 관리하는 팩토리 클래스를 제공합니다.
Chrome, Firefox, Safari 등 다양한 브라우저를 지원하며, 헤드리스 모드, 윈도우 크기 설정,
프록시 설정 등 다양한 옵션을 제공합니다.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass

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


class DriverFactory:
    """
    브라우저 드라이버 생성을 위한 팩토리 클래스
    
    다양한 브라우저 타입과 설정 옵션을 지원하며,
    webdriver-manager를 통한 자동 드라이버 다운로드 기능을 제공합니다.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._driver_cache = {}
    
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
        """원격 드라이버 생성 (Selenium Grid용)"""
        capabilities = DesiredCapabilities.CHROME.copy()
        
        if config.browser == BrowserType.FIREFOX:
            capabilities = DesiredCapabilities.FIREFOX.copy()
        elif config.browser == BrowserType.SAFARI:
            capabilities = DesiredCapabilities.SAFARI.copy()
        elif config.browser == BrowserType.EDGE:
            capabilities = DesiredCapabilities.EDGE.copy()
        
        # 사용자 정의 capabilities 병합
        if config.capabilities:
            capabilities.update(config.capabilities)
        
        return webdriver.Remote(
            command_executor=config.remote_url,
            desired_capabilities=capabilities
        )
    
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
    config = DriverConfig.create_config(browser, **config_dict)
    
    return factory.create_driver(config)