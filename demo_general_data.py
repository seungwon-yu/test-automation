"""
범용 DataManager 데모 스크립트

DataManager의 범용 데이터 기능을 테스트해보는 데모입니다.
블로그, 회사 홈페이지, 학습 사이트 등 다양한 웹사이트에서 활용 가능한 데이터를 생성합니다.
"""

import os
from src.core.data_manager import DataManager, DataManagerConfig, create_general_sample_data

def main():
    print("🌐 범용 DataManager 데모 시작!")
    print("=" * 60)
    
    # 임시 데이터베이스 설정
    config = DataManagerConfig(
        database_path="demo_general_data.db",
        auto_cleanup=False,
        seed=12345,
        locale="ko_KR"
    )
    
    # DataManager 생성
    data_manager = DataManager(config)
    
    try:
        print("\n📊 초기 데이터 통계:")
        stats = data_manager.get_data_stats()
        print(f"  - 사람: {stats['persons']}명")
        print(f"  - 콘텐츠: {stats['contents']}개")
        print(f"  - 레코드: {stats['records']}개")
        print(f"  - 총계: {stats['total']}개")
        
        print("\n👥 다양한 역할의 사람 생성:")
        
        # 관리자 생성
        admin = data_manager.create_person(
            name="김관리",
            email="admin@company.com",
            role="admin",
            department="IT",
            position="시스템 관리자"
        )
        print(f"  ✅ 관리자: {admin.name} ({admin.role}) - {admin.position}")
        
        # 직원 생성
        employee = data_manager.create_person(
            role="employee",
            department="마케팅",
            position="마케팅 매니저"
        )
        print(f"  ✅ 직원: {employee.name} ({employee.role}) - {employee.position}")
        
        # 학생 생성
        student = data_manager.create_person(
            role="student",
            department="컴퓨터공학과"
        )
        print(f"  ✅ 학생: {student.name} ({student.role}) - {student.department}")
        
        print("\n📝 다양한 콘텐츠 생성:")
        
        # 블로그 포스트
        blog_post = data_manager.create_content(
            title="Python 웹 자동화 테스트 가이드",
            content_type="post",
            author_id=admin.person_id,
            category="기술",
            status="published",
            tags=["Python", "테스트", "자동화", "Selenium"]
        )
        print(f"  ✅ 블로그 포스트: {blog_post.title}")
        print(f"      카테고리: {blog_post.category}, 태그: {', '.join(blog_post.tags)}")
        
        # 공지사항
        notice = data_manager.create_content(
            title="시스템 점검 안내",
            content_type="notice",
            author_id=admin.person_id,
            category="공지",
            status="published"
        )
        print(f"  ✅ 공지사항: {notice.title}")
        
        # 강의 콘텐츠
        course = data_manager.create_content(
            title="웹 개발 기초",
            content_type="course",
            author_id=employee.person_id,
            category="교육",
            status="draft"
        )
        print(f"  ✅ 강의: {course.title} (상태: {course.status})")
        
        print("\n📋 다양한 레코드/로그 생성:")
        
        # 로그인 로그
        login_log = data_manager.create_record(
            record_type="activity",
            title="사용자 로그인",
            description=f"{admin.name}님이 시스템에 로그인했습니다.",
            person_id=admin.person_id,
            level="info",
            source="auth_system",
            data={
                "action": "login",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 Chrome/91.0",
                "result": "success"
            }
        )
        print(f"  ✅ 활동 로그: {login_log.title} (레벨: {login_log.level})")
        
        # 에러 로그
        error_log = data_manager.create_record(
            record_type="log",
            title="데이터베이스 연결 오류",
            description="데이터베이스 서버에 연결할 수 없습니다.",
            level="error",
            source="database",
            data={
                "error_code": "DB_CONNECTION_FAILED",
                "retry_count": 3,
                "last_attempt": "2025-01-18 14:30:00"
            }
        )
        print(f"  ✅ 에러 로그: {error_log.title} (레벨: {error_log.level})")
        
        # 거래 기록
        transaction = data_manager.create_record(
            record_type="transaction",
            title="포인트 적립",
            description=f"{student.name}님이 강의 수강으로 포인트를 적립했습니다.",
            person_id=student.person_id,
            level="info",
            source="point_system",
            data={
                "action": "earn_points",
                "points": 100,
                "reason": "course_completion",
                "balance": 1500
            }
        )
        print(f"  ✅ 거래 기록: {transaction.title}")
        
        print("\n🎲 범용 샘플 데이터 대량 생성:")
        sample_data = create_general_sample_data(data_manager, persons=5, contents=8, records=10)
        print(f"  ✅ 샘플 사람: {len(sample_data['persons'])}명")
        print(f"  ✅ 샘플 콘텐츠: {len(sample_data['contents'])}개")
        print(f"  ✅ 샘플 레코드: {len(sample_data['records'])}개")
        
        print("\n📊 최종 데이터 통계:")
        final_stats = data_manager.get_data_stats()
        print(f"  - 사람: {final_stats['persons']}명")
        print(f"  - 콘텐츠: {final_stats['contents']}개")
        print(f"  - 레코드: {final_stats['records']}개")
        print(f"  - 총계: {final_stats['total']}개")
        
        print("\n👥 역할별 사람 목록:")
        # 관리자 목록
        admins = data_manager.get_persons(limit=10, role="admin")
        print(f"  📋 관리자 ({len(admins)}명):")
        for admin in admins[:3]:
            print(f"    - {admin.name} ({admin.email}) - {admin.position}")
        
        # 직원 목록
        employees = data_manager.get_persons(limit=10, role="employee")
        print(f"  📋 직원 ({len(employees)}명):")
        for emp in employees[:3]:
            print(f"    - {emp.name} ({emp.department}) - {emp.position}")
        
        print("\n📝 콘텐츠 타입별 목록:")
        # 게시글
        posts = data_manager.get_contents(limit=5, content_type="post")
        print(f"  📄 게시글 ({len(posts)}개):")
        for post in posts[:2]:
            print(f"    - {post.title} (조회수: {post.view_count})")
        
        # 공지사항
        notices = data_manager.get_contents(limit=5, content_type="notice")
        print(f"  📢 공지사항 ({len(notices)}개):")
        for notice in notices[:2]:
            print(f"    - {notice.title} (상태: {notice.status})")
        
        print("\n📋 레벨별 레코드 목록:")
        # 에러 레코드
        errors = data_manager.get_records(limit=5, level="error")
        print(f"  ❌ 에러 ({len(errors)}개):")
        for error in errors[:2]:
            print(f"    - {error.title} ({error.source})")
        
        # 정보 레코드
        infos = data_manager.get_records(limit=5, level="info")
        print(f"  ℹ️ 정보 ({len(infos)}개):")
        for info in infos[:2]:
            print(f"    - {info.title} ({info.record_type})")
        
        print("\n🌟 활용 시나리오 예시:")
        print("  📚 블로그/커뮤니티: 사용자, 게시글, 댓글 데이터")
        print("  🏢 회사 홈페이지: 직원, 공지사항, 활동 로그")
        print("  🎓 학습 사이트: 학생, 강의, 수강 기록")
        print("  📊 관리자 페이지: 사용자, 콘텐츠, 시스템 로그")
        print("  🔍 모니터링 시스템: 이벤트, 에러 로그, 성능 기록")
        
        print("\n🧹 데이터 정리 테스트:")
        success = data_manager.clear_all_data()
        if success:
            print("  ✅ 모든 데이터 삭제 완료")
            clean_stats = data_manager.get_data_stats()
            print(f"  📊 정리 후 통계: 총 {clean_stats['total']}개")
        
        print("\n🎉 범용 DataManager 데모 완료!")
        print("💡 이제 어떤 종류의 웹사이트든 테스트 데이터를 생성할 수 있습니다!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        
    finally:
        # 정리
        data_manager.stop_cleanup()
        
        # 데모 데이터베이스 파일 삭제
        if os.path.exists("demo_general_data.db"):
            try:
                os.remove("demo_general_data.db")
                print("🗑️ 데모 데이터베이스 파일 삭제 완료")
            except:
                print("⚠️ 데모 데이터베이스 파일 삭제 실패 (수동으로 삭제하세요)")


if __name__ == "__main__":
    main()