from pathlib import Path
import pandas as pd
from repository import ReviewRepository

CSV = Path("data/reviews.csv")
PROPORCAO_SEM_ROTULO = 0.10
SEED = 42


def carregar_csv(caminho):
    df = pd.read_csv(caminho)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def montar_documentos(df):
    # transforma cada linha do DataFrame em um documento do MongoDB.
    # sorteia 10% das linhas para entrarem sem rótulo

    sem_rotulo = set(df.sample(frac=PROPORCAO_SEM_ROTULO, random_state=SEED).index)

    documentos = []
    for linha in df.itertuples():
        documentos.append({
            "texto": linha.texto,
            "produto": None if pd.isna(linha.produto) else linha.produto,
            "data": None if pd.isna(linha.data) else linha.data.to_pydatetime(),
            "nota": int(linha.nota),
            "rotulo": None if linha.Index in sem_rotulo else linha.rotulo,
            "rotulo_real": linha.rotulo,
            "predicao": None,
        })
    return documentos


def main():
    df = carregar_csv(CSV)
    print(f"CSV lido: {len(df)} linhas")

    documentos = montar_documentos(df)

    with ReviewRepository() as repo:
        repo.limpar()
        inseridos = repo.inserir_varios(documentos)
        repo.criar_indices()

        print(f"Inseridos: {inseridos} documentos")
        print("Documentos por rótulo:", repo.contar_por_rotulo())


if __name__ == "__main__":
    main()