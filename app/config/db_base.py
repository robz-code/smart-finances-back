from sqlalchemy.orm import declarative_base

# Standalone SQLAlchemy Base without creating an engine.
# Import this in model/entity modules to avoid connecting at import time.
Base = declarative_base()

