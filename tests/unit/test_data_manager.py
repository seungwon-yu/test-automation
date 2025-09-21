"""
DataManager 클래스 단위 테스트

이 모듈은 DataManager 클래스의 핵심 기능에 대한
단위 테스트를 제공합니다.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.core.data_manager import (
    DataManager,
    DataManagerConfig,
    TestUser,
    TestProduct,
    TestOrder,
    create_test_data_manager,
    create_sample_data
)
from src.core.exceptions import (
    TestDataException,
    TestDataGenerationException,
    TestDataCleanupException
)


class TestDataManagerConfig:
    """DataManagerConfig 클래스 테스트"""
    
    def test_config_default_values(self):
        """기본 설정값 테스트"""
        config = DataManagerConfig()
        
        assert config.database_path == "test_data.db"
        assert config.auto_cleanup is True
        assert config.cleanup_interval == 3600
        assert config.data_retention_days == 7
        assert config.max_users == 1000
        assert config.max_products == 500
        assert config.max_orders == 200
        assert config.locale == "ko_KR"
        assert config.seed is None
    
    def test_config_custom_values(self):
        """커스텀 설정값 테스트"""
        config = DataManagerConfig(
            database_path="custom.db",
            auto_cleanup=False,
            cleanup_interval=1800,
            data_retention_days=14,
            max_users=500,
            locale="en_US",
            seed=12345
        )
        
        assert config.database_path == "custom.db"
        assert config.auto_cleanup is False
        assert config.cleanup_interval == 1800
        assert config.data_retention_days == 14
        assert config.max_users == 500
        assert config.locale == "en_US"
        assert config.seed == 12345


class TestTestUser:
    """TestUser 데이터 모델 테스트"""
    
    def test_user_default_creation(self):
        """기본 사용자 생성 테스트"""
        user = TestUser()
        
        assert user.user_id is not None
        assert len(user.user_id) > 0
        assert user.username == ""
        assert user.email == ""
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.metadata, dict)
    
    def test_user_custom_creation(self):
        """커스텀 사용자 생성 테스트"""
        user = TestUser(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=False
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is False


class TestTestProduct:
    """TestProduct 데이터 모델 테스트"""
    
    def test_product_default_creation(self):
        """기본 상품 생성 테스트"""
        product = TestProduct()
        
        assert product.product_id is not None
        assert len(product.product_id) > 0
        assert product.name == ""
        assert product.price == 0.0
        assert product.stock == 0
        assert product.is_available is True
        assert isinstance(product.created_at, datetime)
    
    def test_product_custom_creation(self):
        """커스텀 상품 생성 테스트"""
        product = TestProduct(
            name="Test Product",
            price=99.99,
            category="Electronics",
            stock=50,
            is_available=False
        )
        
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.category == "Electronics"
        assert product.stock == 50
        assert product.is_available is False


class TestTestOrder:
    """TestOrder 데이터 모델 테스트"""
    
    def test_order_default_creation(self):
        """기본 주문 생성 테스트"""
        order = TestOrder()
        
        assert order.order_id is not None
        assert len(order.order_id) > 0
        assert order.user_id == ""
        assert order.products == []
        assert order.total_amount == 0.0
        assert order.status == "pending"
        assert isinstance(order.created_at, datetime)
    
    def test_order_custom_creation(self):
        """커스텀 주문 생성 테스트"""
        products = [
            {"product_id": "prod1", "quantity": 2, "price": 50.0},
            {"product_id": "prod2", "quantity": 1, "price": 30.0}
        ]
        
        order = TestOrder(
            user_id="user123",
            products=products,
            total_amount=130.0,
            status="completed"
        )
        
        assert order.user_id == "user123"
        assert order.products == products
        assert order.total_amount == 130.0
        assert order.status == "completed"


class TestDataManager:
    """DataManager 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.config = DataManagerConfig(
            database_path=self.temp_db.name,
            auto_cleanup=False,  # 테스트에서는 자동 정리 비활성화
            seed=12345  # 일관된 테스트 데이터를 위한 시드
        )
        
        self.mock_logger = Mock()
        
        with patch('src.core.data_manager.get_logger', return_value=self.mock_logger):
            self.data_manager = DataManager(self.config)
    
    def teardown_method(self):
        """각 테스트 메서드 실행 후 정리"""
        try:
            self.data_manager.stop_cleanup()
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_data_manager_initialization(self):
        """DataManager 초기화 테스트"""
        assert self.data_manager.config == self.config
        assert self.data_manager.faker is not None
        assert self.data_manager._db_path == Path(self.temp_db.name)
        assert os.path.exists(self.temp_db.name)
    
    def test_database_initialization(self):
        """데이터베이스 초기화 테스트"""
        # 테이블 존재 확인
        with self.data_manager._get_connection() as conn:
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'test_%'
            """).fetchall()
            
            table_names = [table[0] for table in tables]
            assert 'test_users' in table_names
            assert 'test_products' in table_names
            assert 'test_orders' in table_names
    
    def test_create_user_success(self):
        """사용자 생성 성공 테스트"""
        user = self.data_manager.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.user_id is not None
        
        # 데이터베이스에서 확인
        retrieved_user = self.data_manager.get_user(user_id=user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
    
    def test_create_user_with_faker_data(self):
        """Faker 데이터로 사용자 생성 테스트"""
        user = self.data_manager.create_user()
        
        assert user.username != ""
        assert user.email != ""
        assert user.first_name != ""
        assert user.last_name != ""
        assert "@" in user.email
    
    def test_get_user_by_id(self):
        """사용자 ID로 조회 테스트"""
        # 사용자 생성
        created_user = self.data_manager.create_user(username="testuser")
        
        # ID로 조회
        retrieved_user = self.data_manager.get_user(user_id=created_user.user_id)
        
        assert retrieved_user is not None
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.username == "testuser"
    
    def test_get_user_by_username(self):
        """사용자명으로 조회 테스트"""
        # 사용자 생성
        self.data_manager.create_user(username="testuser")
        
        # 사용자명으로 조회
        retrieved_user = self.data_manager.get_user(username="testuser")
        
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
    
    def test_get_user_by_email(self):
        """이메일로 조회 테스트"""
        # 사용자 생성
        self.data_manager.create_user(email="test@example.com")
        
        # 이메일로 조회
        retrieved_user = self.data_manager.get_user(email="test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
    
    def test_get_user_not_found(self):
        """존재하지 않는 사용자 조회 테스트"""
        user = self.data_manager.get_user(user_id="nonexistent")
        assert user is None
    
    def test_get_users_list(self):
        """사용자 목록 조회 테스트"""
        # 여러 사용자 생성
        for i in range(5):
            self.data_manager.create_user(username=f"user{i}")
        
        # 목록 조회
        users = self.data_manager.get_users(limit=10)
        
        assert len(users) == 5
        assert all(isinstance(user, TestUser) for user in users)
    
    def test_update_user_success(self):
        """사용자 정보 업데이트 성공 테스트"""
        # 사용자 생성
        user = self.data_manager.create_user(username="testuser")
        
        # 정보 업데이트
        success = self.data_manager.update_user(
            user.user_id,
            first_name="Updated",
            email="updated@example.com"
        )
        
        assert success is True
        
        # 업데이트된 정보 확인
        updated_user = self.data_manager.get_user(user_id=user.user_id)
        assert updated_user.first_name == "Updated"
        assert updated_user.email == "updated@example.com"
    
    def test_delete_user_success(self):
        """사용자 삭제 성공 테스트"""
        # 사용자 생성
        user = self.data_manager.create_user(username="testuser")
        
        # 삭제
        success = self.data_manager.delete_user(user.user_id)
        assert success is True
        
        # 삭제 확인
        deleted_user = self.data_manager.get_user(user_id=user.user_id)
        assert deleted_user is None
    
    def test_create_product_success(self):
        """상품 생성 성공 테스트"""
        product = self.data_manager.create_product(
            name="Test Product",
            price=99.99,
            category="Electronics",
            stock=50
        )
        
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.category == "Electronics"
        assert product.stock == 50
        assert product.product_id is not None
        
        # 데이터베이스에서 확인
        retrieved_product = self.data_manager.get_product(product_id=product.product_id)
        assert retrieved_product is not None
        assert retrieved_product.name == "Test Product"
    
    def test_get_products_list(self):
        """상품 목록 조회 테스트"""
        # 여러 상품 생성
        for i in range(3):
            self.data_manager.create_product(name=f"Product {i}")
        
        # 목록 조회
        products = self.data_manager.get_products(limit=10)
        
        assert len(products) == 3
        assert all(isinstance(product, TestProduct) for product in products)
    
    def test_create_order_success(self):
        """주문 생성 성공 테스트"""
        # 사용자와 상품 생성
        user = self.data_manager.create_user(username="testuser")
        product1 = self.data_manager.create_product(name="Product 1", price=50.0)
        product2 = self.data_manager.create_product(name="Product 2", price=30.0)
        
        # 주문 생성
        order_products = [
            {"product_id": product1.product_id, "quantity": 2, "price": 50.0},
            {"product_id": product2.product_id, "quantity": 1, "price": 30.0}
        ]
        
        order = self.data_manager.create_order(user.user_id, order_products)
        
        assert order.user_id == user.user_id
        assert order.products == order_products
        assert order.total_amount == 130.0  # (50*2) + (30*1)
        assert order.order_id is not None
    
    def test_create_bulk_users(self):
        """대량 사용자 생성 테스트"""
        users = self.data_manager.create_bulk_users(5)
        
        assert len(users) == 5
        assert all(isinstance(user, TestUser) for user in users)
        assert all(user.username != "" for user in users)
        
        # 데이터베이스에서 확인
        db_users = self.data_manager.get_users(limit=10)
        assert len(db_users) == 5
    
    def test_create_bulk_products(self):
        """대량 상품 생성 테스트"""
        products = self.data_manager.create_bulk_products(3)
        
        assert len(products) == 3
        assert all(isinstance(product, TestProduct) for product in products)
        assert all(product.name != "" for product in products)
        
        # 데이터베이스에서 확인
        db_products = self.data_manager.get_products(limit=10)
        assert len(db_products) == 3
    
    def test_get_data_stats(self):
        """데이터 통계 조회 테스트"""
        # 초기 상태
        stats = self.data_manager.get_data_stats()
        assert stats['users'] == 0
        assert stats['products'] == 0
        assert stats['orders'] == 0
        assert stats['total'] == 0
        
        # 데이터 생성 후
        user = self.data_manager.create_user()
        product = self.data_manager.create_product()
        self.data_manager.create_order(user.user_id, [{"product_id": product.product_id, "quantity": 1, "price": 10.0}])
        
        stats = self.data_manager.get_data_stats()
        assert stats['users'] == 1
        assert stats['products'] == 1
        assert stats['orders'] == 1
        assert stats['total'] == 3
    
    def test_clear_all_data(self):
        """모든 데이터 삭제 테스트"""
        # 데이터 생성
        user = self.data_manager.create_user()
        product = self.data_manager.create_product()
        self.data_manager.create_order(user.user_id, [{"product_id": product.product_id, "quantity": 1, "price": 10.0}])
        
        # 데이터 존재 확인
        stats_before = self.data_manager.get_data_stats()
        assert stats_before['total'] > 0
        
        # 모든 데이터 삭제
        success = self.data_manager.clear_all_data()
        assert success is True
        
        # 삭제 확인
        stats_after = self.data_manager.get_data_stats()
        assert stats_after['total'] == 0
    
    def test_cleanup_old_data(self):
        """오래된 데이터 정리 테스트"""
        # 오래된 데이터 생성 (수동으로 날짜 조작)
        user = self.data_manager.create_user()
        old_date = datetime.now() - timedelta(days=10)
        
        with self.data_manager._get_connection() as conn:
            conn.execute(
                "UPDATE test_users SET created_at = ? WHERE user_id = ?",
                (old_date, user.user_id)
            )
            conn.commit()
        
        # 정리 실행 (7일 기준)
        cleanup_stats = self.data_manager.cleanup_old_data(days=7)
        
        assert cleanup_stats['users'] == 1
        assert cleanup_stats['products'] == 0
        assert cleanup_stats['orders'] == 0
        
        # 삭제 확인
        remaining_user = self.data_manager.get_user(user_id=user.user_id)
        assert remaining_user is None


class TestConvenienceFunctions:
    """편의 함수들 테스트"""
    
    def test_create_test_data_manager(self):
        """테스트 데이터 매니저 생성 함수 테스트"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            config = DataManagerConfig(
                database_path=temp_db.name,
                auto_cleanup=False
            )
            
            with patch('src.core.data_manager.get_logger'):
                manager = create_test_data_manager(config)
                
                assert isinstance(manager, DataManager)
                assert manager.config == config
                
                # 정리
                manager.stop_cleanup()
                try:
                    os.unlink(temp_db.name)
                except PermissionError:
                    pass  # Windows에서 파일이 사용 중일 수 있음
    
    def test_create_sample_data(self):
        """샘플 데이터 생성 함수 테스트"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            config = DataManagerConfig(
                database_path=temp_db.name,
                auto_cleanup=False,
                seed=12345
            )
            
            with patch('src.core.data_manager.get_logger'):
                manager = DataManager(config)
                
                # 샘플 데이터 생성
                sample_data = create_sample_data(manager, users=3, products=5)
                
                assert 'users' in sample_data
                assert 'products' in sample_data
                assert 'orders' in sample_data
                
                assert len(sample_data['users']) == 3
                assert len(sample_data['products']) == 5
                assert len(sample_data['orders']) <= 3  # 최대 3개 (사용자 수만큼)
                
                # 정리
                manager.stop_cleanup()
                try:
                    os.unlink(temp_db.name)
                except PermissionError:
                    pass  # Windows에서 파일이 사용 중일 수 있음


class TestDataManagerExceptions:
    """DataManager 예외 처리 테스트"""
    
    def test_database_initialization_failure(self):
        """데이터베이스 초기화 실패 테스트"""
        # 잘못된 경로로 데이터베이스 생성 시도
        config = DataManagerConfig(database_path="/invalid/path/test.db")
        
        with patch('src.core.data_manager.get_logger'):
            with pytest.raises(TestDataException):
                DataManager(config)
    
    def test_user_creation_failure(self):
        """사용자 생성 실패 테스트"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            config = DataManagerConfig(
                database_path=temp_db.name,
                auto_cleanup=False
            )
            
            with patch('src.core.data_manager.get_logger'):
                manager = DataManager(config)
                
                # 데이터베이스 연결 실패 시뮬레이션
                with patch.object(manager, '_get_connection', side_effect=Exception("DB Error")):
                    with pytest.raises(TestDataGenerationException):
                        manager.create_user()
                
                # 정리
                manager.stop_cleanup()
                try:
                    os.unlink(temp_db.name)
                except PermissionError:
                    pass  # Windows에서 파일이 사용 중일 수 있음
    
    def test_cleanup_failure(self):
        """데이터 정리 실패 테스트"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            config = DataManagerConfig(
                database_path=temp_db.name,
                auto_cleanup=False
            )
            
            with patch('src.core.data_manager.get_logger'):
                manager = DataManager(config)
                
                # 데이터베이스 연결 실패 시뮬레이션
                with patch.object(manager, '_get_connection', side_effect=Exception("DB Error")):
                    with pytest.raises(TestDataCleanupException):
                        manager.cleanup_old_data()
                
                # 정리
                manager.stop_cleanup()
                try:
                    os.unlink(temp_db.name)
                except PermissionError:
                    pass  # Windows에서 파일이 사용 중일 수 있음