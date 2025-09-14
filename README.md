# Test Automation Framework

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/Selenium-4.35.0-green.svg)](https://selenium-python.readthedocs.io/)
[![Pytest](https://img.shields.io/badge/Pytest-8.4.2-orange.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

포트폴리오급 엔터프라이즈 웹/앱 자동화 테스트 프레임워크입니다. QA 테스트를 자동화하여 효율성을 증대시키고 CI/CD 파이프라인에 연동할 수 있는 확장 가능한 테스트 솔루션을 제공합니다.

## 🚀 주요 기능

- **Page Object Pattern**: 유지보수가 용이한 테스트 코드 구조
- **크로스 브라우저 테스트**: Chrome, Firefox, Safari, Edge 지원
- **병렬 테스트 실행**: 빠른 테스트 실행을 위한 멀티프로세싱
- **성능 모니터링**: Core Web Vitals 및 페이지 로딩 시간 측정
- **시각적 회귀 테스트**: 스크린샷 비교를 통한 UI 변경 감지
- **API 테스트**: REST API 자동화 테스트
- **자동 리포팅**: HTML, Allure 리포트 생성
- **CI/CD 통합**: GitHub Actions, Jenkins 지원
- **Docker 지원**: 컨테이너 환경에서의 테스트 실행

## 📋 요구사항

- Python 3.11+
- Windows 10/11 (현재 환경)
- Chrome, Firefox 브라우저 설치

## 🛠️ 설치 및 설정

### 1. 프로젝트 클론 및 의존성 설치

```bash
# 프로젝트 클론
git clone https://github.com/seungwon-yu/test-automation.git
cd test-automation

# 가상환경 생성 (Windows)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# 환경 변수 파일 생성
copy .env.example .env

# .env 파일을 편집하여 실제 값 입력
notepad .env
```

### 3. 브라우저 드라이버 설정

브라우저 드라이버는 webdriver-manager를 통해 자동으로 다운로드됩니다.

## 🏃‍♂️ 테스트 실행

### 기본 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 마커로 테스트 실행
pytest -m smoke
pytest -m regression
pytest -m api

# 특정 브라우저로 테스트 실행
pytest --browser=chrome
pytest --browser=firefox

# 병렬 테스트 실행
pytest -n auto
pytest -n 4
```

### 리포트 생성

```bash
# HTML 리포트 생성
pytest --html=reports/report.html

# Allure 리포트 생성
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

## 📁 프로젝트 구조

```
test-automation/
├── src/                    # 소스 코드
│   ├── core/              # 핵심 프레임워크 컴포넌트
│   ├── pages/             # Page Object 클래스
│   └── utils/             # 유틸리티 함수
├── tests/                 # 테스트 케이스
│   ├── ui/               # UI 테스트
│   └── api/              # API 테스트
├── config/               # 설정 파일
├── reports/              # 테스트 리포트
├── docs/                 # 문서
├── requirements.txt      # Python 의존성
├── pytest.ini          # Pytest 설정
└── README.md           # 프로젝트 문서
```

## 🧪 테스트 작성 예시

### Page Object 클래스

```python
from src.core.base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-btn")
    
    def login(self, username: str, password: str):
        self.input_text(self.USERNAME_INPUT, username)
        self.input_text(self.PASSWORD_INPUT, password)
        self.click_element(self.LOGIN_BUTTON)
```

### 테스트 케이스

```python
import pytest
from src.pages.login_page import LoginPage

@pytest.mark.smoke
def test_successful_login(driver):
    login_page = LoginPage(driver)
    login_page.login("admin@example.com", "admin123")
    assert login_page.is_login_successful()
```

## 🐳 Docker 실행

```bash
# Docker 이미지 빌드
docker build -t test-automation .

# Docker 컨테이너에서 테스트 실행
docker run --rm -v $(pwd)/reports:/app/reports test-automation

# Docker Compose로 병렬 실행
docker-compose up --scale test-runner=4
```

## 📊 CI/CD 통합

GitHub Actions 워크플로우가 포함되어 있어 코드 푸시 시 자동으로 테스트가 실행됩니다.

```yaml
# .github/workflows/test.yml
name: Automated Testing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    # ... (워크플로우 설정)
```

## 🔧 개발 도구

### 코드 품질

```bash
# 코드 포맷팅
black src/ tests/

# 린팅
flake8 src/ tests/

# 타입 체킹
mypy src/
```

### 테스트 커버리지

```bash
# 커버리지 리포트 생성
pytest --cov=src --cov-report=html
```

## 📈 성능 모니터링

프레임워크는 다음 성능 메트릭을 자동으로 수집합니다:

- 페이지 로딩 시간
- DOM Content Loaded 시간
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Cumulative Layout Shift (CLS)

## 🔐 보안 고려사항

- 환경 변수를 통한 민감 정보 관리
- 테스트 데이터 자동 마스킹
- HTTPS 연결 강제
- 보안 스캔 자동화 (OWASP ZAP 연동)

## 📞 지원 및 기여

이슈나 기능 요청은 GitHub Issues를 통해 제출해 주세요.

## 📄 라이선스

MIT License

## 🚧 개발 현황

**현재 진행률**: 8.0% (기초 설정 및 검증 완료)

### ✅ 완료된 작업
- [x] 프로젝트 구조 및 기본 설정 구성
- [x] Python 가상환경 및 의존성 설치 (32개 패키지)
- [x] pytest 설정 및 검증 (7개 검증 테스트 통과)
- [x] Git 저장소 초기화

### 🔄 진행 예정
- [ ] 핵심 데이터 모델 및 예외 클래스 구현
- [ ] 설정 관리 시스템 구현
- [ ] 드라이버 관리 시스템 구현
- [ ] Page Object Pattern 기반 페이지 클래스 구현
- [ ] 테스트 실행 엔진 구현

## 🏆 포트폴리오 하이라이트

이 프로젝트는 다음과 같은 실무 기술을 보여줍니다:

- **아키텍처 설계**: 모듈화된 확장 가능한 구조
- **디자인 패턴**: Page Object, Factory, Strategy 패턴 활용
- **테스트 자동화**: 포괄적인 테스트 전략 및 실행
- **DevOps**: CI/CD 파이프라인 및 컨테이너화
- **성능 최적화**: 병렬 실행 및 리소스 관리
- **모니터링**: 구조화된 로깅 및 메트릭 수집
- **보안**: 보안 테스트 및 데이터 보호

## 👨‍💻 개발자

**유승원 (Seungwon Yu)**
- GitHub: [@seungwon-yu](https://github.com/seungwon-yu)
- Email: y123587979@gmail.com