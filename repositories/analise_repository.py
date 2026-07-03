from sqlalchemy.orm import Session
from models.analise import AnaliseModel
from typing import List, Optional
import datetime

class AnaliseRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, analise: AnaliseModel) -> AnaliseModel:
        self.db.add(analise)
        self.db.commit()
        self.db.refresh(analise)
        return analise

    def get_all(self, search: Optional[str] = None, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> List[AnaliseModel]:
        query = self.db.query(AnaliseModel)
        if search:
            query = query.filter(
                (AnaliseModel.descricao.ilike(f"%{search}%")) | 
                (AnaliseModel.objetos.ilike(f"%{search}%")) |
                (AnaliseModel.transcricao.ilike(f"%{search}%"))
            )
        if start_date:
            query = query.filter(AnaliseModel.created_at >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            query = query.filter(AnaliseModel.created_at <= datetime.datetime.combine(end_date, datetime.time.max))
        return query.order_by(AnaliseModel.created_at.desc()).all()

    def delete(self, analise_id: int) -> bool:
        analise = self.db.query(AnaliseModel).filter(AnaliseModel.id == analise_id).first()
        if analise:
            self.db.delete(analise)
            self.db.commit()
            return True
        return False

    def update_transcricao(self, analise_id: int, transcricao: str) -> Optional[AnaliseModel]:
        analise = self.db.query(AnaliseModel).filter(AnaliseModel.id == analise_id).first()
        if analise:
            analise.transcricao = transcricao
            self.db.commit()
            self.db.refresh(analise)
            return analise
        return None
