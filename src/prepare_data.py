from pathlib import Path

import pandas as pd

RAW = Path("data/raw/B2W-Reviews01.csv")
OUT = Path("data/reviews.csv")
AMOSTRA = 20_000
MIN_CARACTERES = 10
SEED = 42

# nome da coluna no CSV original → nome usado no projeto
COLUNAS = {
    "overall_rating": "nota",
    "review_text": "texto",
    "product_name": "produto",
    "submission_date": "data",
}


def carregar_bruto(caminho):
    """Lê o CSV original e deixa só as colunas que importam, já renomeadas."""
    df = pd.read_csv(caminho, sep=";", low_memory=False)
    df = df.rename(columns=COLUNAS)

    return df[["texto", "nota", "produto", "data"]]


def limpar(df):
    """Remove nulos, textos muito curtos e duplicados."""
    df = df.dropna(subset=["texto", "nota"]).copy()
    df["texto"] = df["texto"].str.strip()
    df = df[df["texto"].str.len() >= MIN_CARACTERES]

    return df.drop_duplicates(subset="texto")


def criar_rotulo(nota):
    """Nota 4/5 → positivo, 1/2 → negativo, 3 → None (neutra, será descartada)."""
    if nota >= 4:
        return "positivo"

    if nota <= 2:
        return "negativo"

    return None


def rotular(df):
    """Cria a coluna 'rotulo' e descarta as notas neutras."""
    df = df.copy()
    df["rotulo"] = df["nota"].apply(criar_rotulo)

    return df.dropna(subset=["rotulo"])


def amostrar(df, n=AMOSTRA):
    """Amostra reprodutível (só se houver mais linhas que o necessário)."""
    if len(df) > n:
        return df.sample(n, random_state=SEED)

    return df


def preparar(df):
    return amostrar(rotular(limpar(df)))


def main():
    df = preparar(carregar_bruto(RAW))
    df.to_csv(OUT, index=False)

    print(f"Salvo em {OUT}: {len(df)} linhas")
    print(df["rotulo"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()