import pandas as pd

from repository import ReviewRepository

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", None)


def pivotar_evolucao(df):
    """Transforma (mes, sentimento, total) em uma tabela: uma linha por mês."""
    if df.empty:
        return df
    return (
        df.pivot(index="mes", columns="sentimento", values="total")
        .fillna(0)
        .astype(int)
    )


def carregar_analises():
    """Roda as agregações no MongoDB e devolve tudo pronto como DataFrames."""
    with ReviewRepository() as repo:
        return {
            "total": repo.contar(),
            "com_data": repo.contar({"data": {"$ne": None}}),
            "negativas_por_produto": pd.DataFrame(repo.negativas_por_produto()),
            "evolucao_por_mes": pivotar_evolucao(pd.DataFrame(repo.evolucao_por_mes())),
            "confianca_media": pd.DataFrame(repo.confianca_media_por_classe()),
            "taxa_acerto": pd.DataFrame(repo.taxa_acerto()),
        }


def mostrar(titulo, df, index=False):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)
    if df.empty:
        print("(sem dados)")
    else:
        print(df.to_string(index=index))


def conferir(analises):
    """Confere se a soma por mês bate com o total de documentos que têm data."""
    evolucao = analises["evolucao_por_mes"]
    soma = int(evolucao.sum().sum()) if not evolucao.empty else 0
    print("\n" + "=" * 60)
    print("CONFERÊNCIA")
    print("=" * 60)
    print(f"Soma por mês: {soma} | Documentos com data: {analises['com_data']}")


def main():
    analises = carregar_analises()
    print(f"Total de documentos: {analises['total']}")

    mostrar("TOP PRODUTOS COM MAIS AVALIAÇÕES NEGATIVAS", analises["negativas_por_produto"])
    mostrar("EVOLUÇÃO POR MÊS", analises["evolucao_por_mes"], index=True)
    mostrar("CONFIANÇA MÉDIA POR CLASSE PREVISTA", analises["confianca_media"])
    mostrar("TAXA DE ACERTO", analises["taxa_acerto"])
    conferir(analises)


if __name__ == "__main__":
    main()