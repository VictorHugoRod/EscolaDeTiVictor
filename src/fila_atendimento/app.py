"""factory do app flask que monta as camadas e os tratamentos de erro"""

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .config import Config
from .dominio import (
    ErroDeNegocio,
    FilaVazia,
    SenhaNaoAguardando,
    SenhaNaoChamada,
    SenhaNaoEncontrada,
    TipoInvalido,
)
from .repositorio import RepositorioSenhas
from .rotas import criar_rotas
from .servico import FilaService

logger = logging.getLogger(__name__)

STATUS_HTTP_POR_ERRO: dict[type[ErroDeNegocio], int] = {
    TipoInvalido: 422,
    FilaVazia: 404,
    SenhaNaoEncontrada: 404,
    SenhaNaoChamada: 409,
    SenhaNaoAguardando: 409,
}


def create_app(config: Config | None = None) -> Flask:
    config = config or Config.carregar()

    repositorio = RepositorioSenhas(config.caminho_banco)
    servico = FilaService(repositorio, config.prefixo, config.razao_preferencial)

    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(criar_rotas(servico))
    _registrar_tratadores_de_erro(app)

    logger.info(
        "Fila pronta (prefixo=%s, razao=%d, persistencia=%s)",
        config.prefixo,
        config.razao_preferencial,
        config.caminho_banco if config.persistente else "memoria",
    )
    return app


def _registrar_tratadores_de_erro(app: Flask) -> None:
    @app.errorhandler(ErroDeNegocio)
    def erro_de_negocio(erro: ErroDeNegocio):
        return jsonify(erro=erro.codigo), STATUS_HTTP_POR_ERRO.get(type(erro), 400)

    @app.errorhandler(HTTPException)
    def erro_http(erro: HTTPException):
        codigo = (erro.name or "erro").lower().replace(" ", "_")
        return jsonify(erro=codigo), erro.code

    @app.errorhandler(Exception)
    def erro_inesperado(erro: Exception):
        logger.exception("Erro inesperado", exc_info=erro)
        return jsonify(erro="erro_interno"), 500
