from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import shutil
from datetime import datetime
import glob

SQLALCHEMY_DATABASE_URL = "sqlite:///./database/residents.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    from sqlalchemy.orm import Session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def backup_database():
    """Create a timestamped backup of the database"""
    try:
        backup_dir = r"C:\Users\cash crusaders\Documents\Khoronemo\residents_db_backups"
        os.makedirs(backup_dir, exist_ok=True)
        source_db = "./database/residents.db"
        if not os.path.exists(source_db):
            print(f"Source database not found: {source_db}")
            return False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"residents_backup_{timestamp}.db")
        shutil.copy2(source_db, backup_file)
        print(f"Database backup created: {backup_file}")
        backup_files = glob.glob(os.path.join(backup_dir, "residents_backup_*.db"))
        backup_files.sort(key=os.path.getmtime)
        if len(backup_files) > 10:
            for old_backup in backup_files[:-10]:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully!")