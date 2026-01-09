"""데이터베이스 연결 및 세션 관리 모듈.

SQLite 데이터베이스 연결과 세션 관리를 담당해요.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 데이터베이스 파일 경로 (프로젝트 루트의 data 폴더)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "ranking_history.db"

# data 폴더가 없으면 생성
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite 연결 URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLite는 check_same_thread=False 필요
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # SQL 로깅 (디버깅 시 True로 설정)
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """데이터베이스 테이블을 초기화해요.

    정의된 모든 모델의 테이블을 생성해요.
    이미 존재하는 테이블은 건너뛰어요.
    """
    from .models import Base

    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DB_PATH}")


def get_db():
    """데이터베이스 세션을 컨텍스트 매니저로 반환해요.

    의존성 주입(FastAPI 등)에서 사용해요.
    사용 후 자동으로 세션을 닫아요.

    Yields:
        Session: SQLAlchemy 세션 객체
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """데이터베이스 세션을 직접 반환해요.

    수동 관리가 필요한 경우에 사용해요.
    호출자가 세션을 직접 닫아야 해요.

    Returns:
        Session: SQLAlchemy 세션 객체
    """
    return SessionLocal()
