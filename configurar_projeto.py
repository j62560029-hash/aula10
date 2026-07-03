import os

# Define a estrutura de pastas e arquivos
estrutura = {
    "config/settings.py": """import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///local.db")
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "assets/images")
    AUDIO_FOLDER: str = os.getenv("AUDIO_FOLDER", "assets/audio")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

os.makedirs(Settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Settings.AUDIO_FOLDER, exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(Settings.LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("CV_App")
""",

    "database/connection.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import Settings, logger

engine = create_engine(Settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Banco de dados inicializado com sucesso via SQLAlchemy.")
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")
        raise e
""",

    "models/analise.py": """from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
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
""",

    "repositories/analise_repository.py": """from sqlalchemy.orm import Session
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
""",

    "services/cv_service.py": """import cv2
import numpy as np
import datetime
from config.settings import logger

class CVService:
    @staticmethod
    def analisar_imagem(image_bytes: bytes) -> dict:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Incapaz de decodificar o arquivo de imagem.")

            height, width, _ = img.shape
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            num_faces = len(faces)

            luminosidade_media = np.mean(gray)
            luminosidade_label = "Boa" if 100 <= luminosidade_media <= 200 else ("Baixa" if luminosidade_media < 100 else "Alta")

            nitidez_valor = cv2.Laplacian(gray, cv2.CV_64F).var()
            nitidez_label = "Focada" if nitidez_valor > 100 else "Desfocada"

            avg_b, avg_g, avg_r = np.mean(img[:, :, 0]), np.mean(img[:, :, 1]), np.mean(img[:, :, 2])
            cor_predominante = f"R:{int(avg_r)} G:{int(avg_g)} B:{int(avg_b)}"

            agora = datetime.datetime.now()

            return {
                "descricao": f"Imagem processada com resolução {width}x{height}.",
                "objetos": "Detectados por proximidade estrutural e contrastes",
                "quantidade_pessoas": num_faces, 
                "rostos": num_faces,
                "idade": "Disponível sob integração de API de VLM",
                "emocao": "Disponível sob integração de API de VLM",
                "cores": cor_predominante,
                "luminosidade": luminosidade_label,
                "nitidez": nitidez_label,
                "resolucao": f"{width}x{height}",
                "data": agora.strftime("%Y-%m-%d"),
                "horario": agora.strftime("%H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Erro no pipeline de Visão Computacional: {str(e)}")
            raise e
""",

    "services/stt_service.py": """import os
from config.settings import logger

class STTService:
    def __init__(self):
        self.model = None

    def _lazy_init(self):
        if self.model is None:
            from faster_whisper import WhisperModel
            logger.info("Carregando modelo Faster-Whisper...")
            self.model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def transcrever_audio(self, audio_path: str) -> str:
        try:
            if not os.path.exists(audio_path):
                return "Arquivo de áudio não encontrado."
            self._lazy_init()
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            transcricao = "".join([segment.text for segment in segments])
            return transcricao.strip()
        except Exception as e:
            logger.error(f"Erro na transcrição de áudio: {str(e)}")
            return f"Erro ao transcrever áudio: {str(e)}"
""",

    "controllers/app_controller.py": """import uuid
import os
from typing import Optional
from repositories.analise_repository import AnaliseRepository
from services.cv_service import CVService
from services.stt_service import STTService
from models.analise import AnaliseModel
from config.settings import Settings

class AppController:
    def __init__(self, db):
        self.repo = AnaliseRepository(db)
        self.stt_service = STTService()

    def processar_fluxo_completo(self, image_bytes: bytes, audio_bytes: Optional[bytes] = None) -> AnaliseModel:
        analise_resultado = CVService.analisar_imagem(image_bytes)
        
        filename = f"img_{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(Settings.UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        transcricao_texto = ""
        if audio_bytes:
            audio_filename = f"aud_{uuid.uuid4().hex}.wav"
            audio_path = os.path.join(Settings.AUDIO_FOLDER, audio_filename)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            transcricao_texto = self.stt_service.transcrever_audio(audio_path)

        analise_model = AnaliseModel(
            image_path=filepath,
            descricao=analise_resultado["descricao"],
            objetos=analise_resultado["objetos"],
            quantidade_pessoas=analise_resultado["quantidade_pessoas"],
            rostos=analise_resultado["rostos"],
            idade=analise_resultado["idade"],
            emocao=analise_resultado["emocao"],
            cores=analise_resultado["cores"],
            luminosidade=analise_resultado["luminosidade"],
            nitidez=analise_resultado["nitidez"],
            transcricao=transcricao_texto,
            json_resultado=analise_resultado
        )
        return self.repo.save(analise_model)

    def associar_audio_a_analise(self, analise_id: int, audio_bytes: bytes) -> Optional[AnaliseModel]:
        audio_filename = f"aud_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(Settings.AUDIO_FOLDER, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        transcricao_texto = self.stt_service.transcrever_audio(audio_path)
        return self.repo.update_transcricao(analise_id, transcricao_texto)

    def remover_audio_da_analise(self, analise_id: int) -> Optional[AnaliseModel]:
        return self.repo.update_transcricao(analise_id, "")

    def listar_historico(self, search: str = None, start_date=None, end_date=None):
        return self.repo.get_all(search, start_date, end_date)

    def deletar_registro(self, analise_id: int) -> bool:
        return self.repo.delete(analise_id)
""",

    "app.py": """import streamlit as str_ui
import pandas as pd
import plotly.express as px
import os
import datetime
from database.connection import SessionLocal, init_db
from controllers.app_controller import AppController

init_db()
str_ui.set_page_config(page_title="Vision & Speech AI", layout="wide")

if "db" not in str_ui.session_state:
    str_ui.session_state.db = SessionLocal()

controller = AppController(str_ui.session_state.db)

str_ui.title("🎛️ Plataforma Avançada de Visão Computacional & Speech-to-Text")
str_ui.markdown("---")

str_ui.sidebar.header("🔌 Status de Conexão")
if str_ui.session_state.db.bind.url.host:
    str_ui.sidebar.success(f"Conectado ao Banco: \\n`{str_ui.session_state.db.bind.url.host}`")
else:
    str_ui.sidebar.warning("Rodando em Banco Local (Fallback SQLite).")

menu = str_ui.sidebar.radio("Navegação do Sistema", ["Real-time Capture", "Histórico & Analytics"])

if menu == "Real-time Capture":
    str_ui.header("📸 Captura de Mídia Integrada")
    col1, col2 = str_ui.columns(2)

    with col1:
        str_ui.subheader("Webcam Input")
        camera_photo = str_ui.camera_input("Foque no objetivo e capture a foto")
        str_ui.subheader("Comentário em Áudio")
        audio_file = str_ui.file_uploader("Opcional: Suba uma gravação (.wav)", type=["wav"])

    with col2:
        if camera_photo:
            str_ui.subheader("Visualização da Foto")
            str_ui.image(camera_photo, caption="Captura Pronta", use_column_width=True)
            if str_ui.button("⚡ Executar Pipeline de Processamento Automatizado"):
                with str_ui.spinner("Analisando frames..."):
                    img_bytes = camera_photo.getvalue()
                    aud_bytes = audio_file.getvalue() if audio_file else None
                    registro = controller.processar_fluxo_completo(img_bytes, aud_bytes)
                    str_ui.success("Análise persistida com sucesso!")
                    str_ui.json(registro.json_resultado)
                    if registro.transcricao:
                        str_ui.info(f"🗣️ Transcrição: {registro.transcricao}")
else:
    str_ui.header("📊 Painel Analítico & Histórico")
    col_f1, col_f2, col_f3 = str_ui.columns(3)
    with col_f1:
        search_query = str_ui.text_input("🔍 Buscar texto")
    with col_f2:
        start_d = str_ui.date_input("Data de Início", datetime.date.today() - datetime.timedelta(days=7))
    with col_f3:
        end_d = str_ui.date_input("Data Fim", datetime.date.today())

    registros = controller.listar_historico(search_query, start_d, end_d)
    if registros:
        data_dicts = [{"Data": r.created_at, "Pessoas": r.quantidade_pessoas, "Rostos": r.rostos, "Luminosidade": r.luminosidade, "Nitidez": r.nitidez} for r in registros]
        df = pd.DataFrame(data_dicts)
        
        db_col1, db_col2 = str_ui.columns(2)
        with db_col1:
            str_ui.plotly_chart(px.line(df, x="Data", y="Pessoas", title="Contagem Volumétrica"), use_container_width=True)
        with db_col2:
            str_ui.plotly_chart(px.histogram(df, x="Luminosidade", title="Luminosidade"), use_container_width=True)

        str_ui.subheader("💾 Exportação de Dados")
        exp_col1, exp_col2 = str_ui.columns(2)
        with exp_col1:
            str_ui.download_button("Exportar em CSV", data=df.to_csv(index=False), file_name="historico.csv", mime="text/csv")
        with exp_col2:
            str_ui.download_button("Exportar em JSON", data=df.to_json(orient="records"), file_name="historico.json", mime="application/json")

        for reg in registros:
            with str_ui.expander(f"Registro #{reg.id} - {reg.created_at.strftime('%d/%m/%Y %H:%M:%S')}"):
                c1, c2 = str_ui.columns([1, 2])
                with c1:
                    if os.path.exists(reg.image_path):
                        str_ui.image(reg.image_path, use_column_width=True)
                with c2:
                    str_ui.write(f"**Descrição:** {reg.descricao}")
                    str_ui.write(f"**Objetos:** {reg.objetos}")
                    if reg.transcricao:
                        str_ui.info(f"🗣️ Transcrição: {reg.transcricao}")
                    if str_ui.button(f"🗑️ Excluir Registro #{reg.id}", key=f"del_{reg.id}"):
                        controller.deletar_registro(reg.id)
                        str_ui.rerun()
""",

    "requirements.txt": """streamlit==1.32.0
opencv-python-headless==4.9.0.80
pillow==10.2.0
numpy==1.26.4
SQLAlchemy==2.0.28
alembic==1.13.1
psycopg[binary]==3.1.18
python-dotenv==1.0.1
faster-whisper==1.0.1
pandas==2.2.1
plotly==5.19.0
""",

    "runtime.txt": "python-3.12.2",
    
    ".env": "DATABASE_URL=sqlite:///local.db\nUPLOAD_FOLDER=assets/images\nSECRET_KEY=super-secret-key\n",
    
    ".gitignore": ".env\n__pycache__/\n*.pyc\nlogs/*.log\nassets/images/*\nassets/audio/*\n"
}

# Cria fisicamente as pastas e arquivos
for caminho, conteudo in estrutura.items():
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

print("✅ Estrutura completa gerada com sucesso em menos de 1 segundo!")
print("Instruções: Rode 'pip install -r requirements.txt' e depois 'streamlit run app.py'")