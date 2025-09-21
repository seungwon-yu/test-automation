"""
DataManager 클래스 - 테스트 데이터 관리 시스템

이 모듈은 테스트 데이터의 생성, 관리, 정리를 담당합니다.
데이터베이스 연동, 테스트 데이터 CRUD 작업, 자동 정리 기능을 제공합니다.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from faker import Faker
import threading
import time

from .logging import get_logger
from .exceptions import (
    TestDataException,
    TestDataGenerationException,
    TestDataCleanupException
)


@dataclass
class TestUser:
    """테스트 사용자 데이터 모델"""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestProduct:
    """테스트 상품 데이터 모델"""
    product_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    price: float = 0.0
    category: str = ""
    stock: int = 0
    sku: str = ""
    brand: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestOrder:
    """테스트 주문 데이터 모델"""
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    products: List[Dict[str, Any]] = field(default_factory=list)
    total_amount: float = 0.0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==================== 범용 데이터 모델 (확장) ====================

@dataclass
class TestPerson:
    """범용 사람 정보 데이터 모델"""
    person_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    role: str = "user"  # user, admin, employee, student, teacher 등
    department: str = ""
    position: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestContent:
    """범용 콘텐츠 데이터 모델"""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    body: str = ""
    content_type: str = "article"  # article, post, notice, course, document 등
    author_id: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, published, archived
    view_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestRecord:
    """범용 레코드/로그 데이터 모델"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_type: str = "log"  # log, transaction, activity, event 등
    title: str = ""
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    person_id: str = ""
    level: str = "info"  # debug, info, warning, error, critical
    source: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataManagerConfig:
    """DataManager 설정"""
    database_path: str = "test_data.db"
    auto_cleanup: bool = True
    cleanup_interval: int = 3600  # 1시간
    data_retention_days: int = 7
    max_users: int = 1000
    max_products: int = 500
    max_orders: int = 200
    locale: str = "ko_KR"
    seed: Optional[int] = None


class DataManager:
    """
    테스트 데이터 관리 클래스
    
    테스트 데이터의 생성, 저장, 조회, 삭제를 관리하며
    자동 정리 기능을 제공합니다.
    """
    
    def __init__(self, config: DataManagerConfig = None):
        """
        DataManager 초기화
        
        Args:
            config: DataManager 설정
        """
        self.config = config or DataManagerConfig()
        self.logger = get_logger(self.__class__.__name__)
        self.faker = Faker(self.config.locale)
        
        if self.config.seed:
            Faker.seed(self.config.seed)
        
        self._db_path = Path(self.config.database_path)
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 자동 정리 시작
        if self.config.auto_cleanup:
            self._start_cleanup_thread()
        
        self.logger.debug("DataManager initialized")
    
    def _init_database(self) -> None:
        """데이터베이스 초기화"""
        try:
            with self._get_connection() as conn:
                # 사용자 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE,
                        email TEXT UNIQUE,
                        password TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        phone TEXT,
                        address TEXT,
                        city TEXT,
                        country TEXT,
                        created_at TIMESTAMP,
                        is_active BOOLEAN,
                        metadata TEXT
                    )
                """)
                
                # 상품 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_products (
                        product_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        price REAL,
                        category TEXT,
                        stock INTEGER,
                        sku TEXT UNIQUE,
                        brand TEXT,
                        created_at TIMESTAMP,
                        is_available BOOLEAN,
                        metadata TEXT
                    )
                """)
                
                # 주문 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_orders (
                        order_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        products TEXT,
                        total_amount REAL,
                        status TEXT,
                        created_at TIMESTAMP,
                        metadata TEXT,
                        FOREIGN KEY (user_id) REFERENCES test_users (user_id)
                    )
                """)
                
                # 범용 데이터 테이블들
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_persons (
                        person_id TEXT PRIMARY KEY,
                        name TEXT,
                        email TEXT UNIQUE,
                        phone TEXT,
                        address TEXT,
                        role TEXT,
                        department TEXT,
                        position TEXT,
                        created_at TIMESTAMP,
                        is_active BOOLEAN,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_contents (
                        content_id TEXT PRIMARY KEY,
                        title TEXT,
                        body TEXT,
                        content_type TEXT,
                        author_id TEXT,
                        category TEXT,
                        tags TEXT,
                        status TEXT,
                        view_count INTEGER,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_records (
                        record_id TEXT PRIMARY KEY,
                        record_type TEXT,
                        title TEXT,
                        description TEXT,
                        data TEXT,
                        person_id TEXT,
                        level TEXT,
                        source TEXT,
                        created_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                # 인덱스 생성
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON test_users(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_products_created_at ON test_products(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON test_orders(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_persons_created_at ON test_persons(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_contents_created_at ON test_contents(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_records_created_at ON test_records(created_at)")
                
                conn.commit()
                self.logger.debug("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise TestDataException(f"Database initialization failed: {str(e)}")
    
    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    # ==================== 사용자 데이터 관리 ====================
    
    def create_user(self, **kwargs) -> TestUser:
        """
        테스트 사용자 생성
        
        Args:
            **kwargs: 사용자 속성 오버라이드
            
        Returns:
            생성된 TestUser 객체
        """
        try:
            user = TestUser(
                username=kwargs.get('username', self.faker.user_name()),
                email=kwargs.get('email', self.faker.email()),
                password=kwargs.get('password', self.faker.password()),
                first_name=kwargs.get('first_name', self.faker.first_name()),
                last_name=kwargs.get('last_name', self.faker.last_name()),
                phone=kwargs.get('phone', self.faker.phone_number()),
                address=kwargs.get('address', self.faker.address()),
                city=kwargs.get('city', self.faker.city()),
                country=kwargs.get('country', self.faker.country()),
                **{k: v for k, v in kwargs.items() if k not in [
                    'username', 'email', 'password', 'first_name', 'last_name',
                    'phone', 'address', 'city', 'country'
                ]}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_users 
                    (user_id, username, email, password, first_name, last_name,
                     phone, address, city, country, created_at, is_active, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.password,
                    user.first_name, user.last_name, user.phone, user.address,
                    user.city, user.country, user.created_at, user.is_active,
                    json.dumps(user.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test user: {user.username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            raise TestDataGenerationException("user", str(e))
    
    def get_user(self, user_id: str = None, username: str = None, email: str = None) -> Optional[TestUser]:
        """
        사용자 조회
        
        Args:
            user_id: 사용자 ID
            username: 사용자명
            email: 이메일
            
        Returns:
            TestUser 객체 또는 None
        """
        try:
            with self._get_connection() as conn:
                if user_id:
                    row = conn.execute("SELECT * FROM test_users WHERE user_id = ?", (user_id,)).fetchone()
                elif username:
                    row = conn.execute("SELECT * FROM test_users WHERE username = ?", (username,)).fetchone()
                elif email:
                    row = conn.execute("SELECT * FROM test_users WHERE email = ?", (email,)).fetchone()
                else:
                    return None
                
                if row:
                    return TestUser(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone=row['phone'],
                        address=row['address'],
                        city=row['city'],
                        country=row['country'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_active=bool(row['is_active']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get user: {str(e)}")
            return None
    
    def get_users(self, limit: int = 100, active_only: bool = True) -> List[TestUser]:
        """
        사용자 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            active_only: 활성 사용자만 조회 여부
            
        Returns:
            TestUser 객체 리스트
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM test_users"
                params = []
                
                if active_only:
                    query += " WHERE is_active = ?"
                    params.append(True)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                users = []
                for row in rows:
                    users.append(TestUser(
                        user_id=row['user_id'],
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone=row['phone'],
                        address=row['address'],
                        city=row['city'],
                        country=row['country'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_active=bool(row['is_active']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return users
                
        except Exception as e:
            self.logger.error(f"Failed to get users: {str(e)}")
            return []
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        사용자 정보 업데이트
        
        Args:
            user_id: 사용자 ID
            **kwargs: 업데이트할 속성들
            
        Returns:
            업데이트 성공 여부
        """
        try:
            if not kwargs:
                return True
            
            # 업데이트 가능한 필드들
            allowed_fields = {
                'username', 'email', 'password', 'first_name', 'last_name',
                'phone', 'address', 'city', 'country', 'is_active'
            }
            
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
                elif field == 'metadata':
                    update_fields.append("metadata = ?")
                    params.append(json.dumps(value))
            
            if not update_fields:
                return True
            
            params.append(user_id)
            
            with self._get_connection() as conn:
                query = f"UPDATE test_users SET {', '.join(update_fields)} WHERE user_id = ?"
                result = conn.execute(query, params)
                conn.commit()
                
                success = result.rowcount > 0
                if success:
                    self.logger.debug(f"Updated user: {user_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update user: {str(e)}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """
        사용자 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            with self._get_connection() as conn:
                # 관련 주문도 함께 삭제
                conn.execute("DELETE FROM test_orders WHERE user_id = ?", (user_id,))
                result = conn.execute("DELETE FROM test_users WHERE user_id = ?", (user_id,))
                conn.commit()
                
                success = result.rowcount > 0
                if success:
                    self.logger.debug(f"Deleted user: {user_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete user: {str(e)}")
            return False
    
    # ==================== 상품 데이터 관리 ====================
    
    def create_product(self, **kwargs) -> TestProduct:
        """
        테스트 상품 생성
        
        Args:
            **kwargs: 상품 속성 오버라이드
            
        Returns:
            생성된 TestProduct 객체
        """
        try:
            product = TestProduct(
                name=kwargs.get('name', self.faker.catch_phrase()),
                description=kwargs.get('description', self.faker.text()),
                price=kwargs.get('price', round(self.faker.random.uniform(10.0, 1000.0), 2)),
                category=kwargs.get('category', self.faker.word()),
                stock=kwargs.get('stock', self.faker.random_int(0, 100)),
                sku=kwargs.get('sku', self.faker.ean13()),
                brand=kwargs.get('brand', self.faker.company()),
                **{k: v for k, v in kwargs.items() if k not in [
                    'name', 'description', 'price', 'category', 'stock', 'sku', 'brand'
                ]}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_products 
                    (product_id, name, description, price, category, stock, sku, brand,
                     created_at, is_available, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product.product_id, product.name, product.description, product.price,
                    product.category, product.stock, product.sku, product.brand,
                    product.created_at, product.is_available, json.dumps(product.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test product: {product.name}")
            return product
            
        except Exception as e:
            self.logger.error(f"Failed to create product: {str(e)}")
            raise TestDataGenerationException("product", str(e))
    
    def get_product(self, product_id: str = None, sku: str = None) -> Optional[TestProduct]:
        """
        상품 조회
        
        Args:
            product_id: 상품 ID
            sku: SKU
            
        Returns:
            TestProduct 객체 또는 None
        """
        try:
            with self._get_connection() as conn:
                if product_id:
                    row = conn.execute("SELECT * FROM test_products WHERE product_id = ?", (product_id,)).fetchone()
                elif sku:
                    row = conn.execute("SELECT * FROM test_products WHERE sku = ?", (sku,)).fetchone()
                else:
                    return None
                
                if row:
                    return TestProduct(
                        product_id=row['product_id'],
                        name=row['name'],
                        description=row['description'],
                        price=row['price'],
                        category=row['category'],
                        stock=row['stock'],
                        sku=row['sku'],
                        brand=row['brand'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_available=bool(row['is_available']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get product: {str(e)}")
            return None
    
    def get_products(self, limit: int = 100, category: str = None, available_only: bool = True) -> List[TestProduct]:
        """
        상품 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            category: 카테고리 필터
            available_only: 판매 가능한 상품만 조회 여부
            
        Returns:
            TestProduct 객체 리스트
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM test_products"
                params = []
                conditions = []
                
                if available_only:
                    conditions.append("is_available = ?")
                    params.append(True)
                
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                products = []
                for row in rows:
                    products.append(TestProduct(
                        product_id=row['product_id'],
                        name=row['name'],
                        description=row['description'],
                        price=row['price'],
                        category=row['category'],
                        stock=row['stock'],
                        sku=row['sku'],
                        brand=row['brand'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_available=bool(row['is_available']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return products
                
        except Exception as e:
            self.logger.error(f"Failed to get products: {str(e)}")
            return []
    
    # ==================== 주문 데이터 관리 ====================
    
    def create_order(self, user_id: str, products: List[Dict[str, Any]], **kwargs) -> TestOrder:
        """
        테스트 주문 생성
        
        Args:
            user_id: 사용자 ID
            products: 주문 상품 리스트 [{'product_id': str, 'quantity': int, 'price': float}]
            **kwargs: 주문 속성 오버라이드
            
        Returns:
            생성된 TestOrder 객체
        """
        try:
            total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in products)
            
            order = TestOrder(
                user_id=user_id,
                products=products,
                total_amount=kwargs.get('total_amount', total_amount),
                status=kwargs.get('status', 'pending'),
                **{k: v for k, v in kwargs.items() if k not in ['total_amount', 'status']}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_orders 
                    (order_id, user_id, products, total_amount, status, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    order.order_id, order.user_id, json.dumps(order.products),
                    order.total_amount, order.status, order.created_at,
                    json.dumps(order.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test order: {order.order_id}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to create order: {str(e)}")
            raise TestDataGenerationException("order", str(e))
    
    # ==================== 대량 데이터 생성 ====================
    
    def create_bulk_users(self, count: int) -> List[TestUser]:
        """
        대량 사용자 생성
        
        Args:
            count: 생성할 사용자 수
            
        Returns:
            생성된 TestUser 객체 리스트
        """
        users = []
        try:
            for i in range(count):
                user = self.create_user()
                users.append(user)
                
                if (i + 1) % 100 == 0:
                    self.logger.debug(f"Created {i + 1}/{count} users")
            
            self.logger.info(f"Created {count} test users")
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to create bulk users: {str(e)}")
            raise TestDataGenerationException("bulk_users", str(e))
    
    def create_bulk_products(self, count: int) -> List[TestProduct]:
        """
        대량 상품 생성
        
        Args:
            count: 생성할 상품 수
            
        Returns:
            생성된 TestProduct 객체 리스트
        """
        products = []
        try:
            categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Beauty']
            
            for i in range(count):
                product = self.create_product(
                    category=self.faker.random.choice(categories)
                )
                products.append(product)
                
                if (i + 1) % 50 == 0:
                    self.logger.debug(f"Created {i + 1}/{count} products")
            
            self.logger.info(f"Created {count} test products")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to create bulk products: {str(e)}")
            raise TestDataGenerationException("bulk_products", str(e))
    
    # ==================== 범용 데이터 관리 (확장) ====================
    
    def create_person(self, **kwargs) -> TestPerson:
        """
        범용 사람 정보 생성
        
        Args:
            **kwargs: 사람 속성 오버라이드
            
        Returns:
            생성된 TestPerson 객체
        """
        try:
            person = TestPerson(
                name=kwargs.get('name', self.faker.name()),
                email=kwargs.get('email', self.faker.email()),
                phone=kwargs.get('phone', self.faker.phone_number()),
                address=kwargs.get('address', self.faker.address()),
                role=kwargs.get('role', 'user'),
                department=kwargs.get('department', self.faker.word()),
                position=kwargs.get('position', self.faker.job()),
                **{k: v for k, v in kwargs.items() if k not in [
                    'name', 'email', 'phone', 'address', 'role', 'department', 'position'
                ]}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_persons 
                    (person_id, name, email, phone, address, role, department, position,
                     created_at, is_active, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    person.person_id, person.name, person.email, person.phone,
                    person.address, person.role, person.department, person.position,
                    person.created_at, person.is_active, json.dumps(person.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test person: {person.name}")
            return person
            
        except Exception as e:
            self.logger.error(f"Failed to create person: {str(e)}")
            raise TestDataGenerationException("person", str(e))
    
    def create_content(self, **kwargs) -> TestContent:
        """
        범용 콘텐츠 생성
        
        Args:
            **kwargs: 콘텐츠 속성 오버라이드
            
        Returns:
            생성된 TestContent 객체
        """
        try:
            content = TestContent(
                title=kwargs.get('title', self.faker.sentence()),
                body=kwargs.get('body', self.faker.text()),
                content_type=kwargs.get('content_type', 'article'),
                author_id=kwargs.get('author_id', ''),
                category=kwargs.get('category', self.faker.word()),
                tags=kwargs.get('tags', [self.faker.word() for _ in range(3)]),
                status=kwargs.get('status', 'draft'),
                view_count=kwargs.get('view_count', self.faker.random_int(0, 1000)),
                **{k: v for k, v in kwargs.items() if k not in [
                    'title', 'body', 'content_type', 'author_id', 'category', 'tags', 'status', 'view_count'
                ]}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_contents 
                    (content_id, title, body, content_type, author_id, category, tags,
                     status, view_count, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content.content_id, content.title, content.body, content.content_type,
                    content.author_id, content.category, json.dumps(content.tags),
                    content.status, content.view_count, content.created_at,
                    content.updated_at, json.dumps(content.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test content: {content.title}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to create content: {str(e)}")
            raise TestDataGenerationException("content", str(e))
    
    def create_record(self, **kwargs) -> TestRecord:
        """
        범용 레코드/로그 생성
        
        Args:
            **kwargs: 레코드 속성 오버라이드
            
        Returns:
            생성된 TestRecord 객체
        """
        try:
            record = TestRecord(
                record_type=kwargs.get('record_type', 'log'),
                title=kwargs.get('title', self.faker.sentence()),
                description=kwargs.get('description', self.faker.text()),
                data=kwargs.get('data', {'action': self.faker.word(), 'result': 'success'}),
                person_id=kwargs.get('person_id', ''),
                level=kwargs.get('level', 'info'),
                source=kwargs.get('source', self.faker.word()),
                **{k: v for k, v in kwargs.items() if k not in [
                    'record_type', 'title', 'description', 'data', 'person_id', 'level', 'source'
                ]}
            )
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO test_records 
                    (record_id, record_type, title, description, data, person_id,
                     level, source, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id, record.record_type, record.title, record.description,
                    json.dumps(record.data), record.person_id, record.level,
                    record.source, record.created_at, json.dumps(record.metadata)
                ))
                conn.commit()
            
            self.logger.debug(f"Created test record: {record.title}")
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {str(e)}")
            raise TestDataGenerationException("record", str(e))
    
    def get_persons(self, limit: int = 100, role: str = None, active_only: bool = True) -> List[TestPerson]:
        """
        사람 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            role: 역할 필터
            active_only: 활성 사용자만 조회 여부
            
        Returns:
            TestPerson 객체 리스트
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM test_persons"
                params = []
                conditions = []
                
                if active_only:
                    conditions.append("is_active = ?")
                    params.append(True)
                
                if role:
                    conditions.append("role = ?")
                    params.append(role)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                persons = []
                for row in rows:
                    persons.append(TestPerson(
                        person_id=row['person_id'],
                        name=row['name'],
                        email=row['email'],
                        phone=row['phone'],
                        address=row['address'],
                        role=row['role'],
                        department=row['department'],
                        position=row['position'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        is_active=bool(row['is_active']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return persons
                
        except Exception as e:
            self.logger.error(f"Failed to get persons: {str(e)}")
            return []
    
    def get_contents(self, limit: int = 100, content_type: str = None, status: str = None) -> List[TestContent]:
        """
        콘텐츠 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            content_type: 콘텐츠 타입 필터
            status: 상태 필터
            
        Returns:
            TestContent 객체 리스트
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM test_contents"
                params = []
                conditions = []
                
                if content_type:
                    conditions.append("content_type = ?")
                    params.append(content_type)
                
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                contents = []
                for row in rows:
                    contents.append(TestContent(
                        content_id=row['content_id'],
                        title=row['title'],
                        body=row['body'],
                        content_type=row['content_type'],
                        author_id=row['author_id'],
                        category=row['category'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        status=row['status'],
                        view_count=row['view_count'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return contents
                
        except Exception as e:
            self.logger.error(f"Failed to get contents: {str(e)}")
            return []
    
    def get_records(self, limit: int = 100, record_type: str = None, level: str = None) -> List[TestRecord]:
        """
        레코드 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            record_type: 레코드 타입 필터
            level: 레벨 필터
            
        Returns:
            TestRecord 객체 리스트
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM test_records"
                params = []
                conditions = []
                
                if record_type:
                    conditions.append("record_type = ?")
                    params.append(record_type)
                
                if level:
                    conditions.append("level = ?")
                    params.append(level)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                records = []
                for row in rows:
                    records.append(TestRecord(
                        record_id=row['record_id'],
                        record_type=row['record_type'],
                        title=row['title'],
                        description=row['description'],
                        data=json.loads(row['data']) if row['data'] else {},
                        person_id=row['person_id'],
                        level=row['level'],
                        source=row['source'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get records: {str(e)}")
            return []

    # ==================== 데이터 정리 ====================
    
    def cleanup_old_data(self, days: int = None) -> Dict[str, int]:
        """
        오래된 데이터 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            정리된 데이터 개수 딕셔너리
        """
        days = days or self.config.data_retention_days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with self._get_connection() as conn:
                # 오래된 주문 삭제
                orders_result = conn.execute(
                    "DELETE FROM test_orders WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                # 오래된 상품 삭제
                products_result = conn.execute(
                    "DELETE FROM test_products WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                # 오래된 사용자 삭제
                users_result = conn.execute(
                    "DELETE FROM test_users WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                # 오래된 범용 데이터 삭제
                persons_result = conn.execute(
                    "DELETE FROM test_persons WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                contents_result = conn.execute(
                    "DELETE FROM test_contents WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                records_result = conn.execute(
                    "DELETE FROM test_records WHERE created_at < ?", 
                    (cutoff_date,)
                )
                
                conn.commit()
                
                cleanup_stats = {
                    'users': users_result.rowcount,
                    'products': products_result.rowcount,
                    'orders': orders_result.rowcount,
                    'persons': persons_result.rowcount,
                    'contents': contents_result.rowcount,
                    'records': records_result.rowcount
                }
                
                self.logger.info(f"Cleaned up old data: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {str(e)}")
            raise TestDataCleanupException("old_data", str(e))
    
    def clear_all_data(self) -> bool:
        """
        모든 테스트 데이터 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM test_orders")
                conn.execute("DELETE FROM test_products")
                conn.execute("DELETE FROM test_users")
                conn.execute("DELETE FROM test_records")
                conn.execute("DELETE FROM test_contents")
                conn.execute("DELETE FROM test_persons")
                conn.commit()
            
            self.logger.info("Cleared all test data")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear all data: {str(e)}")
            return False
    
    def get_data_stats(self) -> Dict[str, int]:
        """
        데이터 통계 조회
        
        Returns:
            데이터 통계 딕셔너리
        """
        try:
            with self._get_connection() as conn:
                users_count = conn.execute("SELECT COUNT(*) FROM test_users").fetchone()[0]
                products_count = conn.execute("SELECT COUNT(*) FROM test_products").fetchone()[0]
                orders_count = conn.execute("SELECT COUNT(*) FROM test_orders").fetchone()[0]
                persons_count = conn.execute("SELECT COUNT(*) FROM test_persons").fetchone()[0]
                contents_count = conn.execute("SELECT COUNT(*) FROM test_contents").fetchone()[0]
                records_count = conn.execute("SELECT COUNT(*) FROM test_records").fetchone()[0]
                
                return {
                    'users': users_count,
                    'products': products_count,
                    'orders': orders_count,
                    'persons': persons_count,
                    'contents': contents_count,
                    'records': records_count,
                    'total': users_count + products_count + orders_count + persons_count + contents_count + records_count
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get data stats: {str(e)}")
            return {'users': 0, 'products': 0, 'orders': 0, 'persons': 0, 'contents': 0, 'records': 0, 'total': 0}
    
    # ==================== 자동 정리 스레드 ====================
    
    def _start_cleanup_thread(self) -> None:
        """자동 정리 스레드 시작"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="DataManager-Cleanup"
        )
        self._cleanup_thread.start()
        self.logger.debug("Started cleanup thread")
    
    def _cleanup_worker(self) -> None:
        """자동 정리 워커"""
        while not self._stop_cleanup.is_set():
            try:
                # 정리 간격만큼 대기
                if self._stop_cleanup.wait(self.config.cleanup_interval):
                    break
                
                # 오래된 데이터 정리
                self.cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {str(e)}")
    
    def stop_cleanup(self) -> None:
        """자동 정리 중지"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
            self.logger.debug("Stopped cleanup thread")
    
    def __del__(self):
        """소멸자"""
        try:
            self.stop_cleanup()
        except:
            pass


# ==================== 편의 함수들 ====================

def create_test_data_manager(config: DataManagerConfig = None) -> DataManager:
    """
    테스트 데이터 매니저 생성
    
    Args:
        config: DataManager 설정
        
    Returns:
        DataManager 인스턴스
    """
    return DataManager(config)


def create_sample_data(manager: DataManager, users: int = 10, products: int = 20) -> Dict[str, List]:
    """
    기존 샘플 데이터 생성 (쇼핑몰용)
    """
    return _create_ecommerce_sample_data(manager, users, products)


def _create_ecommerce_sample_data(manager: DataManager, users: int = 10, products: int = 20) -> Dict[str, List]:
    """
    샘플 데이터 생성
    
    Args:
        manager: DataManager 인스턴스
        users: 생성할 사용자 수
        products: 생성할 상품 수
        
    Returns:
        생성된 데이터 딕셔너리
    """
    try:
        # 사용자 생성
        test_users = manager.create_bulk_users(users)
        
        # 상품 생성
        test_products = manager.create_bulk_products(products)
        
        # 일부 주문 생성
        orders = []
        for i in range(min(5, users)):
            user = test_users[i]
            selected_products = manager.faker.random.choices(test_products, k=2)
            
            order_products = []
            for product in selected_products:
                order_products.append({
                    'product_id': product.product_id,
                    'quantity': manager.faker.random_int(1, 3),
                    'price': product.price
                })
            
            order = manager.create_order(user.user_id, order_products)
            orders.append(order)
        
        return {
            'users': test_users,
            'products': test_products,
            'orders': orders
        }
        
    except Exception as e:
        raise TestDataGenerationException("sample_data", str(e))


def create_general_sample_data(manager: DataManager, persons: int = 10, contents: int = 20, records: int = 30) -> Dict[str, List]:
    """
    범용 샘플 데이터 생성
    
    Args:
        manager: DataManager 인스턴스
        persons: 생성할 사람 수
        contents: 생성할 콘텐츠 수
        records: 생성할 레코드 수
        
    Returns:
        생성된 범용 데이터 딕셔너리
    """
    try:
        # 사람 생성 (다양한 역할)
        roles = ['user', 'admin', 'employee', 'student', 'teacher', 'manager']
        test_persons = []
        
        for i in range(persons):
            person = manager.create_person(
                role=manager.faker.random.choice(roles),
                department=manager.faker.word(),
                position=manager.faker.job()
            )
            test_persons.append(person)
        
        # 콘텐츠 생성 (다양한 타입)
        content_types = ['article', 'post', 'notice', 'course', 'document', 'news']
        statuses = ['draft', 'published', 'archived']
        test_contents = []
        
        for i in range(contents):
            # 작성자는 생성된 사람 중에서 선택
            author = manager.faker.random.choice(test_persons) if test_persons else None
            
            content = manager.create_content(
                content_type=manager.faker.random.choice(content_types),
                author_id=author.person_id if author else '',
                status=manager.faker.random.choice(statuses),
                tags=[manager.faker.word() for _ in range(manager.faker.random_int(1, 5))]
            )
            test_contents.append(content)
        
        # 레코드 생성 (다양한 타입)
        record_types = ['log', 'transaction', 'activity', 'event', 'audit']
        levels = ['debug', 'info', 'warning', 'error', 'critical']
        test_records = []
        
        for i in range(records):
            # 관련 사람은 생성된 사람 중에서 선택
            person = manager.faker.random.choice(test_persons) if test_persons else None
            
            record = manager.create_record(
                record_type=manager.faker.random.choice(record_types),
                person_id=person.person_id if person else '',
                level=manager.faker.random.choice(levels),
                data={
                    'action': manager.faker.word(),
                    'result': manager.faker.random.choice(['success', 'failure', 'pending']),
                    'duration': manager.faker.random_int(1, 1000),
                    'ip_address': manager.faker.ipv4()
                }
            )
            test_records.append(record)
        
        return {
            'persons': test_persons,
            'contents': test_contents,
            'records': test_records
        }
        
    except Exception as e:
        raise TestDataGenerationException("general_sample_data", str(e))