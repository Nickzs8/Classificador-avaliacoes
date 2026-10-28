from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report

from services.classificador import Classificador
from config import MODEL_PATH
from repository import ReviewRepository


def prever(modelo, documentos):
    """Extrai predições para documentos usando um modelo"""
    textos = [d["texto"] for d in documentos]
    probabilidades = modelo.predict_proba(textos)
    posicoes = probabilidades.argmax(axis=1)

    versao = Path(MODEL_PATH).stem
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


def carregar_documentos():
    with ReviewRepository() as repo:
        return repo.buscar_sem_predicao()


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
    classificador = Classificador()

    documentos = carregar_documentos()
    if not documentos:
        print("Nenhum documento pendente de predição.")
        return

    print(f"Documentos a classificar: {len(documentos)}")

    predicoes = classificador.classificar_documentos(documentos)
    gravados = gravar_predicoes(predicoes)
    print(f"Predições gravadas: {gravados}")

    avaliar(documentos, predicoes)


if __name__ == "__main__":
    classificar_pendentes()
