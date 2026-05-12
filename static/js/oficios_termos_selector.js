(function () {
  function optionInfo(option) {
    return {
      cargo: option.dataset.cargo || "",
      cpf: option.dataset.cpf || "",
      label: (option.textContent || "").trim(),
      meta: option.dataset.meta || option.dataset.unidade || "",
      value: option.value,
    };
  }

  function selectedValues(select) {
    return new Set(Array.from(select.selectedOptions).map((option) => option.value));
  }

  function syncTarget(target, checkedValues) {
    Array.from(target.options).forEach((option) => {
      option.selected = checkedValues.has(option.value);
    });
    target.dispatchEvent(new Event("input", { bubbles: true }));
    target.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function init(root) {
    const source = document.querySelector("select[name='servidores']");
    const target = root.querySelector("select[name='servidores_termo_autorizacao']");
    const list = root.querySelector("[data-oficio-termos-list]");
    const empty = root.querySelector("[data-oficio-termos-empty]");
    if (!source || !target || !list || !empty) return;

    target.classList.add("app-termos-selector__native");

    const knownSelected = new Set(Array.from(source.selectedOptions).map((option) => option.value));
    let checkedValues = selectedValues(target);

    function render() {
      const sourceSelected = Array.from(source.selectedOptions).filter((option) => option.value);
      const sourceValues = new Set(sourceSelected.map((option) => option.value));

      sourceSelected.forEach((option) => {
        if (!knownSelected.has(option.value)) {
          checkedValues.add(option.value);
          knownSelected.add(option.value);
        }
      });

      checkedValues = new Set(Array.from(checkedValues).filter((value) => sourceValues.has(value)));
      syncTarget(target, checkedValues);

      list.innerHTML = "";
      sourceSelected.forEach((option) => {
        const item = optionInfo(option);
        const id = `termo-servidor-${item.value}`;
        const row = document.createElement("label");
        row.className = "oficio-termos-selector__item";
        row.setAttribute("for", id);

        const input = document.createElement("input");
        input.id = id;
        input.type = "checkbox";
        input.className = "oficio-termos-selector__checkbox";
        input.checked = checkedValues.has(item.value);
        input.addEventListener("change", () => {
          if (input.checked) checkedValues.add(item.value);
          else checkedValues.delete(item.value);
          syncTarget(target, checkedValues);
        });

        const copy = document.createElement("span");
        copy.className = "oficio-termos-selector__copy";

        const name = document.createElement("strong");
        name.className = "oficio-termos-selector__name";
        name.textContent = item.label;

        const meta = document.createElement("span");
        meta.className = "oficio-termos-selector__meta";
        meta.textContent = [item.cargo, item.cpf || item.meta].filter(Boolean).join(" - ") || "Dados complementares nao informados";

        const action = document.createElement("span");
        action.className = "oficio-termos-selector__action";
        action.textContent = "Gerar termo";

        copy.appendChild(name);
        copy.appendChild(meta);
        row.appendChild(input);
        row.appendChild(copy);
        row.appendChild(action);
        list.appendChild(row);
      });

      empty.hidden = sourceSelected.length > 0;
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
