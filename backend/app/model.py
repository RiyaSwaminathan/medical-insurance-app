from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector
from .db import Base

class Chunk(Base):

    __tablename__ = "insurance_chunks"
    id = Column(Integer, primary_key=True, index=True)
    chunk = Column(String)
    embedding = Column(Vector(768))
