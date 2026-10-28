from datetime import datetime
import joblib
import pytest
from services.classificador import Classificador
from src.train import montar_pipeline


TEXTOS = [
    "excelente produto, recomendo muito",
    "produto excelente, entrega rápida",
    "muito bom, recomendo o produto",
    "ótimo produto, recomendo",
    "péssimo produto, não funciona",
    "produto horrível, não funciona",
    "muito ruim, péssimo produto",
    "qualidade horrível, não recomendo",
]
ROTULOS = ["positivo"] * 4 + ["negativo"] * 4


@pytest.fixture
def modelo_temporario(tmp_path):
    """Treina um modelo sintético rápido e salva em pasta temporária (tmp_path)."""
    pipeline = montar_pipeline()
    pipeline.fit(TEXTOS, ROTULOS)

    caminho = tmp_path / "modelo_teste.joblib"
    joblib.dump(pipeline, caminho)
    return caminho


def test_erro_quando_modelo_nao_existe(tmp_path):
    caminho_inexistente = tmp_path / "fantasma.joblib"
    with pytest.raises(FileNotFoundError, match="Arquivo do modelo não encontrado"):
        Classificador(caminho_modelo=str(caminho_inexistente))


def test_classificar_texto_individual(modelo_temporario):
    servico = Classificador(caminho_modelo=str(modelo_temporario))
    resultado = servico.classificar_texto("produto excelente, recomendo muito")

    assert resultado["classe"] == "positivo"
    assert 0.5 <= resultado["confianca"] <= 1.0
    assert resultado["modelo"] == "modelo_teste"
    assert isinstance(resultado["data"], datetime)


def test_classificar_documentos_em_lote(modelo_temporario):
    servico = Classificador(caminho_modelo=str(modelo_temporario))
    docs = [
        {"_id": "id_1", "texto": "produto excelente, recomendo"},
        {"_id": "id_2", "texto": "produto péssimo, não funciona"},
    ]
    predicoes = servico.classificar_documentos(docs)

    assert len(predicoes) == 2
    assert predicoes[0]["_id"] == "id_1"
    assert predicoes[0]["predicao"]["classe"] == "positivo"
    assert predicoes[1]["_id"] == "id_2"
    assert predicoes[1]["predicao"]["classe"] == "negativo"
