"""entidades, regras de transicao de estado e erros de negocio"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

FUSO_HORARIO = timezone(timedelta(hours=-3))


def agora() -> datetime:
    return datetime.now(FUSO_HORARIO)


def formatar_data_hora(momento: datetime) -> str:
    return momento.astimezone(FUSO_HORARIO).isoformat(timespec="seconds")


# ---------------------------------------------------------------- erros


class ErroDeNegocio(Exception):
    """base dos erros de regra de negocio, codigo vai no corpo da resposta"""

    codigo = "erro_de_negocio"


class TipoInvalido(ErroDeNegocio):
    codigo = "tipo_invalido"


class FilaVazia(ErroDeNegocio):
    codigo = "fila_vazia"


class SenhaNaoEncontrada(ErroDeNegocio):
    codigo = "senha_nao_encontrada"


class SenhaNaoChamada(ErroDeNegocio):
    codigo = "senha_nao_chamada"


class SenhaNaoAguardando(ErroDeNegocio):
    codigo = "senha_nao_aguardando"


# -------------------------------------------------------------- valores


class Tipo(StrEnum):
    NORMAL = "normal"
    PREFERENCIAL = "preferencial"

    @classmethod
    def de_valor(cls, valor: object) -> "Tipo":
        if not isinstance(valor, str):
            raise TipoInvalido()
        try:
            return cls(valor)
        except ValueError as erro:
            raise TipoInvalido() from erro


class Status(StrEnum):
    AGUARDANDO = "aguardando"
    CHAMADA = "chamada"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


# -------------------------------------------------------------- entidade


@dataclass
class Senha:
    id: int | None
    codigo: str
    tipo: Tipo
    emissao: datetime
    status: Status = Status.AGUARDANDO
    chamada_em: datetime | None = None

    def chamar(self, momento: datetime) -> None:
        if self.status is not Status.AGUARDANDO:
            raise SenhaNaoAguardando()
        self.status = Status.CHAMADA
        self.chamada_em = momento

    def rechamar(self, momento: datetime) -> None:
        if self.status is not Status.CHAMADA:
            raise SenhaNaoChamada()
        self.chamada_em = momento

    def concluir(self) -> None:
        if self.status is not Status.CHAMADA:
            raise SenhaNaoChamada()
        self.status = Status.CONCLUIDA

    def cancelar(self) -> None:
        if self.status is not Status.AGUARDANDO:
            raise SenhaNaoAguardando()
        self.status = Status.CANCELADA

    def para_dict(self) -> dict:
        corpo = {
            "codigo": self.codigo,
            "tipo": self.tipo.value,
            "emissao": formatar_data_hora(self.emissao),
            "status": self.status.value,
        }
        if self.chamada_em is not None:
            corpo["chamada_em"] = formatar_data_hora(self.chamada_em)
        return corpo
