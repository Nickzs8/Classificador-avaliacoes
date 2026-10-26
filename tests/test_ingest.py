from datetime import datetime

import pandas as pd

from src.ingest import carregar_csv, montar_documentos


def criar_df(n=100):
    return pd.DataFrame(
        {
            "texto": [f"texto de exemplo {i}" for i in range(n)],
            "nota": [5 if i % 2 == 0 else 1 for i in range(n)],
            "produto": [f"produto {i % 3}" for i in range(n)],
            "data": pd.date_range("2018-01-01", periods=n, freq="D"),
            "rotulo": ["positivo" if i % 2 == 0 else "negativo" for i in range(n)],
        }
    )


def test_cerca_de_10_por_cento_fica_sem_rotulo():
    documentos = montar_documentos(criar_df(100))
    sem_rotulo = [d for d in documentos if d["rotulo"] is None]
    assert len(sem_rotulo) == 10


def test_rotulo_real_sempre_preenchido():
    for doc in montar_documentos(criar_df()):
        assert doc["rotulo_real"] in ("positivo", "negativo")


def test_rotulo_quando_existe_e_igual_ao_real():
    for doc in montar_documentos(criar_df()):
        assert doc["rotulo"] in (None, doc["rotulo_real"])


def test_data_vira_datetime_do_python():
    documentos = montar_documentos(criar_df())
    assert all(type(d["data"]) is datetime for d in documentos)


def test_valores_ausentes_viram_none():
    df = criar_df()
    df.loc[0, "data"] = pd.NaT
    df.loc[0, "produto"] = None

    doc = montar_documentos(df)[0]

    assert doc["data"] is None
    assert doc["produto"] is None


def test_campos_iniciais_do_documento():
    doc = montar_documentos(criar_df())[0]

    assert doc["predicao"] is None
    assert isinstance(doc["nota"], int)
    assert set(doc) == {
        "texto", "produto", "data", "nota", "rotulo", "rotulo_real", "predicao",
    }


def test_sorteio_e_reprodutivel():
    a = [d["rotulo"] is None for d in montar_documentos(criar_df())]
    b = [d["rotulo"] is None for d in montar_documentos(criar_df())]
    assert a == b


def test_carregar_csv_converte_data(tmp_path):
    caminho = tmp_path / "reviews.csv"
    caminho.write_text(
        "texto,nota,produto,data,rotulo\n"
        "ótimo produto,5,A,2018-03-12 14:05:00,positivo\n"
        "muito ruim,1,B,data-invalida,negativo\n",
        encoding="utf-8",
    )

    df = carregar_csv(caminho)

    assert pd.api.types.is_datetime64_any_dtype(df["data"])
    assert pd.isna(df.loc[1, "data"])  # data inválida vira NaT