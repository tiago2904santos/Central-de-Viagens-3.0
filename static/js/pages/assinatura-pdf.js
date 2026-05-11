/**
 * Editor de assinatura: PDF.js + etiqueta arrastável (coordenadas normalizadas 0–1, origem topo-esquerdo da página).
 * Depende de `window.pdfjsLib` (pdf.min.js carregado antes deste módulo).
 */

const BASE_SCALE = 1.22;
const ZOOM_MIN = 0.75;
const ZOOM_MAX = 2.1;
const ZOOM_STEP = 0.12;

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function qs(root, sel) {
  return root ? root.querySelector(sel) : null;
}

function readFloatInput(el, fallback) {
  if (!el) return fallback;
  const v = parseFloat(String(el.value).replace(",", "."));
  return Number.isFinite(v) ? v : fallback;
}

function buildLabelHtml(signer, url, code) {
  const safe = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  const u = safe(url);
  const shortUrl = u.length > 72 ? u.slice(0, 70) + "…" : u;
  return (
    '<div class="assinatura-label assinatura-label--draggable" tabindex="0" role="group" aria-label="Posição da assinatura eletrónica">' +
    '<div class="assinatura-label__logo" aria-hidden="true">PCPR</div>' +
    '<div class="assinatura-label__body">' +
    '<div class="assinatura-label__title">DOCUMENTO ASSINADO ELETRONICAMENTE</div>' +
    '<div class="assinatura-label__name">' +
    safe(signer || "—") +
    "</div>" +
    '<div class="assinatura-label__meta">Verifique em: ' +
    shortUrl +
    "</div>" +
    '<div class="assinatura-label__code">Código: ' +
    safe(code || "—") +
    "</div>" +
    "</div>" +
    "</div>"
  );
}

function initEditor(root) {
  const pdfjsLib = window.pdfjsLib;
  const pdfUrl = root.dataset.pdfUrl || "";
  const workerSrc = root.dataset.workerSrc || "";
  const signer = root.dataset.signerName || "";
  const verUrl = root.dataset.verificationUrl || "";
  const verCode = root.dataset.verificationCode || "";
  const pagesCol = qs(root, "#assinatura-pages-column");
  const scroller = qs(root, "#assinatura-editor-scroll");
  const metaEl = qs(root, "#assinatura-pdf-meta");
  const errEl = document.getElementById("assinatura-pdf-error");
  const form = document.getElementById("form-assinar-oficio");
  const inpX = form ? form.querySelector('[name="sig_x"]') : null;
  const inpY = form ? form.querySelector('[name="sig_y"]') : null;
  const inpW = form ? form.querySelector('[name="sig_w"]') : null;
  const inpH = form ? form.querySelector('[name="sig_h"]') : null;
  const inpPg = form ? form.querySelector('[name="sig_page"]') : null;

  function showErr(msg) {
    if (errEl) {
      errEl.textContent = msg;
      errEl.hidden = false;
    }
  }

  if (!pdfjsLib || !pdfUrl || !pagesCol || !form) return;

  if (workerSrc) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;
  }

  let pdfDoc = null;
  let zoom = 1;
  let pageWraps = [];
  let labelWrap = null;
  let labelEl = null;
  let drag = null;

  function readNorm() {
    return {
      x: readFloatInput(inpX, 0.58),
      y: readFloatInput(inpY, 0.78),
      w: readFloatInput(inpW, 0.34),
      h: readFloatInput(inpH, 0.11),
      page: parseInt(String(inpPg && inpPg.value !== "" ? inpPg.value : "-1"), 10),
    };
  }

  function writeNorm(n) {
    if (inpX) inpX.value = String(clamp(n.x, 0, 1).toFixed(4));
    if (inpY) inpY.value = String(clamp(n.y, 0, 1).toFixed(4));
    if (inpW) inpW.value = String(clamp(n.w, 0.2, 0.95).toFixed(4));
    if (inpH) inpH.value = String(clamp(n.h, 0.06, 0.22).toFixed(4));
    const last = pdfDoc ? pdfDoc.numPages - 1 : 0;
    let pg = Number.isFinite(n.page) ? n.page : -1;
    if (pg === -1) pg = last;
    pg = clamp(pg, 0, last);
    if (inpPg) inpPg.value = String(pg);
  }

  function labelPageIndex() {
    const n = pdfDoc ? pdfDoc.numPages : 1;
    const raw = inpPg && inpPg.value !== "" ? inpPg.value : "-1";
    let p = parseInt(String(raw), 10);
    if (!Number.isFinite(p) || p === -1) return n - 1;
    return clamp(p, 0, n - 1);
  }

  function applyLabelPosition() {
    if (!labelEl || !labelWrap) return;
    const n = readNorm();
    const pw = labelWrap.clientWidth;
    const ph = labelWrap.clientHeight;
    if (!pw || !ph) return;
    labelEl.style.left = n.x * 100 + "%";
    labelEl.style.top = n.y * 100 + "%";
    labelEl.style.width = n.w * 100 + "%";
    labelEl.style.height = n.h * 100 + "%";
  }

  function ensureLabelOnPage(idx) {
    const wrap = pageWraps[idx];
    if (!wrap || !labelEl) return;
    if (labelWrap !== wrap) {
      if (labelEl.parentNode) labelEl.parentNode.removeChild(labelEl);
      wrap.appendChild(labelEl);
      labelWrap = wrap;
    }
    applyLabelPosition();
  }

  function syncLabelToInputs() {
    const idx = labelPageIndex();
    ensureLabelOnPage(idx);
    applyLabelPosition();
  }

  function startDrag(ev) {
    if (!labelEl || !labelWrap) return;
    ev.preventDefault();
    const r = labelWrap.getBoundingClientRect();
    const lr = labelEl.getBoundingClientRect();
    drag = {
      sx: ev.clientX,
      sy: ev.clientY,
      sl: lr.left - r.left,
      st: lr.top - r.top,
      rw: r.width,
      rh: r.height,
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  function onMove(ev) {
    if (!drag || !labelWrap || !labelEl) return;
    const dx = ev.clientX - drag.sx;
    const dy = ev.clientY - drag.sy;
    let nl = drag.sl + dx;
    let nt = drag.st + dy;
    const lw = labelEl.offsetWidth;
    const lh = labelEl.offsetHeight;
    nl = clamp(nl, 0, drag.rw - lw);
    nt = clamp(nt, 0, drag.rh - lh);
    labelEl.style.left = (nl / drag.rw) * 100 + "%";
    labelEl.style.top = (nt / drag.rh) * 100 + "%";
  }

  function onUp() {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
    if (!labelEl || !labelWrap || !pdfDoc) {
      drag = null;
      return;
    }
    const rw = labelWrap.clientWidth;
    const rh = labelWrap.clientHeight;
    const nx = labelEl.offsetLeft / rw;
    const ny = labelEl.offsetTop / rh;
    const nw = labelEl.offsetWidth / rw;
    const nh = labelEl.offsetHeight / rh;
    const idx = pageWraps.indexOf(labelWrap);
    writeNorm({ x: nx, y: ny, w: nw, h: nh, page: idx >= 0 ? idx : labelPageIndex() });
    drag = null;
  }

  async function renderAll() {
    if (!pdfDoc) return;
    pagesCol.innerHTML = "";
    pageWraps = [];
    labelWrap = null;
    const n = pdfDoc.numPages;
    const scale = BASE_SCALE * zoom;
    for (let i = 1; i <= n; i += 1) {
      const page = await pdfDoc.getPage(i);
      const wrap = document.createElement("div");
      wrap.className = "assinatura-page-wrap";
      wrap.dataset.pageNum = String(i);
      const canvas = document.createElement("canvas");
      const vp = page.getViewport({ scale: scale });
      canvas.width = vp.width;
      canvas.height = vp.height;
      canvas.style.width = vp.width + "px";
      canvas.style.height = vp.height + "px";
      canvas.className = "assinatura-page-canvas";
      wrap.appendChild(canvas);
      pagesCol.appendChild(wrap);
      pageWraps.push(wrap);
      await page.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;
    }
    const idx = labelPageIndex();
    if (!labelEl) {
      const tmp = document.createElement("div");
      tmp.innerHTML = buildLabelHtml(signer, verUrl, verCode).trim();
      labelEl = tmp.firstElementChild;
      labelEl.addEventListener("mousedown", startDrag);
    }
    labelWrap = pageWraps[idx];
    if (labelWrap) {
      labelWrap.appendChild(labelEl);
    }
    syncLabelToInputs();
    if (metaEl) metaEl.textContent = "Documento — " + n + " página" + (n > 1 ? "s" : "");
  }

  let resizeT = null;
  function onResize() {
    clearTimeout(resizeT);
    resizeT = setTimeout(function () {
      renderAll().catch(function () {});
    }, 200);
  }

  pdfjsLib
    .getDocument({ url: pdfUrl, withCredentials: false })
    .promise.then(function (doc) {
      pdfDoc = doc;
      return renderAll();
    })
    .catch(function () {
      showErr("Não foi possível carregar o PDF. Tente abrir em nova aba ou verifique a sessão.");
    });

  const zIn = document.getElementById("assinatura-zoom-in");
  const zOut = document.getElementById("assinatura-zoom-out");
  const zReset = document.getElementById("assinatura-zoom-reset");
  if (zIn)
    zIn.addEventListener("click", function () {
      zoom = clamp(zoom + ZOOM_STEP, ZOOM_MIN, ZOOM_MAX);
      renderAll().catch(function () {});
    });
  if (zOut)
    zOut.addEventListener("click", function () {
      zoom = clamp(zoom - ZOOM_STEP, ZOOM_MIN, ZOOM_MAX);
      renderAll().catch(function () {});
    });
  if (zReset)
    zReset.addEventListener("click", function () {
      zoom = 1;
      renderAll().catch(function () {});
    });

  window.addEventListener("resize", onResize);

  if (scroller) {
    scroller.addEventListener("scroll", function () {
      if (!pdfDoc || !pageWraps.length) return;
      const mid = scroller.scrollTop + scroller.clientHeight * 0.35;
      let best = 0;
      for (let i = 0; i < pageWraps.length; i += 1) {
        const top = pageWraps[i].offsetTop;
        if (top <= mid) best = i;
      }
      if (metaEl) metaEl.textContent = "Página " + (best + 1) + " / " + pdfDoc.numPages;
    });
  }
}

const root = document.getElementById("assinatura-pdf-editor");
if (root) {
  initEditor(root);
}
