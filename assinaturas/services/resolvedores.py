from __future__ import annotations

from dataclasses import dataclass

from cadastros.models import AssinaturaConfiguracao
from cadastros.models import ConfiguracaoSistema
from documentos.models import DocumentoArtefato
from documentos.services.types import DocumentoTipo


class AssinanteNaoConfiguradoError(ValueError):
    pass


@dataclass(frozen=True)
class AssinanteResolvido:
    servidor: object
    usuario: object | None
    nome: str
    cpf: str
    email: str
    cargo: str
    unidade: str


def _snapshot_servidor(servidor) -> AssinanteResolvido:
    cargo = servidor.cargo.nome if getattr(servidor, "cargo_id", None) and servidor.cargo else ""
    unidade = ""
    if getattr(servidor, "unidade_id", None) and servidor.unidade:
        unidade = servidor.unidade.sigla or servidor.unidade.nome
    return AssinanteResolvido(
        servidor=servidor,
        usuario=None,
        nome=(servidor.nome or "").strip(),
        cpf=(servidor.cpf or "").strip(),
        email="",
        cargo=cargo,
        unidade=unidade,
    )


def resolver_assinante_para_artefato(artefato: DocumentoArtefato) -> AssinanteResolvido:
    tipo = (artefato.tipo or "").strip().lower()
    if tipo == DocumentoTipo.OFICIO.value:
        cfg = ConfiguracaoSistema.get_singleton()
        assinatura = (
            cfg.assinaturas.select_related("servidor", "servidor__cargo", "servidor__unidade")
            .filter(
                tipo=AssinaturaConfiguracao.TIPO_OFICIO,
                ordem=1,
                ativo=True,
                servidor__isnull=False,
            )
            .first()
        )
        if not assinatura or not assinatura.servidor_id:
            raise AssinanteNaoConfiguradoError(
                "Nenhum assinante de ofício configurado nas Configurações do Sistema."
            )
        return _snapshot_servidor(assinatura.servidor)

    raise AssinanteNaoConfiguradoError(
        f"Nenhum assinante configurado para o tipo de documento '{artefato.tipo}'."
    )
