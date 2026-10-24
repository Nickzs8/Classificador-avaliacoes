from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, classification_report

from config import MODEL_PATH
from repository import ReviewRepository


def carregar_modelo():
    caminho_modelo = Path(MODEL_PATH)

    if not caminho_modelo.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado em {caminho_modelo}. Execute o src/train.py primeiro."
        )

    modelo = joblib.load(caminho_modelo)
    print(f"Modelo carregado de: {caminho_modelo}")
    return modelo


def carregar_documentos():
    with ReviewRepository() as repo:
        return repo.buscar_sem_predicao()


def prever(modelo, documentos):
    # preve todos os textos de uma vez (uma linha de probabilidades por texto)
    textos = [d["texto"] for d in documentos]
    probabilidades = modelo.predict_proba(textos)
    posicoes = probabilidades.argmax(axis=1)  # posição da classe mais provável

    versao = Path(MODEL_PATH).stem  # "modelo_v1"
    agora = datetime.now(timezone.utc)

    predicoes = []
    for doc, probs, pos in zip(documentos, probabilidades, posicoes):
        predicoes.append(
            {
                "_id": doc["_id"],
                "predicao": {
                    "classe": str(modelo.classes_[pos]),
                    "confianca": float(probs[pos]),
                    "modelo": versao,
                    "data": agora,
                },
            }
        )
    return predicoes


def gravar_predicoes(predicoes):
    with ReviewRepository() as repo:
        return repo.gravar_predicoes(predicoes)


def avaliar(documentos, predicoes, n_erros=5):
    # o rotulo_real só é usado aqui, para avaliar
    reais = [d["rotulo_real"] for d in documentos]
    previstos = [p["predicao"]["classe"] for p in predicoes]

    print("\n" + "=" * 50)
    print("AVALIAÇÃO DAS PREDIÇÕES")
    print("=" * 50)
    print(f"Acurácia: {accuracy_score(reais, previstos):.3f}\n")
    print(classification_report(reais, previstos))

    erros = [
        (d, p)
        for d, p in zip(documentos, predicoes)
        if d["rotulo_real"] != p["predicao"]["classe"]
    ]
    print(f"Erros: {len(erros)} de {len(documentos)}")
    for doc, pred in erros[:n_erros]:
        print(
            f"- real={doc['rotulo_real']} | previsto={pred['predicao']['classe']} "
            f"({pred['predicao']['confianca']:.2f}) | {doc['texto'][:100]}"
        )


def classificar_pendentes():
    modelo = carregar_modelo()

    documentos = carregar_documentos()
    if not documentos:
        print("Nenhum documento pendente de predição.")
        return

    print(f"Documentos a classificar: {len(documentos)}")

    predicoes = prever(modelo, documentos)
    gravados = gravar_predicoes(predicoes)
    print(f"Predições gravadas: {gravados}")

    avaliar(documentos, predicoes)


if __name__ == "__main__":
    classificar_pendentes()