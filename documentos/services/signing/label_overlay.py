"""Desenha a etiqueta institucional no PDF (conteúdo vetorial) antes da assinatura criptográfica."""

from __future__ import annotations

import io
import logging
from typing import Any

from pypdf import PdfReader
from pypdf import PdfWriter

from documentos.services.signing.position import SignaturePositionNormalizada

logger = logging.getLogger(__name__)


def _page_dimensions_pt(page) -> tuple[float, float]:
    mb = page.mediabox
    return float(mb.width), float(mb.height)


def _build_label_overlay_pdf(
    width_pt: float,
    height_pt: float,
    pos: SignaturePositionNormalizada,
    *,
    signer_name: str,
    verification_url: str,
    code_short: str,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width_pt, height_pt))

    llx = pos.box_x * width_pt
    lly = (1.0 - pos.box_y - pos.box_h) * height_pt
    ww = pos.box_w * width_pt
    hh = pos.box_h * height_pt

    pad = min(ww, hh) * 0.06
    inner_w = ww - 2 * pad
    inner_h = hh - 2 * pad

    c.setFillColor(colors.HexColor("#0b2b4a"))
    c.setStrokeColor(colors.HexColor("#1a4a7a"))
    c.setLineWidth(0.5)
    path = c.beginPath()
    r = min(3.5, ww * 0.04)
    path.roundRect(llx, lly, ww, hh, r)
    c.drawPath(path, fill=1, stroke=1)

    c.setFillColor(colors.white)
    title = "DOCUMENTO ASSINADO ELETRONICAMENTE"
    fs_title = max(6.0, min(9.0, hh * 0.11))
    fs_body = max(5.0, min(7.5, hh * 0.095))
    fs_meta = max(4.5, min(6.5, hh * 0.082))
    c.setFont("Helvetica-Bold", fs_title)
    c.drawString(llx + pad, lly + hh - pad - fs_title - 1, title)

    c.setFont("Helvetica", fs_body)
    name = (signer_name or "—")[:64]
    c.drawString(llx + pad, lly + hh - pad - fs_title - fs_body - 4, name)

    meta = f"Verifique em: {verification_url[:90]}{'…' if len(verification_url) > 90 else ''}"
    c.setFont("Helvetica", fs_meta)
    c.drawString(llx + pad, lly + pad + fs_meta + 6, meta)

    code = f"Código: {code_short}"
    c.drawString(llx + pad, lly + pad, code)

    qr_size = min(inner_h - 18, inner_w * 0.28, 52)
    if pos.qr and qr_size > 14:
        try:
            import qrcode
            from reportlab.lib.utils import ImageReader

            qr = qrcode.QRCode(version=None, box_size=2, border=0)
            qr.add_data(verification_url[:2048])
            qr.make(fit=True)
            pil = qr.make_image(fill_color="black", back_color="white")
            bio = io.BytesIO()
            pil.save(bio, format="PNG")
            bio.seek(0)
            qx = llx + ww - pad - qr_size
            qy = lly + pad
            c.drawImage(ImageReader(bio), qx, qy, width=qr_size, height=qr_size, mask="auto")
        except Exception:
            logger.debug("QR da etiqueta omitido (dependência ou dados).", exc_info=True)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def aplicar_etiqueta_assinatura_pdf(
    pdf_bytes: bytes,
    pos: SignaturePositionNormalizada,
    *,
    signer_name: str,
    verification_url: str,
    code_short: str,
) -> tuple[bytes, dict[str, Any]]:
    """
    Incorpora a etiqueta como conteúdo gráfico na página indicada.
    Retorna PDF em bytes e metadados para auditoria.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    n = len(reader.pages)
    if n == 0:
        return pdf_bytes, {"stamp": "skipped", "reason": "no_pages"}
    idx = max(0, min(n - 1, pos.page_index))
    page = reader.pages[idx]
    w_pt, h_pt = _page_dimensions_pt(page)
    overlay_pdf = _build_label_overlay_pdf(
        w_pt,
        h_pt,
        pos,
        signer_name=signer_name,
        verification_url=verification_url,
        code_short=code_short,
    )
    overlay_reader = PdfReader(io.BytesIO(overlay_pdf))
    overlay_page = overlay_reader.pages[0]
    page.merge_page(overlay_page)

    writer = PdfWriter()
    for i, p in enumerate(reader.pages):
        writer.add_page(p)
    out = io.BytesIO()
    writer.write(out)
    merged = out.getvalue()
    meta = {
        "stamp": "label_overlay",
        "signature_position": pos.to_audit_dict(),
    }
    return merged, meta
