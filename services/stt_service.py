import os
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
