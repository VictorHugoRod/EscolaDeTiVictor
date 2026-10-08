"""persistencia em sqllite"""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from .dominio import Senha, Status, Tipo

ESQUEMA = """
CREATE TABLE IF NOT EXISTS senhas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT    NOT NULL,
    tipo          TEXT    NOT NULL,
    status        TEXT    NOT NULL,
    emissao       TEXT    NOT NULL,
    chamada_em    TEXT,
    ordem_chamada INTEGER
);
CREATE INDEX IF NOT EXISTS idx_senhas_codigo ON senhas (codigo);
CREATE INDEX IF NOT EXISTS idx_senhas_fila ON senhas (status, tipo, id);
CREATE INDEX IF NOT EXISTS idx_senhas_painel ON senhas (ordem_chamada);

CREATE TABLE IF NOT EXISTS sequencias (
    dia    TEXT    PRIMARY KEY,
    ultimo INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS contadores (
    chave TEXT    PRIMARY KEY,
    valor INTEGER NOT NULL
);
"""

COLUNAS = "id, codigo, tipo, status, emissao, chamada_em"


class RepositorioSenhas:

    def __init__(self, caminho_banco: str) -> None:
        self._conexao = sqlite3.connect(caminho_banco, check_same_thread=False)
        self._trava = threading.Lock()
        with self._conexao:
            self._conexao.executescript(ESQUEMA)

    @contextmanager
    def transacao(self) -> Iterator[None]:
        with self._trava, self._conexao:
            yield

    # ------------------------------------------------------------ sequencia

    def proximo_numero(self, dia: str) -> int:
        self._conexao.execute(
            "INSERT INTO sequencias (dia, ultimo) VALUES (?, 1) "
            "ON CONFLICT (dia) DO UPDATE SET ultimo = ultimo + 1",
            (dia,),
        )
        linha = self._conexao.execute(
            "SELECT ultimo FROM sequencias WHERE dia = ?", (dia,)
        ).fetchone()
        return int(linha[0])

    # ------------------------------------------------------------ contadores

    def ler_contador(self, chave: str) -> int:
        linha = self._conexao.execute(
            "SELECT valor FROM contadores WHERE chave = ?", (chave,)
        ).fetchone()
        return int(linha[0]) if linha else 0

    def gravar_contador(self, chave: str, valor: int) -> None:
        self._conexao.execute(
            "INSERT INTO contadores (chave, valor) VALUES (?, ?) "
            "ON CONFLICT (chave) DO UPDATE SET valor = excluded.valor",
            (chave, valor),
        )

    # ------------------------------------------------------------ senhas

    def inserir(self, senha: Senha) -> Senha:
        cursor = self._conexao.execute(
            "INSERT INTO senhas (codigo, tipo, status, emissao) VALUES (?, ?, ?, ?)",
            (senha.codigo, senha.tipo.value, senha.status.value, senha.emissao.isoformat()),
        )
        senha.id = cursor.lastrowid
        return senha

    def buscar_por_codigo(self, codigo: str) -> Senha | None:
        linha = self._conexao.execute(
            f"SELECT {COLUNAS} FROM senhas WHERE codigo = ? ORDER BY id DESC LIMIT 1",
            (codigo,),
        ).fetchone()
        return _para_senha(linha) if linha else None

    def primeira_aguardando(self, tipo: Tipo) -> Senha | None:
        linha = self._conexao.execute(
            f"SELECT {COLUNAS} FROM senhas WHERE status = ? AND tipo = ? ORDER BY id LIMIT 1",
            (Status.AGUARDANDO.value, tipo.value),
        ).fetchone()
        return _para_senha(linha) if linha else None

    def registrar_chamada(self, senha: Senha) -> None:
        self._conexao.execute(
            "UPDATE senhas SET status = ?, chamada_em = ?, "
            "ordem_chamada = (SELECT COALESCE(MAX(ordem_chamada), 0) + 1 FROM senhas) "
            "WHERE id = ?",
            (senha.status.value, _data_ou_nulo(senha.chamada_em), senha.id),
        )

    def atualizar_status(self, senha: Senha) -> None:
        self._conexao.execute(
            "UPDATE senhas SET status = ? WHERE id = ?", (senha.status.value, senha.id)
        )

    def ultimas_chamadas(self, limite: int) -> list[Senha]:
        linhas = self._conexao.execute(
            f"SELECT {COLUNAS} FROM senhas WHERE ordem_chamada IS NOT NULL "
            "ORDER BY ordem_chamada DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [_para_senha(linha) for linha in linhas]


def _data_ou_nulo(momento: datetime | None) -> str | None:
    return momento.isoformat() if momento else None


def _para_senha(linha: tuple) -> Senha:
    id_, codigo, tipo, status, emissao, chamada_em = linha
    return Senha(
        id=id_,
        codigo=codigo,
        tipo=Tipo(tipo),
        status=Status(status),
        emissao=datetime.fromisoformat(emissao),
        chamada_em=datetime.fromisoformat(chamada_em) if chamada_em else None,
    )
