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

  /**
   * NUMERO/ANO — só dígitos contam como número do ofício (até 3).
   * Com "/" no valor, usa apenas o trecho antes da barra (evita misturar com o ano fixo).
   * Sem "/", remove sufixo numérico igual ao ano quando o usuário cola "022026".
   */
  function maskOficioMotoristaValue(input) {
    const yearFinal = resolveOficioMotoristaYear(input);
    const yStr = String(yearFinal);
    const raw = String(input.value ?? "");
    const slashIdx = raw.indexOf("/");
    let officeDigits = "";
    if (slashIdx !== -1) {
      officeDigits = onlyDigits(raw.slice(0, slashIdx)).slice(0, 3);
    } else {
      let all = onlyDigits(raw);
      if (all.length >= 4 && all.slice(-4) === yStr) {
        all = all.slice(0, -4);
      }
      officeDigits = all.slice(0, 3);
    }
    if (!officeDigits) {
      return "";
    }
    return `${officeDigits}/${yearFinal}`;
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
      const next = maskOficioMotoristaValue(input);
      if (input.value !== next) {
        input.value = next;
        dispatchMaskEvents(input);
      }
    }
  }

  function initMasks() {
    document.querySelectorAll("input[data-mask]").forEach((input) => {
      applyMask(input);
      if (input.dataset.mask === "oficio_motorista") {
        input.addEventListener("input", () => applyMask(input));
        input.addEventListener("blur", () => applyMask(input));
      } else {
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
