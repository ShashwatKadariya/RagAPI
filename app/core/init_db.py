from sqlalchemy import create_engine
from app.core.config import Settings
from app.models.document import Base as DocumentBase
from app.models.booking import Base as BookingBase
from app.core.database import init_qdrant

def init_db():
    settings = Settings()
    
    # Initialize tables
    engine = create_engine(settings.postgres_url)
    DocumentBase.metadata.create_all(bind=engine)
    BookingBase.metadata.create_all(bind=engine)
    
    # Initialize collection
    init_qdrant()

if __name__ == "__main__":
    init_db()
    print("Database tables and Qdrant collection created successfully.")
