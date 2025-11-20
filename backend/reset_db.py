import os
import sys

# Add the current directory to sys.path to make sure we can import app
sys.path.append(os.getcwd())

from app.db_orm import Base, engine

def reset_database():
    print("Resetting database as requested...")
    
    try:
        Base.metadata.drop_all(bind=engine)
        print("Tabelle eliminate.")
        
        Base.metadata.create_all(bind=engine)
        print("Tabelle ricreate. Il database è vuoto e pronto.")
        
    except Exception as e:
        print(f"Errore durante il reset: {e}")

if __name__ == "__main__":
    reset_database()
