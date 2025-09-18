#!/usr/bin/env python3
"""
데이터베이스 연결 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 다양한 연결 설정 시도
connection_configs = [
    {
        "url": "postgresql://postgres:@localhost:5433/postgres",
        "description": "기본 postgres 사용자, 비밀번호 없음"
    },
    {
        "url": "postgresql://postgres:password@localhost:5433/postgres", 
        "description": "postgres 사용자, 'password' 비밀번호"
    },
    {
        "url": "postgresql://postgres:postgres@localhost:5433/postgres",
        "description": "postgres 사용자, 'postgres' 비밀번호" 
    },
    {
        "url": "postgresql://postgres:admin@localhost:5433/postgres",
        "description": "postgres 사용자, 'admin' 비밀번호"
    },
    {
        "url": "postgresql://admin:admin123@localhost:5433/ISPLDB",
        "description": "admin 사용자, Docker Compose와 동일한 설정"
    }
]

def test_connection(url, description):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 연결 성공: {description}")
            print(f"   PostgreSQL 버전: {version}")
            
            # 데이터베이스 목록 조회
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
            databases = [row[0] for row in result.fetchall()]
            print(f"   사용 가능한 데이터베이스: {', '.join(databases)}")
            return True
            
    except OperationalError as e:
        print(f"❌ 연결 실패: {description}")
        print(f"   오류: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {description}")
        print(f"   오류: {str(e)}")
        return False

def main():
    print("PostgreSQL 연결 테스트를 시작합니다...\n")
    
    successful_configs = []
    
    for config in connection_configs:
        if test_connection(config["url"], config["description"]):
            successful_configs.append(config)
        print()
    
    if successful_configs:
        print("성공한 연결 설정:")
        for config in successful_configs:
            print(f"  - {config['description']}")
            print(f"    URL: {config['url']}")
        
        # 첫 번째 성공한 설정을 권장
        recommended = successful_configs[0]
        print(f"\n권장 설정: {recommended['url']}")
        
        # database.py 업데이트를 위한 제안
        print(f"\ndatabase.py 파일의 DATABASE_URL을 다음과 같이 수정하세요:")
        print(f'DATABASE_URL = os.getenv("DATABASE_URL", "{recommended["url"]}")')
        
    else:
        print("❌ 모든 연결 시도가 실패했습니다.")
        print("\n해결 방법:")
        print("1. PostgreSQL 서비스가 실행 중인지 확인")
        print("2. 포트 5433이 올바른지 확인")
        print("3. 사용자명과 비밀번호 확인")
        print("4. pg_hba.conf 파일의 인증 설정 확인")

if __name__ == "__main__":
    main()
