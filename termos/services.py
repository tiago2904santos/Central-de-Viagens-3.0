from __future__ import annotations

import io
import zipfile

from cadastros.models import Servidor

from documentos.services.facade import build_default_facade
from documentos.services.facade import DocumentoGerado
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo

from oficios.documents import build_termo_payload
from oficios.models import Oficio


def preview_termo_context(
    oficio: Oficio,
    servidor: Servidor | None = None,
    *,
    modo_semipreenchido: bool = False,
    variante: str | None = None,
) -> dict:
    srv = servidor or oficio.servidores.order_by("nome").first()
    if srv is None:
        return {"erro": "Ofício sem servidores para montar o termo."}
    payload = build_termo_payload(
        oficio,
        srv,
        modo_semipreenchido=modo_semipreenchido,
        variante=variante,
    )
    return {"payload": payload, "variante_efetiva": payload["termo"]["variante"]}


def gerar_termo_um(
    oficio: Oficio,
    servidor: Servidor,
    formato: DocumentoFormato,
    *,
    modo_semipreenchido: bool = False,
    variante: str | None = None,
) -> DocumentoGerado:
    payload = build_termo_payload(
        oficio,
        servidor,
        modo_semipreenchido=modo_semipreenchido,
        variante=variante,
    )
    ref = f"{oficio.numero_formatado.replace('/', '-')}-termo-{servidor.pk}"
    facade = build_default_facade()
    # DOCX do termo segue placeholders aninhados ({{ oficio.* }}, {{ termo.participante.* }}).
    return facade.gerar(
        tipo=DocumentoTipo.TERMO_AUTORIZACAO,
        formato=formato,
        payload=payload,
        reference=ref,
    )


def gerar_termo_lote(oficio: Oficio, formato: DocumentoFormato) -> list[DocumentoGerado]:
    out: list[DocumentoGerado] = []
    for servidor in oficio.servidores.order_by("nome"):
        out.append(gerar_termo_um(oficio, servidor, formato))
    return out


def empacotar_termos_zip(documentos: list[DocumentoGerado]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in documentos:
            zf.writestr(doc.nome_arquivo, doc.conteudo)
    return buf.getvalue()
