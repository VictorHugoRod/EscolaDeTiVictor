"""casos de uso da fial de atendimento"""

from collections.abc import Callable
from datetime import datetime
from .dominio import FilaVazia, Senha, SenhaNaoEncontrada, Tipo, agora
from .repositorio import RepositorioSenhas

TAMANHO_PAINEL = 5
CONTADOR_PREFERENCIAIS_SEGUIDAS = "preferenciais_seguidas"

class FilaService:
    def __init__(
        self,
        repositorio: RepositorioSenhas,
        prefixo: str,
        razao_preferencial: int,
        relogio: Callable[[], datetime] = agora,
    ) -> None:
        self._repositorio = repositorio
        self._prefixo = prefixo
        self._razao_preferencial = razao_preferencial
        self._relogio = relogio

    def emitir(self, tipo_informado: object) -> Senha:
        tipo = Tipo.de_valor(tipo_informado)
        momento = self._relogio()
        with self._repositorio.transacao():
            
            numero = self._repositorio.proximo_numero(momento.date().isoformat())
            senha = Senha(
                id=None, codigo=f"{self._prefixo}{numero:03d}", tipo=tipo, emissao=momento
            )
            return self._repositorio.inserir(senha)

    def chamar_proxima(self) -> Senha:
        with self._repositorio.transacao():
            seguidas = self._repositorio.ler_contador(CONTADOR_PREFERENCIAIS_SEGUIDAS)
            senha = self._escolher_proxima(seguidas)
            if senha is None:
                raise FilaVazia()

            senha.chamar(self._relogio())
            self._repositorio.registrar_chamada(senha)

            seguidas = seguidas + 1 if senha.tipo is Tipo.PREFERENCIAL else 0
            self._repositorio.gravar_contador(CONTADOR_PREFERENCIAIS_SEGUIDAS, seguidas)
            return senha

    def concluir(self, codigo: str) -> Senha:
        with self._repositorio.transacao():
            senha = self._obter(codigo)
            senha.concluir()
            self._repositorio.atualizar_status(senha)
            return senha

    def rechamar(self, codigo: str) -> Senha:
        with self._repositorio.transacao():
            senha = self._obter(codigo)
            senha.rechamar(self._relogio())
            self._repositorio.registrar_chamada(senha)
            return senha

    def cancelar(self, codigo: str) -> Senha:
        with self._repositorio.transacao():
            senha = self._obter(codigo)
            senha.cancelar()
            self._repositorio.atualizar_status(senha)
            return senha

    def painel(self) -> list[Senha]:
        with self._repositorio.transacao():
            return self._repositorio.ultimas_chamadas(TAMANHO_PAINEL)

    def _escolher_proxima(self, preferenciais_seguidas: int) -> Senha | None:
        normal = self._repositorio.primeira_aguardando(Tipo.NORMAL)
        if normal and preferenciais_seguidas >= self._razao_preferencial:
            return normal
        preferencial = self._repositorio.primeira_aguardando(Tipo.PREFERENCIAL)
        return preferencial or normal

    def _obter(self, codigo: str) -> Senha:
        senha = self._repositorio.buscar_por_codigo(codigo)
        if senha is None:
            raise SenhaNaoEncontrada()
        return senha
