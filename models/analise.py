from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from database.connection import Base
import datetime

class AnaliseModel(Base):
    __tablename__ = "analises"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    image_path = Column(String(500), nullable=False)
    descricao = Column(Text, nullable=True)
    objetos = Column(Text, nullable=True)
    quantidade_pessoas = Column(Integer, default=0)
    rostos = Column(Integer, default=0)
    idade = Column(String(100), nullable=True)
    emocao = Column(String(100), nullable=True)
    cores = Column(String(255), nullable=True)
    luminosidade = Column(String(100), nullable=True)
    nitidez = Column(String(100), nullable=True)
    transcricao = Column(Text, nullable=True)
    json_resultado = Column(JSON, nullable=True)
