(function () {
  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function optionInfo(option) {
    const metaParts = [option.dataset.cargo, option.dataset.rg, option.dataset.cpf].filter(Boolean);
    return {
      cargo: option.dataset.cargo || "",
      cpf: option.dataset.cpf || "",
      label: option.dataset.main || (option.textContent || "").trim(),
      meta: metaParts.length ? metaParts.join(" · ") : option.dataset.meta || option.dataset.unidade || "",
      value: option.value,
    };
  }

  function selectedValues(select) {
    return new Set(Array.from(select.selectedOptions).map((option) => option.value));
  }

  function syncTarget(target, selected) {
    Array.from(target.options).forEach((option) => {
      option.selected = selected.has(option.value);
    });
    target.dispatchEvent(new Event("input", { bubbles: true }));
    target.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function updateSummary(summary, withTerm, withoutTerm) {
    if (!summary) return;
    summary.textContent = `${withTerm} com termo · ${withoutTerm} sem termo`;
  }

  function renderOptionButton(item, selected, label, modifier, onClick) {
    const button = createElement(
      "button",
      `oficio-termos-selector__option oficio-termos-selector__option--${modifier}`,
      label,
    );
    button.type = "button";
    button.setAttribute("aria-pressed", selected ? "true" : "false");
    button.classList.toggle("oficio-termos-selector__option--active", selected);
    button.addEventListener("click", onClick);
    button.dataset.value = item.value;
    return button;
  }

  function init(root) {
    const source = document.querySelector("select[name='servidores']");
    const target = root.querySelector("select[name='servidores_termo_autorizacao']");
    const list = root.querySelector("[data-oficio-termos-list]");
    const empty = root.querySelector("[data-oficio-termos-empty]");
    const summary = root.querySelector("[data-oficio-termos-summary]");
    if (!source || !target || !list || !empty) return;

    target.classList.add("app-termos-selector__native");
    target.setAttribute("aria-hidden", "true");
    target.tabIndex = -1;

    const knownSelected = new Set(Array.from(source.selectedOptions).map((option) => option.value));
    let selectedForTerm = selectedValues(target);

    function setTermValue(value, enabled) {
      if (enabled) selectedForTerm.add(value);
      else selectedForTerm.delete(value);
      render();
    }

    function renderItem(option) {
      const item = optionInfo(option);
      const enabled = selectedForTerm.has(item.value);
      const card = createElement(
        "article",
        `oficio-termos-selector__item${enabled ? " oficio-termos-selector__item--active" : ""}`,
      );
      card.dataset.value = item.value;

      const identity = createElement("div", "oficio-termos-selector__identity");
      const name = createElement("strong", "oficio-termos-selector__name", item.label);
      const meta = createElement(
        "span",
        "oficio-termos-selector__meta",
        item.meta || "Dados complementares nao informados",
      );
      identity.appendChild(name);
      identity.appendChild(meta);

      const toggle = createElement("div", "oficio-termos-selector__toggle");
      toggle.setAttribute("aria-label", `Termo de Autorizacao para ${item.label}`);
      toggle.appendChild(
        renderOptionButton(item, !enabled, "Não gerar termo", "no", () => setTermValue(item.value, false)),
      );
      toggle.appendChild(
        renderOptionButton(item, enabled, "Gerar termo", "yes", () => setTermValue(item.value, true)),
      );

      card.appendChild(identity);
      card.appendChild(toggle);
      return card;
    }

    function render() {
      const selectedOptions = Array.from(source.selectedOptions).filter((option) => option.value);
      const sourceValues = new Set(selectedOptions.map((option) => option.value));

      selectedOptions.forEach((option) => {
        if (!knownSelected.has(option.value)) {
          selectedForTerm.add(option.value);
          knownSelected.add(option.value);
        }
      });

      selectedForTerm = new Set(Array.from(selectedForTerm).filter((value) => sourceValues.has(value)));
      syncTarget(target, selectedForTerm);

      list.innerHTML = "";
      selectedOptions.forEach((option) => list.appendChild(renderItem(option)));

      const withTerm = selectedForTerm.size;
      const withoutTerm = Math.max(selectedOptions.length - withTerm, 0);
      updateSummary(summary, withTerm, withoutTerm);
      empty.hidden = selectedOptions.length > 0;
      list.hidden = selectedOptions.length === 0;
    }

    source.addEventListener("change", render);
    render();
  }

  function boot() {
    document.querySelectorAll("[data-oficio-termos-selector]").forEach(init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
