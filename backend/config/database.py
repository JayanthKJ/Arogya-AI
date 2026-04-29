from sqlmodel import SQLModel, create_engine, Session
from config.settings import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Supabase requires SSL
connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)