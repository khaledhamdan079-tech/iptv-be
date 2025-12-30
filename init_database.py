"""
Initialize the database - create all tables
"""
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from app.database import init_db, engine
from app.models import Base

if __name__ == "__main__":
    print("Initializing database...")
    print("Creating all tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print("Tables created:")
    print("  - playlists")
    print("  - categories")
    print("  - movies")
    print("  - series")
    print("  - episodes")
    print("  - live_channels")

