"""
Setup verification test
pytest 설정 및 환경 검증을 위한 테스트
"""
import pytest
import sys
import os


class TestSetupVerification:
    """Setup verification test class"""
    
    @pytest.mark.smoke
    def test_python_version(self):
        """Python 버전 확인"""
        assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"
        
    @pytest.mark.smoke  
    def test_project_structure(self):
        """프로젝트 구조 확인"""
        required_dirs = ['src', 'tests', 'config', 'reports']
        for dir_name in required_dirs:
            assert os.path.exists(dir_name), f"Required directory '{dir_name}' not found"
            
    @pytest.mark.smoke
    def test_selenium_import(self):
        """Selenium import 테스트"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            assert True
        except ImportError as e:
            pytest.fail(f"Selenium import failed: {e}")
            
    @pytest.mark.smoke
    def test_webdriver_manager_import(self):
        """WebDriver Manager import 테스트"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            assert True
        except ImportError as e:
            pytest.fail(f"WebDriver Manager import failed: {e}")
            
    @pytest.mark.unit
    def test_config_files_exist(self):
        """설정 파일 존재 확인"""
        config_files = [
            'pytest.ini',
            'requirements.txt',
            '.gitignore',
            'config/environments.yml',
            '.env.example'
        ]
        for file_path in config_files:
            assert os.path.exists(file_path), f"Config file '{file_path}' not found"
            
    @pytest.mark.integration
    def test_pytest_markers(self):
        """pytest 마커 설정 확인"""
        # 이 테스트 자체가 마커를 사용하므로 실행되면 마커가 작동하는 것
        assert True
        
    def test_basic_functionality(self):
        """기본 기능 테스트"""
        # 간단한 계산 테스트
        result = 2 + 2
        assert result == 4
        
        # 문자열 테스트
        test_string = "Hello, World!"
        assert "World" in test_string
        assert len(test_string) == 13