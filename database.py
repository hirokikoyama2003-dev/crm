import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Vercel 環境（VERCEL=1）では /tmp に DB を置く（書き込み可能だが再起動でリセット）
_is_vercel = os.environ.get("VERCEL") == "1"
DATABASE_URL = "sqlite:////tmp/crm.db" if _is_vercel else "sqlite:///./crm.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SQLite の外部キー制約を有効化
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
