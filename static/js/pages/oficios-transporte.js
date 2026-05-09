(function () {
  function normalizePlate(value) {
    return String(value || "")
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, "");
  }

  function debounce(fn, ms) {
    let handle = null;
    return function debounced() {
      const args = arguments;
      window.clearTimeout(handle);
      handle = window.setTimeout(function () {
        fn.apply(null, args);
      }, ms);
    };
  }

  function dispatchFieldEvents(element) {
    if (!element) return;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function OficioTransporte(root) {
    this.root = root;
    this.apiUrl = root.dataset.apiViaturaUrl || "";
    this.placaInput = root.querySelector("[data-oficio-placa]");
    this.viaturaInput = root.querySelector("[data-oficio-viatura-id]");
    this.modeloInput = root.querySelector("[data-oficio-viatura-modelo]");
    this.combustivelSelect = root.querySelector("[data-oficio-viatura-combustivel]");
    this.tipoSelect = root.querySelector("[data-oficio-viatura-tipo]");
    this.foundBanner = root.querySelector("[data-oficio-viatura-found]");
    this.modHidden = root.querySelector("[data-oficio-motorista-modo]");
    this.servidorPanel = root.querySelector("[data-oficio-motorista-servidor]");
    this.manualPanel = root.querySelector("[data-oficio-motorista-manual]");
    this.bindPlaca();
    this.bindMotoristaModoButtons();
    this.applyInitialMotoristaModo();
    this.syncViaturaLockFromDom();
  }

  OficioTransporte.prototype.bindMotoristaModoButtons = function () {
    const self = this;
    this.root.querySelectorAll("[data-oficio-motorista-modo-set]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const next = btn.getAttribute("data-oficio-motorista-modo-set") || "SERVIDOR";
        if (self.modHidden) {
          self.modHidden.value = next;
          dispatchFieldEvents(self.modHidden);
        }
        self.toggleMotoristaModo(next, false);
      });
    });
  };

  OficioTransporte.prototype.applyInitialMotoristaModo = function () {
    const initial = this.root.dataset.oficioMotoristaModInicial || "SERVIDOR";
    const current = (this.modHidden && this.modHidden.value) || initial;
    this.toggleMotoristaModo(current, true);
  };

  OficioTransporte.prototype.toggleMotoristaModo = function (modo, isInitial) {
    const manual = modo === "MANUAL";
    const motoristaSelect = this.root.querySelector("select[name='motorista']");
    if (!isInitial) {
      if (manual) {
        if (motoristaSelect) {
          motoristaSelect.value = "";
          dispatchFieldEvents(motoristaSelect);
        }
      } else if (this.manualPanel) {
        this.manualPanel.querySelectorAll("input, textarea").forEach(function (field) {
          if (field.type === "hidden") return;
          field.value = "";
          dispatchFieldEvents(field);
        });
      }
    }
    if (this.servidorPanel) {
      this.servidorPanel.classList.toggle("form-field--hidden", manual);
      this.servidorPanel.setAttribute("aria-hidden", manual ? "true" : "false");
    }
    if (this.manualPanel) {
      this.manualPanel.classList.toggle("form-field--hidden", !manual);
      this.manualPanel.setAttribute("aria-hidden", !manual ? "true" : "false");
    }
    if (motoristaSelect) {
      motoristaSelect.disabled = manual;
    }
  };

  OficioTransporte.prototype.setViaturaLocked = function (locked) {
    [this.modeloInput, this.combustivelSelect, this.tipoSelect].forEach(function (el) {
      if (!el) return;
      el.readOnly = !!(locked && el.tagName === "INPUT");
      el.disabled = !!(locked && el.tagName === "SELECT");
      el.classList.toggle("is-viatura-cadastro", !!locked);
    });
    if (this.foundBanner) {
      this.foundBanner.hidden = !locked;
      this.foundBanner.classList.toggle("form-field--hidden", !locked);
    }
  };

  OficioTransporte.prototype.syncViaturaLockFromDom = function () {
    const id = this.viaturaInput && this.viaturaInput.value;
    if (id) {
      this.setViaturaLocked(true);
    }
  };

  OficioTransporte.prototype.bindPlaca = function () {
    const self = this;
    if (!this.placaInput || !this.apiUrl) return;
    const runLookup = debounce(function () {
      self.lookupPlate();
    }, 420);
    this.placaInput.addEventListener("input", runLookup);
    this.placaInput.addEventListener("change", runLookup);
  };

  OficioTransporte.prototype.lookupPlate = function () {
    const self = this;
    const normalized = normalizePlate(this.placaInput.value);
    if (normalized.length !== 7) {
      if (this.viaturaInput) this.viaturaInput.value = "";
      dispatchFieldEvents(this.viaturaInput);
      this.setViaturaLocked(false);
      return;
    }
    const url = `${this.apiUrl}?placa=${encodeURIComponent(normalized)}`;
    window
      .fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (!data || !data.found) {
          if (self.viaturaInput) self.viaturaInput.value = "";
          dispatchFieldEvents(self.viaturaInput);
          self.setViaturaLocked(false);
          return;
        }
        if (self.viaturaInput) {
          self.viaturaInput.value = String(data.id);
          dispatchFieldEvents(self.viaturaInput);
        }
        if (self.modeloInput) {
          self.modeloInput.value = data.modelo || "";
          dispatchFieldEvents(self.modeloInput);
        }
        if (self.combustivelSelect && data.combustivel_id) {
          self.combustivelSelect.value = String(data.combustivel_id);
          dispatchFieldEvents(self.combustivelSelect);
        }
        if (self.tipoSelect && data.tipo) {
          self.tipoSelect.value = data.tipo;
          dispatchFieldEvents(self.tipoSelect);
        }
        self.setViaturaLocked(true);
      })
      .catch(function () {
        if (self.viaturaInput) self.viaturaInput.value = "";
        dispatchFieldEvents(self.viaturaInput);
        self.setViaturaLocked(false);
      });
  };

  function boot() {
    const root = document.getElementById("oficio-transporte-root");
    if (!root) return;
    new OficioTransporte(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
