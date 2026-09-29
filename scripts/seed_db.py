import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import SessionLocal, engine, Base
from app.routers.seed import seed_database

def main():
    print("Initializing Database Tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding Incidents, Feedbacks, and Memory Bank...")
        res = seed_database(db)
        print("Seeding Complete!")
        print(f"Details: {res.data}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
