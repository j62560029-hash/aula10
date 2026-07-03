import os
import whisper
from config.settings import logger

class STTService:
    def __init__(self):
        self.model = None

    def _lazy_init(self):
        if self.model is None:
            logger.info("A carregar o modelo OpenAI Whisper...")
            self.model = whisper.load_model("tiny")

    def transcrever_audio(self, audio_path: str) -> str:
        try:
            if not os.path.exists(audio_path):
                return "Arquivo de áudio não encontrado."
            
            self._lazy_init()
            
            # O OpenAI Whisper devolve um dicionário com o texto direto
            result = self.model.transcribe(audio_path)
            transcricao = result.get("text", "")
            
            return transcricao.strip()
        except Exception as e:
            logger.error(f"Erro na transcrição de áudio: {str(e)}")
            return f"Erro ao transcrever áudio: {str(e)}"