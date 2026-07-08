from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """DBセッションを取得するジェネレータ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """テーブルを初期化する"""
    from models.clothing import Clothing  # 循環import回避
    from models.ootd_log import OotdLog  # 追加
    Base.metadata.create_all(engine)
    print("[DB] テーブルの初期化が完了しました")