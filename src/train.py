from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config import MODEL_PATH
from repository import ReviewRepository


def carregar_dados():
    with ReviewRepository() as repo:
        documentos = repo.buscar_rotulados()

    if not documentos:
        raise ValueError(
            "Nenhum documento rotulado encontrado no MongoDB. Execute o src/ingest.py primeiro."
        )

    df = pd.DataFrame(documentos)
    print(f"Dados carregados do MongoDB: {len(df)} documentos rotulados.")
    return df

def montar_pipeline():
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),  # unigramas e bigramas
                    min_df=2,  # descarta palavras/expressões que aparecem em menos de 2 textos
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",  # pondera a perda para compensar a minoria de negativos
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )

def predizer_conjunto(pipeline, X_test):
    return pipeline.predict(X_test)


def treinar_modelo():
    # carregar dados
    df = carregar_dados()
    X = df["texto"]
    y = df["rotulo"]

    # dividir em Treino (80%) e Teste (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(
        f"Base dividida: {len(X_train)} amostras de treino e {len(X_test)} de teste.\n"
    )

    pipeline = montar_pipeline()

    # treinar o modelo
    print("Treinando o pipeline...")
    pipeline.fit(X_train, y_train)

    # avaliar no conjunto de teste
    y_pred = predizer_conjunto(pipeline, X_test)

    print("\n" + "=" * 50)
    print("RELATÓRIO DE CLASSIFICAÇÃO (TESTE)")
    print("=" * 50)
    print(classification_report(y_test, y_pred))

    # salvar o modelo em disco
    caminho_modelo = Path(MODEL_PATH)
    caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, caminho_modelo)
    print(f"Modelo salvo com sucesso em: {caminho_modelo}")


if __name__ == "__main__":
    treinar_modelo()