from app.config.db_base import Base
from app.config.database import get_engine
import app.entities.user  # Import active models so Base.metadata is aware of them
import app.entities.account
import app.entities.category
import app.entities.concept
import app.entities.tag
import app.entities.transaction
import app.entities.transaction_tag


def create_all_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    create_all_tables()
