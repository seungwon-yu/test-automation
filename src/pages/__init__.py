"""
Pages 패키지

Page Object Pattern을 구현한 페이지 클래스들을 포함합니다.
"""

from .base_page import BasePage
from .login_page import LoginPage

__all__ = ['BasePage', 'LoginPage']