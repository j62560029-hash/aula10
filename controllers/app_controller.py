import uuid
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
