(function () {
  function onModeloMotivoChange(select) {
    const form = select.closest("form");
    if (!form) return;
    const motivo = form.querySelector("[data-motivo-textarea='true']");
    if (!motivo || (motivo.value || "").trim()) return;
    const selected = select.options[select.selectedIndex];
    if (!selected) return;
    const texto = selected.dataset.textoMotivo || "";
    if (texto.trim()) {
      motivo.value = texto;
    }
  }

  function initModeloMotivo() {
    const select = document.querySelector("[data-modelo-motivo-select='true']");
    if (!select) return;
    select.addEventListener("change", function () {
      onModeloMotivoChange(select);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initModeloMotivo);
  } else {
    initModeloMotivo();
  }
})();
