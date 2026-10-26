import pandas as pd
import pytest

from src.prepare_data import criar_rotulo, limpar, rotular


@pytest.mark.parametrize(
    "nota, esperado",
    [(5, "positivo"), (4, "positivo"), (2, "negativo"), (1, "negativo"), (3, None)],
)
def test_criar_rotulo(nota, esperado):
    assert criar_rotulo(nota) == esperado


def test_rotular_descarta_nota_3():
    df = pd.DataFrame({"texto": list("abcde"), "nota": [1, 2, 3, 4, 5]})
    resultado = rotular(df)

    assert len(resultado) == 4
    assert 3 not in resultado["nota"].values
    assert dict(zip(resultado["nota"], resultado["rotulo"])) == {
        1: "negativo",
        2: "negativo",
        4: "positivo",
        5: "positivo",
    }


def test_rotular_nao_altera_o_dataframe_original():
    df = pd.DataFrame({"texto": ["a"], "nota": [5]})
    rotular(df)
    assert "rotulo" not in df.columns


def test_limpar_remove_nulos_curtos_e_duplicados():
    df = pd.DataFrame(
        {
            "texto": [
                "  produto excelente, recomendo  ",  # fica (sem espaços nas pontas)
                None,                                 # texto nulo
                "ok",                                 # curto demais
                "produto excelente, recomendo",       # duplicado do primeiro
                "entrega atrasada demais",            # nota nula
                "entrega atrasada demais",            # fica
            ],
            "nota": [5, 5, 5, 5, None, 1],
        }
    )

    resultado = limpar(df)

    assert sorted(resultado["texto"]) == [
        "entrega atrasada demais",
        "produto excelente, recomendo",
    ]