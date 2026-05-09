(function () {
  const SELECTOR = "select[data-app-multiselect]";

  function normalize(value) {
    return (value || "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function dispatchNativeEvents(select) {
    select.dispatchEvent(new Event("input", { bubbles: true }));
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function optionData(option) {
    return {
      disabled: option.disabled,
      label: (option.textContent || "").trim(),
      selected: option.selected,
      value: option.value,
    };
  }

  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function initMultiselect(select) {
    if (!select || select.dataset.appMultiselectReady === "true") return;
    select.dataset.appMultiselectReady = "true";

    const options = Array.from(select.options).map(optionData).filter((item) => item.value !== "");
    const placeholder = select.dataset.placeholder || "Selecione";
    const searchPlaceholder = select.dataset.searchPlaceholder || "Pesquisar";
    const emptyMessage = select.dataset.emptyMessage || "Nenhum resultado encontrado.";
    const listboxId = `${select.id || select.name || "app-multiselect"}-listbox`;
    let query = "";
    let activeIndex = -1;
    let isOpen = false;

    select.classList.add("app-multiselect__native");

    const root = createElement("div", "app-multiselect");
    const control = createElement("div", "app-multiselect__control");
    const chips = createElement("div", "app-multiselect__chips");
    const search = createElement("input", "app-multiselect__search");
    const indicator = createElement("span", "app-multiselect__indicator", "v");
    const dropdown = createElement("div", "app-multiselect__dropdown");
    const listbox = createElement("div", "app-multiselect__listbox");
    const empty = createElement("div", "app-multiselect__empty", emptyMessage);
    const count = createElement("div", "app-multiselect__count");

    control.setAttribute("role", "combobox");
    control.setAttribute("aria-expanded", "false");
    control.setAttribute("aria-controls", listboxId);
    control.setAttribute("aria-haspopup", "listbox");
    listbox.id = listboxId;
    listbox.setAttribute("role", "listbox");
    listbox.setAttribute("aria-multiselectable", "true");
    search.type = "search";
    search.placeholder = placeholder;
    search.autocomplete = "off";
    search.setAttribute("aria-label", searchPlaceholder);
    search.disabled = select.disabled;

    control.appendChild(chips);
    control.appendChild(search);
    control.appendChild(indicator);
    dropdown.appendChild(listbox);
    dropdown.appendChild(empty);
    dropdown.appendChild(count);
    root.appendChild(control);
    root.appendChild(dropdown);
    select.insertAdjacentElement("afterend", root);

    function selectedValues() {
      return options.filter((item) => item.selected).map((item) => item.value);
    }

    function filteredOptions() {
      const normalizedQuery = normalize(query);
      return options.filter((item) => !normalizedQuery || normalize(item.label).includes(normalizedQuery));
    }

    function syncSelect(shouldDispatch) {
      const values = new Set(selectedValues());
      Array.from(select.options).forEach((option) => {
        option.selected = values.has(option.value);
      });
      if (shouldDispatch) dispatchNativeEvents(select);
    }

    function setOpen(nextOpen) {
      if (select.disabled) return;
      isOpen = nextOpen;
      root.classList.toggle("app-multiselect--open", isOpen);
      control.setAttribute("aria-expanded", isOpen ? "true" : "false");
      if (isOpen) {
        search.placeholder = searchPlaceholder;
      } else {
        query = "";
        search.value = "";
        activeIndex = -1;
        search.placeholder = selectedValues().length ? "" : placeholder;
      }
      renderOptions();
    }

    function toggleValue(value) {
      const item = options.find((candidate) => candidate.value === value);
      if (!item || item.disabled) return;
      item.selected = !item.selected;
      syncSelect(true);
      query = "";
      search.value = "";
      activeIndex = -1;
      render();
      search.focus();
      setOpen(true);
    }

    function removeValue(value) {
      const item = options.find((candidate) => candidate.value === value);
      if (!item || item.disabled || !item.selected) return;
      item.selected = false;
      syncSelect(true);
      render();
      search.focus();
    }

    function renderChips() {
      chips.innerHTML = "";
      const selected = options.filter((item) => item.selected);
      selected.forEach((item) => {
        const chip = createElement("span", "app-multiselect__chip");
        const label = createElement("span", "app-multiselect__chip-label", item.label);
        const remove = createElement("button", "app-multiselect__chip-remove", "x");
        remove.type = "button";
        remove.setAttribute("aria-label", `Remover ${item.label}`);
        remove.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          removeValue(item.value);
        });
        chip.appendChild(label);
        chip.appendChild(remove);
        chips.appendChild(chip);
      });
      root.classList.toggle("app-multiselect--empty", selected.length === 0);
      search.placeholder = selected.length || isOpen ? searchPlaceholder : placeholder;
    }

    function renderOptions() {
      const visibleOptions = filteredOptions();
      listbox.innerHTML = "";
      empty.hidden = visibleOptions.length > 0;
      count.hidden = options.filter((item) => item.selected).length < 2;
      count.textContent = `${options.filter((item) => item.selected).length} selecionados`;
      if (activeIndex >= visibleOptions.length) activeIndex = visibleOptions.length - 1;

      visibleOptions.forEach((item, index) => {
        const option = createElement("button", "app-multiselect__option");
        const marker = createElement("span", "app-multiselect__option-marker");
        const label = createElement("span", "app-multiselect__option-label", item.label);
        option.type = "button";
        option.dataset.value = item.value;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", item.selected ? "true" : "false");
        option.disabled = item.disabled;
        option.classList.toggle("app-multiselect__option--selected", item.selected);
        option.classList.toggle("app-multiselect__option--active", index === activeIndex);
        option.appendChild(marker);
        option.appendChild(label);
        option.addEventListener("mousedown", (event) => event.preventDefault());
        option.addEventListener("click", () => toggleValue(item.value));
        listbox.appendChild(option);
      });
    }

    function render() {
      renderChips();
      renderOptions();
    }

    control.addEventListener("click", () => {
      setOpen(true);
      search.focus();
    });

    search.addEventListener("focus", () => setOpen(true));
    search.addEventListener("input", () => {
      query = search.value;
      activeIndex = 0;
      setOpen(true);
      renderOptions();
    });
    search.addEventListener("keydown", (event) => {
      const visibleOptions = filteredOptions().filter((item) => !item.disabled);
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const item = visibleOptions[Math.max(activeIndex, 0)];
        if (item) toggleValue(item.value);
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        activeIndex = Math.min(activeIndex + 1, visibleOptions.length - 1);
        renderOptions();
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        renderOptions();
        return;
      }
      if (event.key === "Backspace" && !search.value) {
        const selected = options.filter((item) => item.selected);
        const last = selected[selected.length - 1];
        if (last) removeValue(last.value);
      }
    });

    document.addEventListener("click", (event) => {
      if (!root.contains(event.target) && event.target !== select) setOpen(false);
    });

    select.addEventListener("change", () => {
      const selected = new Set(Array.from(select.selectedOptions).map((option) => option.value));
      options.forEach((item) => {
        item.selected = selected.has(item.value);
      });
      render();
    });

    syncSelect(false);
    render();
    setOpen(false);
  }

  function boot() {
    document.querySelectorAll(SELECTOR).forEach(initMultiselect);
  }

  window.AppMultiselect = { boot };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
