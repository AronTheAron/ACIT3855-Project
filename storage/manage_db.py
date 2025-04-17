from sqlalchemy import create_engine
from models import Base

SQLALCHEMY_DATABASE_URI = 'mysql://aron:password@db/database3855?charset=utf8mb4'

# Create the SQLite engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Create all tables in the database
def create_db():
    Base.metadata.create_all(engine)

# Drop all tables in the database
def drop_db():
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    drop_db()
    create_db()
    