from datetime import datetime

import joblib
import pytest

import src.predict as predict
from src.config import MODEL_PATH
from src.train import montar_pipeline

TEXTOS = [
    # positivos
    "excelente produto, recomendo",
    "ótimo produto, recomendo muito",
    "excelente qualidade, adorei",
    "chegou rápido, produto excelente",
    "adorei, produto ótimo",
    "ótima qualidade, recomendo",
    "produto excelente, chegou antes do prazo",
    "muito bom, excelente, recomendo",
    # negativos
    "péssimo produto, não funciona",
    "produto péssimo, não compensa",
    "não funciona, qualidade péssima",
    "chegou quebrado, produto péssimo",
    "horrível, não funciona nada",
    "qualidade horrível, não compensa",
    "produto horrível, chegou quebrado",
    "muito ruim, péssimo, não compensa",
]
ROTULOS = ["positivo"] * 8 + ["negativo"] * 8


@pytest.fixture(scope="module")
def modelo():
    pipeline = montar_pipeline()
    pipeline.fit(TEXTOS, ROTULOS)
    return pipeline


def test_classifica_frases_obvias(modelo):
    previsoes = modelo.predict(["excelente, recomendo", "péssimo, não funciona"])
    assert list(previsoes) == ["positivo", "negativo"]


def test_probabilidades_somam_1(modelo):
    probs = modelo.predict_proba(["excelente, recomendo"])

    assert probs.shape == (1, 2)
    assert probs.sum() == pytest.approx(1.0)
    assert list(modelo.classes_) == ["negativo", "positivo"]


def test_modelo_salvo_e_carregado_preve_igual(modelo, tmp_path):
    caminho = tmp_path / "modelo_teste.joblib"
    joblib.dump(modelo, caminho)
    carregado = joblib.load(caminho)

    frases = ["excelente, recomendo", "péssimo, não funciona"]
    assert list(carregado.predict(frases)) == list(modelo.predict(frases))


def test_prever_monta_predicao_no_formato_do_banco(modelo, monkeypatch):
    # o nome da versão vem do nome do arquivo do modelo
    monkeypatch.setattr(predict, "MODEL_PATH", "models/modelo_teste.joblib")
    documentos = [{"_id": 1, "texto": "excelente, recomendo", "rotulo_real": "positivo"}]

    predicoes = predict.prever(modelo, documentos)

    assert len(predicoes) == 1
    predicao = predicoes[0]["predicao"]
    assert predicoes[0]["_id"] == 1
    assert predicao["classe"] == "positivo"
    assert 0.5 <= predicao["confianca"] <= 1.0
    assert predicao["modelo"] == "modelo_teste"
    assert isinstance(predicao["data"], datetime)