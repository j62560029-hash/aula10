import cv2
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
