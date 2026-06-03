from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models.base import Base
from models.category import Category
from models.admin_user import AdminUser
from utils.security import hash_password


def init_db():
    Base.metadata.create_all(bind=engine)

    # Migration: add permissions column if not exists (SQLite)
    import sqlite3
    db_path = engine.url.database
    if db_path and "sqlite" in str(engine.url):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("ALTER TABLE users ADD COLUMN permissions VARCHAR(512) DEFAULT 'dish:query'")
            conn.commit()
            conn.close()
        except Exception:
            pass  # column already exists
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE users SET permissions = 'dish:query' WHERE permissions IS NULL OR permissions = ''")
            conn.commit()
            conn.close()
        except Exception:
            pass
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("ALTER TABLE dishes ADD COLUMN price FLOAT DEFAULT 0.0")
            conn.commit()
            conn.close()
        except Exception:
            pass  # column already exists

    db: Session = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            categories = [
                Category(name="素菜"),
                Category(name="荤菜"),
                Category(name="汤类"),
                Category(name="主食"),
                Category(name="其他"),
            ]
            db.add_all(categories)
            db.commit()
            print("种子分类数据已创建")

        if db.query(AdminUser).count() == 0:
            admin = AdminUser(
                username="admin",
                password_hash=hash_password("admin123"),
                display_name="管理员",
                role="super_admin",
            )
            db.add(admin)
            db.commit()
            print("默认管理员已创建 (admin / admin123)")

        # Always seed chef account if missing
        if not db.query(AdminUser).filter(AdminUser.username == "chef").first():
            chef = AdminUser(
                username="chef",
                password_hash=hash_password("chef123"),
                display_name="厨师",
                role="chef",
            )
            db.add(chef)
            db.commit()
            print("默认厨师账号已创建 (chef / chef123)")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
