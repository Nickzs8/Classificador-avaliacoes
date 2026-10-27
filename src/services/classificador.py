from datetime import datetime, timezone
from pathlib import Path
import joblib

from config import MODEL_PATH


class Classificador:
    """Camada de serviço responsável por carregar o modelo e executar inferências."""

    def __init__(self, caminho_modelo: str = MODEL_PATH):
        self.caminho = Path(caminho_modelo)

        if not self.caminho.exists():
            raise FileNotFoundError(
                f"Arquivo do modelo não encontrado em '{self.caminho}'. "
                "Execute 'python run_pipeline.py' para treinar e gerar o artefato."
            )

        self.modelo = joblib.load(self.caminho)
        self.versao = self.caminho.stem  # Extrai 'modelo_v1' a partir de 'models/modelo_v1.joblib'

    def classificar_texto(self, texto: str) -> dict:
        """Classifica um único texto"""
        probs = self.modelo.predict_proba([texto])[0]
        pos = probs.argmax()

        return {
            "classe": str(self.modelo.classes_[pos]),
            "confianca": round(float(probs[pos]), 4),
            "modelo": self.versao,
            "data": datetime.now(timezone.utc),
        }

    def classificar_documentos(self, documentos: list[dict]) -> list[dict]:
        """Classifica múltiplos documentos em lote."""
        if not documentos:
            return []

        textos = [d["texto"] for d in documentos]
        probabilidades = self.modelo.predict_proba(textos)
        posicoes = probabilidades.argmax(axis=1)
        agora = datetime.now(timezone.utc)

        predicoes = []
        for doc, probs, pos in zip(documentos, probabilidades, posicoes):
            predicoes.append(
                {
                    "_id": doc["_id"],
                    "predicao": {
                        "classe": str(self.modelo.classes_[pos]),
                        "confianca": round(float(probs[pos]), 4),
                        "modelo": self.versao,
                        "data": agora,
                    },
                }
            )
        return predicoes