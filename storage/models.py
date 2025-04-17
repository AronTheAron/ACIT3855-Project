from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, Float, func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Model for player events
class PlayerEvent(Base):
    __tablename__ = "player_events"
    id = mapped_column(Integer, primary_key=True)
    player_id = mapped_column(String(50), nullable=False)
    server_id = mapped_column(String(50), nullable=False)
    action = mapped_column(String(50), nullable=False)
    score = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    trace_id = mapped_column(String(255), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

# Model for server events
class ServerEvent(Base):
    __tablename__ = "server_events"
    id = mapped_column(Integer, primary_key=True)
    server_id = mapped_column(String(50), nullable=False)
    uptime = mapped_column(Integer, nullable=False)
    cpu_usage = mapped_column(Float, nullable=False)
    memory_usage = mapped_column(Float, nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    trace_id = mapped_column(String(255), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

SQLALCHEMY_DATABASE_URI = 'mysql://aron:password@db/database3855?charset=utf8mb4'

# Database connection setup
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Session maker
def make_session():
    return sessionmaker(bind=engine)()
