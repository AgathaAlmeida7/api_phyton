from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db/app_db"

settings = Settings()

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, echo=True)

async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

from app.core.config import settings
from app.models.base import Base

config = context.config

fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Atleta(Base):
    __tablename__ = 'atletas'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    centro_treinamento_id = Column(Integer, ForeignKey('centros_treinamento.id'))

    categoria = relationship("Categoria", back_populates="atletas")
    centro_treinamento = relationship("CentroTreinamento", back_populates="atletas")


from pydantic import BaseModel

class AtletaBase(BaseModel):
    nome: str
    cpf: str

class AtletaCreate(AtletaBase):
    categoria_id: int
    centro_treinamento_id: int

class Atleta(AtletaBase):
    id: int
    categoria_id: int
    centro_treinamento_id: int

    class Config:
        orm_mode = True

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Categoria(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    atletas = relationship("Atleta", back_populates="categoria")
from pydantic import BaseModel

class CategoriaBase(BaseModel):
    nome: str

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id: int

    class Config:
        orm_mode = True
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class CentroTreinamento(Base):
    __tablename__ = 'centros_treinamento'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    atletas = relationship("Atleta", back_populates="centro_treinamento")
from pydantic import BaseModel

class CentroTreinamentoBase(BaseModel):
    nome: str

class CentroTreinamentoCreate(CentroTreinamentoBase):
    pass

class CentroTreinamento(CentroTreinamentoBase):
    id: int

    class Config:
        orm_mode = True
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.atleta import Atleta
from app.schemas.atleta import AtletaCreate, Atleta
from app.core.database import async_session
from fastapi_pagination import Page, paginate

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/atletas/", response_model=Atleta, status_code=status.HTTP_201_CREATED)
async def create_atleta(atleta: AtletaCreate, session: AsyncSession = Depends(get_session)):
    new_atleta = Atleta(**atleta.dict())
    session.add(new_atleta)
    try:
        await session.commit()
        await session.refresh(new_atleta)
        return new_atleta
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=303, detail=f"Já existe um atleta cadastrado com o cpf: {atleta.cpf}")

@router.get("/atletas/", response_model=Page[Atleta])
async def get_atletas(session: AsyncSession = Depends(get_session), nome: str = None, cpf: str = None):
    query = select(Atleta)
    if nome:
        query = query.where(Atleta.nome.contains(nome))
    if cpf:
        query = query.where(Atleta.cpf == cpf)
    result = await session.execute(query)
    return paginate(result.scalars().all())
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, Categoria
from app.core.database import async_session

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/categorias/", response_model=Categoria, status_code=status.HTTP_201_CREATED)
async def create_categoria(categoria: CategoriaCreate, session: AsyncSession = Depends(get_session)):
    new_categoria = Categoria(**categoria.dict())
    session.add(new_categoria)
    await session.commit()
    await session.refresh(new_categoria)
    return new_categoria

@router.get("/categorias/", response_model=list[Categoria])
async def get_categorias(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Categoria))
    return result.scalars().all()
