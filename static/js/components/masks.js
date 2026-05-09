(function () {
  function onlyDigits(value) {
    return (value || "").replace(/\D/g, "");
  }

  function onlyAlnum(value) {
    return (value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  }

  function maskCpf(value) {
    const v = onlyDigits(value).slice(0, 11);
    if (v.length <= 3) return v;
    if (v.length <= 6) return `${v.slice(0, 3)}.${v.slice(3)}`;
    if (v.length <= 9) return `${v.slice(0, 3)}.${v.slice(3, 6)}.${v.slice(6)}`;
    return `${v.slice(0, 3)}.${v.slice(3, 6)}.${v.slice(6, 9)}-${v.slice(9)}`;
  }

  function maskRg(value) {
    const v = onlyAlnum(value).slice(0, 9);
    if (v.length <= 2) return v;
    if (v.length <= 5) return `${v.slice(0, 2)}.${v.slice(2)}`;
    if (v.length <= 8) return `${v.slice(0, 2)}.${v.slice(2, 5)}.${v.slice(5)}`;
    return `${v.slice(0, 2)}.${v.slice(2, 5)}.${v.slice(5, 8)}-${v.slice(8)}`;
  }

  function maskPlaca(value) {
    return onlyAlnum(value).slice(0, 7);
  }

  function maskCep(value) {
    const v = onlyDigits(value).slice(0, 8);
    if (v.length <= 5) return v;
    return `${v.slice(0, 5)}-${v.slice(5)}`;
  }

  function maskProtocolo(value) {
    const v = onlyDigits(value).slice(0, 9);
    if (v.length <= 2) return v;
    if (v.length <= 5) return `${v.slice(0, 2)}.${v.slice(2)}`;
    if (v.length <= 8) return `${v.slice(0, 2)}.${v.slice(2, 5)}.${v.slice(5)}`;
    return `${v.slice(0, 2)}.${v.slice(2, 5)}.${v.slice(5, 8)}-${v.slice(8)}`;
  }

  function resolveOficioMotoristaYear(input) {
    const raw =
      input.dataset.oficioAno ||
      input.dataset.maskYear ||
      "";
    const y = parseInt(String(raw), 10);
    if (y >= 1900 && y <= 2100) {
      return y;
    }
    return new Date().getFullYear();
  }

  function setupOficioMotoristaMask(input) {
    const year = resolveOficioMotoristaYear(input);
    input.placeholder = `__/${year}`;
    if ((input.value || "").trim() !== "") {
      applyOficioMotoristaMask(input);
    }
  }

  function applyOficioMotoristaMask(input) {
    if (input.dataset.maskApplying === "1") {
      return;
    }
    input.dataset.maskApplying = "1";
    try {
      const year = resolveOficioMotoristaYear(input);
      const yearDigits = String(year);
      input.placeholder = `__/${year}`;

      let raw = String(input.value ?? "");

      let digitsBeforeSlash = "";

      if (raw.includes("/")) {
        digitsBeforeSlash = raw.split("/")[0].replace(/\D/g, "");
      } else {
        digitsBeforeSlash = raw.replace(/\D/g, "");

        if (digitsBeforeSlash.endsWith(yearDigits)) {
          digitsBeforeSlash = digitsBeforeSlash.slice(0, -yearDigits.length);
        }
      }

      const numero = digitsBeforeSlash.slice(0, 3);

      const next = numero ? `${numero}/${year}` : "";

      if (input.value !== next) {
        input.value = next;
        dispatchMaskEvents(input);
      }
    } finally {
      delete input.dataset.maskApplying;
    }
  }

  function maskTelefone(value) {
    const v = onlyDigits(value).slice(0, 11);
    if (!v) return "";
    if (v.length <= 2) return `(${v}`;
    if (v.length <= 6) return `(${v.slice(0, 2)}) ${v.slice(2)}`;
    if (v.length <= 10) return `(${v.slice(0, 2)}) ${v.slice(2, 6)}-${v.slice(6)}`;
    return `(${v.slice(0, 2)}) ${v.slice(2, 7)}-${v.slice(7)}`;
  }

  function maskUpper(value) {
    return (value || "").toUpperCase();
  }

  function dispatchMaskEvents(element) {
    if (!element) return;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function applyMask(input) {
    const mask = input.dataset.mask;
    if (mask === "upper") input.value = maskUpper(input.value);
    if (mask === "cpf") input.value = maskCpf(input.value);
    if (mask === "rg") input.value = maskRg(input.value);
    if (mask === "placa") input.value = maskPlaca(input.value);
    if (mask === "cep") input.value = maskCep(input.value);
    if (mask === "telefone") input.value = maskTelefone(input.value);
    if (mask === "protocolo") input.value = maskProtocolo(input.value);
    if (mask === "oficio_motorista") {
      applyOficioMotoristaMask(input);
    }
  }

  function initMasks() {
    document.querySelectorAll("input[data-mask]").forEach((input) => {
      if (input.dataset.mask === "oficio_motorista") {
        setupOficioMotoristaMask(input);
        input.addEventListener("input", () => applyOficioMotoristaMask(input));
        input.addEventListener("blur", () => applyOficioMotoristaMask(input));
      } else {
        applyMask(input);
        input.addEventListener("input", () => applyMask(input));
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMasks);
  } else {
    initMasks();
  }
})();
