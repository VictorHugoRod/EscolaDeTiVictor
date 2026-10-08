"""camada http"""

from flask import Blueprint, jsonify, request

from .servico import FilaService


def criar_rotas(servico: FilaService) -> Blueprint:
    rotas = Blueprint("fila", __name__)

    @rotas.get("/healthz")
    def healthz():
        return jsonify(status="ok"), 200

    @rotas.post("/senhas")
    def emitir_senha():
        corpo = request.get_json(silent=True)
        tipo = corpo.get("tipo") if isinstance(corpo, dict) else None
        senha = servico.emitir(tipo)
        return jsonify(senha.para_dict()), 201

    @rotas.get("/senhas/proxima")
    def proxima_senha():
        return jsonify(servico.chamar_proxima().para_dict()), 200

    @rotas.post("/senhas/<codigo>/concluir")
    def concluir_senha(codigo: str):
        return jsonify(servico.concluir(codigo).para_dict()), 200

    @rotas.post("/senhas/<codigo>/rechamar")
    def rechamar_senha(codigo: str):
        return jsonify(servico.rechamar(codigo).para_dict()), 200

    @rotas.post("/senhas/<codigo>/cancelar")
    def cancelar_senha(codigo: str):
        return jsonify(servico.cancelar(codigo).para_dict()), 200

    @rotas.get("/painel")
    def painel():
        chamadas = [senha.para_dict() for senha in servico.painel()]
        return jsonify(chamadas=chamadas), 200

    return rotas
