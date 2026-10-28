from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status

from api.dependencies import get_repositorio, get_classificador
from api.schemas import AvaliacaoEntrada, AvaliacaoSaida, SaudeSaida
from repository import ReviewRepository
from services.classificador import Classificador

app = FastAPI(
    title="API de Classificação de Avaliações",
    description="Classificação em tempo real de sentimento de avaliações de e-commerce em português.",
    version="2.0.0",
)


@app.post(
    "/avaliacoes",
    response_model=AvaliacaoSaida,
    status_code=status.HTTP_201_CREATED,
    tags=["Avaliações"],
)
def criar_avaliacao(
    payload: AvaliacaoEntrada,
    repo: ReviewRepository = Depends(get_repositorio),
    classificador: Classificador = Depends(get_classificador),
):
    """Classifica uma avaliação enviada pelo usuário e persiste o resultado no banco."""

    # 1. Inferência com o modelo
    predicao = classificador.classificar_texto(payload.texto)

    # 2. Montagem do documento BSON
    documento = {
        "texto": payload.texto,
        "produto": payload.produto,
        "data": predicao["data"],
        "nota": None,
        "rotulo": None,
        "rotulo_real": None,
        "predicao": {
            "classe": predicao["classe"],
            "confianca": predicao["confianca"],
            "modelo": predicao["modelo"],
            "data": predicao["data"],
        },
        "origem": "api",
    }

    # 3. Gravação no MongoDB
    id_gerado = repo.inserir_avaliacao(documento)

    # 4. Retorno estruturado no DTO de saída
    return AvaliacaoSaida(
        id=id_gerado,
        texto=payload.texto,
        produto=payload.produto,
        classe=predicao["classe"],
        confianca=predicao["confianca"],
        modelo=predicao["modelo"],
        data=predicao["data"],
    )


@app.get(
    "/avaliacoes/{id}",
    response_model=AvaliacaoSaida,
    tags=["Avaliações"],
)
def obter_avaliacao(
    id: str,
    repo: ReviewRepository = Depends(get_repositorio),
):
    """Busca uma avaliação específica pelo seu ID hexadecimal."""
    doc = repo.buscar_por_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avaliação com ID '{id}' não foi encontrada.",
        )

    # Trata documentos da API ou legados com subdocumento predicao
    pred = doc.get("predicao") or {}
    return AvaliacaoSaida(
        id=doc["_id"],
        texto=doc["texto"],
        produto=doc.get("produto"),
        classe=pred.get("classe") or doc.get("rotulo") or "positivo",
        confianca=pred.get("confianca", 1.0),
        modelo=pred.get("modelo", "legado"),
        data=doc.get("data") or pred.get("data"),
    )


@app.get(
    "/avaliacoes",
    response_model=List[AvaliacaoSaida],
    tags=["Avaliações"],
)
def listar_avaliacoes(
    limite: int = Query(default=10, ge=1, le=100, description="Quantidade máxima de itens retornados"),
    repo: ReviewRepository = Depends(get_repositorio),
):
    """Lista as avaliações mais recentes cadastradas na base."""
    docs = repo.listar_recentes(limite=limite)
    resultado = []
    for doc in docs:
        pred = doc.get("predicao") or {}
        resultado.append(
            AvaliacaoSaida(
                id=doc["_id"],
                texto=doc["texto"],
                produto=doc.get("produto"),
                classe=pred.get("classe") or doc.get("rotulo") or "positivo",
                confianca=pred.get("confianca", 1.0),
                modelo=pred.get("modelo", "legado"),
                data=doc.get("data") or pred.get("data"),
            )
        )
    return resultado


@app.get(
    "/saude",
    response_model=SaudeSaida,
    tags=["Monitoramento"],
)
def verificar_saude(
    response: Response,
    repo: ReviewRepository = Depends(get_repositorio),
    classificador: Classificador = Depends(get_classificador),
):
    """Healthcheck: valida conectividade do MongoDB e carregamento do modelo na memória."""
    banco_ok = repo.ping()
    modelo_ok = classificador is not None and classificador.modelo is not None

    if not banco_ok or not modelo_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return SaudeSaida(status="erro", banco=banco_ok, modelo=modelo_ok)

    return SaudeSaida(status="ok", banco=True, modelo=True)