"""
DataManager 데모 스크립트

DataManager 클래스의 기능을 실제로 테스트해보는 데모입니다.
"""

import os
from src.core.data_manager import DataManager, DataManagerConfig, create_sample_data

def main():
    print("🎯 DataManager 데모 시작!")
    print("=" * 50)
    
    # 임시 데이터베이스 설정
    config = DataManagerConfig(
        database_path="demo_test_data.db",
        auto_cleanup=False,  # 데모에서는 자동 정리 비활성화
        seed=12345,  # 일관된 데이터를 위한 시드
        locale="ko_KR"
    )
    
    # DataManager 생성
    data_manager = DataManager(config)
    
    try:
        print("\n📊 초기 데이터 통계:")
        stats = data_manager.get_data_stats()
        print(f"  - 사용자: {stats['users']}개")
        print(f"  - 상품: {stats['products']}개")
        print(f"  - 주문: {stats['orders']}개")
        print(f"  - 총계: {stats['total']}개")
        
        print("\n👤 테스트 사용자 생성:")
        user1 = data_manager.create_user(
            username="testuser1",
            email="test1@example.com",
            first_name="홍",
            last_name="길동"
        )
        print(f"  ✅ 사용자 생성: {user1.username} ({user1.email})")
        
        # Faker로 자동 생성
        user2 = data_manager.create_user()
        print(f"  ✅ 자동 생성 사용자: {user2.username} ({user2.email})")
        
        print("\n🛍️ 테스트 상품 생성:")
        product1 = data_manager.create_product(
            name="테스트 상품 1",
            price=29.99,
            category="Electronics",
            stock=100
        )
        print(f"  ✅ 상품 생성: {product1.name} (₩{product1.price})")
        
        # Faker로 자동 생성
        product2 = data_manager.create_product()
        print(f"  ✅ 자동 생성 상품: {product2.name} (₩{product2.price})")
        
        print("\n📦 테스트 주문 생성:")
        order_products = [
            {"product_id": product1.product_id, "quantity": 2, "price": product1.price},
            {"product_id": product2.product_id, "quantity": 1, "price": product2.price}
        ]
        
        order = data_manager.create_order(user1.user_id, order_products)
        print(f"  ✅ 주문 생성: {order.order_id} (총액: ₩{order.total_amount})")
        
        print("\n🔍 데이터 조회 테스트:")
        # 사용자 조회
        retrieved_user = data_manager.get_user(username="testuser1")
        if retrieved_user:
            print(f"  ✅ 사용자 조회: {retrieved_user.first_name} {retrieved_user.last_name}")
        
        # 상품 조회
        retrieved_product = data_manager.get_product(product_id=product1.product_id)
        if retrieved_product:
            print(f"  ✅ 상품 조회: {retrieved_product.name}")
        
        print("\n📈 대량 데이터 생성:")
        bulk_users = data_manager.create_bulk_users(5)
        print(f"  ✅ 대량 사용자 생성: {len(bulk_users)}명")
        
        bulk_products = data_manager.create_bulk_products(3)
        print(f"  ✅ 대량 상품 생성: {len(bulk_products)}개")
        
        print("\n📊 최종 데이터 통계:")
        final_stats = data_manager.get_data_stats()
        print(f"  - 사용자: {final_stats['users']}개")
        print(f"  - 상품: {final_stats['products']}개")
        print(f"  - 주문: {final_stats['orders']}개")
        print(f"  - 총계: {final_stats['total']}개")
        
        print("\n🎲 샘플 데이터 생성 테스트:")
        sample_data = create_sample_data(data_manager, users=3, products=5)
        print(f"  ✅ 샘플 사용자: {len(sample_data['users'])}명")
        print(f"  ✅ 샘플 상품: {len(sample_data['products'])}개")
        print(f"  ✅ 샘플 주문: {len(sample_data['orders'])}개")
        
        print("\n📋 사용자 목록:")
        all_users = data_manager.get_users(limit=5)
        for i, user in enumerate(all_users[:3], 1):
            print(f"  {i}. {user.first_name} {user.last_name} ({user.email})")
        
        print("\n🛒 상품 목록:")
        all_products = data_manager.get_products(limit=5)
        for i, product in enumerate(all_products[:3], 1):
            print(f"  {i}. {product.name} - ₩{product.price} ({product.category})")
        
        print("\n🧹 데이터 정리 테스트:")
        # 모든 데이터 삭제
        success = data_manager.clear_all_data()
        if success:
            print("  ✅ 모든 데이터 삭제 완료")
            
            # 정리 후 통계
            clean_stats = data_manager.get_data_stats()
            print(f"  📊 정리 후 통계: 총 {clean_stats['total']}개")
        
        print("\n🎉 DataManager 데모 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        
    finally:
        # 정리
        data_manager.stop_cleanup()
        
        # 데모 데이터베이스 파일 삭제
        if os.path.exists("demo_test_data.db"):
            try:
                os.remove("demo_test_data.db")
                print("🗑️ 데모 데이터베이스 파일 삭제 완료")
            except:
                print("⚠️ 데모 데이터베이스 파일 삭제 실패 (수동으로 삭제하세요)")


if __name__ == "__main__":
    main()