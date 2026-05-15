document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-mention]");
  if (button) {
    const textarea = document.querySelector(".post-form textarea");
    if (!textarea) return;
    const mention = button.dataset.mention;
    const prefix = textarea.value && !textarea.value.endsWith(" ") ? " " : "";
    textarea.value = `${textarea.value}${prefix}${mention} `;
    textarea.focus();
    return;
  }

  const addButton = event.target.closest("[data-add-template-row]");
  if (addButton) {
    const kind = addButton.dataset.addTemplateRow;
    const container = document.querySelector(`[data-template-rows="${kind}"]`);
    const template = document.querySelector(`#${kind}-row-template`);
    if (!container || !template) return;
    const nextIndex = Date.now().toString();
    const html = template.innerHTML.replaceAll("__index__", nextIndex);
    container.insertAdjacentHTML("beforeend", html);
    return;
  }

  const removeButton = event.target.closest("[data-remove-row]");
  if (removeButton) {
    removeButton.closest("[data-row]")?.remove();
  }
});

document.addEventListener("change", (event) => {
  const autoSubmitField = event.target.closest("[data-auto-submit] input[type='checkbox']");
  if (autoSubmitField) {
    const form = autoSubmitField.closest("form");
    form?.requestSubmit();
    return;
  }

  const input = event.target.closest("[data-file-picker]");
  if (!input) return;

  const picker = input.closest(".file-picker");
  const count = picker?.querySelector("[data-file-picker-count]");
  if (!count) return;

  const fileCount = input.files ? input.files.length : 0;
  count.textContent = fileCount ? `已选择 ${fileCount} 张图片` : "未选择图片";
  picker.classList.toggle("has-files", fileCount > 0);
});
