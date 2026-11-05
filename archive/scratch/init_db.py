from app.db.database import Base, engine
import app.models  # This imports __init__.py which has all models

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
