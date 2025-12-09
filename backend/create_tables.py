from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
# Ensure all models are imported so they are registered in Base.metadata
from app.modules.notification.model import Notification
from app.modules.guest.model import Guest, GuestImage
from app.modules.user.model import User

engine = create_engine(settings.DATABASE_URL)

print("Creating missing tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")
