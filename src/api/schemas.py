from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class AvaliacaoEntrada(BaseModel):
    texto: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Texto da avaliação do produto",
        examples=["O produto é excelente, entrega muito rápida!"],
    )
    produto: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Nome ou modelo do produto (opcional)",
        examples=["Fone Bluetooth X"],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto_nao_vazio(cls, valor: str) -> str:
        texto_limpo = valor.strip()
        if len(texto_limpo) < 3:
            raise ValueError("O texto não pode ser composto apenas por espaços em branco.")
        return texto_limpo


class AvaliacaoSaida(BaseModel):
    id: str = Field(..., description="ID único gerado pelo MongoDB")
    texto: str = Field(..., description="Texto original submetido")
    produto: Optional[str] = Field(None, description="Nome do produto")
    classe: Literal["positivo", "negativo"] = Field(..., description="Sentimento inferido pelo modelo")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Grau de certeza da predição (0.0 a 1.0)")
    modelo: str = Field(..., description="Identificador da versão do modelo que realizou a inferência")
    data: datetime = Field(..., description="Data e hora UTC da inferência e gravação")


class SaudeSaida(BaseModel):
    status: Literal["ok", "erro"]
    banco: bool = Field(..., description="Status de conectividade com o MongoDB")
    modelo: bool = Field(..., description="Status de carregamento do modelo .joblib em memória")
