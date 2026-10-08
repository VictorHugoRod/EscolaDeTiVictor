"""configuração da aplicação"""

import os
from dataclasses import dataclass
from pathlib import Path

PREFIXO_PADRAO = "E"
RAZAO_PREFERENCIAL_PADRAO = 2
PORTA_PADRAO = 8080

DIRETORIO_DADOS = Path("/data")
NOME_ARQUIVO_BANCO = "fila.db"
BANCO_EM_MEMORIA = ":memory:"


@dataclass(frozen=True)
class Config:
    prefixo: str
    razao_preferencial: int
    porta: int
    caminho_banco: str

    @classmethod
    def carregar(cls) -> "Config":
        return cls(
            prefixo=os.getenv("FILA_PREFIXO", PREFIXO_PADRAO),
            razao_preferencial=int(
                os.getenv("FILA_RAZAO_PREFERENCIAL", str(RAZAO_PREFERENCIAL_PADRAO))
            ),
            porta=int(os.getenv("PORTA", str(PORTA_PADRAO))),
            caminho_banco=os.getenv("FILA_CAMINHO_BANCO") or _caminho_banco_padrao(),
        )

    @property
    def persistente(self) -> bool:
        return self.caminho_banco != BANCO_EM_MEMORIA


def _caminho_banco_padrao() -> str:
    """usa /data quando exsite senao memoria"""
    if DIRETORIO_DADOS.is_dir() and os.access(DIRETORIO_DADOS, os.W_OK):
        return str(DIRETORIO_DADOS / NOME_ARQUIVO_BANCO)
    return BANCO_EM_MEMORIA
