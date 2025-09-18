from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5433/ISPLDB")

# SQLAlchemy 엔진 생성 (인코딩 설정 포함)
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c client_encoding=utf8"
    },
    echo=False
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_database_url():
    """데이터베이스 URL 반환"""
    return DATABASE_URL

async def create_tables():
    """데이터베이스 테이블 생성"""
    from models import Base
    Base.metadata.create_all(bind=engine)

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return False
