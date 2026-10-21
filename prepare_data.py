from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
RAW = ROOT_DIR / "data" / "raw" / "B2W-Reviews01.csv"
OUT = ROOT_DIR / "data" / "reviews.csv"
AMOSTRA = 20_000

if not RAW.exists():
    raise FileNotFoundError(
        f"Ficheiro não encontrado em: {RAW}\n"
        "Verifique se o ficheiro B2W-Reviews01.csv está salvo na pasta data/raw/."
    )

# 1)
df = pd.read_csv(RAW, sep=",", low_memory=False)

df = df.rename(
    columns={
        "overall_rating": "nota",
        "review_text": "texto",
        "product_name": "produto",
        "submission_date": "data",
    }
)
df = df[["texto", "nota", "produto", "data"]]

# 2) Limpeza
df = df.dropna(subset=["texto", "nota"])
df["texto"] = df["texto"].str.strip()
df = df[df["texto"].str.len() >= 10]
df = df.drop_duplicates(subset="texto")

# 3) Rótulo a partir da nota (descartando a nota 3)
df = df[df["nota"] != 3]
df["rotulo"] = df["nota"].apply(lambda n: "positivo" if n >= 4 else "negativo")

# 4) Amostra reprodutível
if len(df) > AMOSTRA:
    df = df.sample(AMOSTRA, random_state=42)

# 5) Guardar
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)

print(f"Salvo com sucesso em {OUT}: {len(df)} linhas")
print("\nDistribuição de rótulos:")
print(df["rotulo"].value_counts(normalize=True).round(3))