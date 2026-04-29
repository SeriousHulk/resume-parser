const allowedExtensions = [".pdf", ".docx", ".doc"];

const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#file-input");
const fileName = document.querySelector("#file-name");
const providerSelect = document.querySelector("#provider-select");
const modelSelect = document.querySelector("#model-select");
const parseButton = document.querySelector("#parse-button");
const statusText = document.querySelector("#status");
const jsonOutput = document.querySelector("#json-output");

let selectedFile = null;
let providers = [];

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.classList.toggle("is-error", isError);
}

function extensionOf(name) {
  const index = name.lastIndexOf(".");
  return index === -1 ? "" : name.slice(index).toLowerCase();
}

function setSelectedFile(file) {
  const extension = extensionOf(file.name);
  if (!allowedExtensions.includes(extension)) {
    selectedFile = null;
    fileInput.value = "";
    dropZone.classList.remove("has-file");
    dropZone.classList.add("is-invalid");
    fileName.textContent = "Unsupported file. Use PDF, DOCX, or DOC.";
    setStatus("Unsupported file type. Please choose a PDF, DOCX, or DOC file.", true);
    return;
  }

  selectedFile = file;
  dropZone.classList.remove("is-invalid");
  dropZone.classList.add("has-file");
  fileName.textContent = file.name;
  setStatus("");
}

function updateModelOptions() {
  const selectedProvider = providers.find((provider) => provider.id === providerSelect.value);
  modelSelect.innerHTML = "";

  if (!selectedProvider || !selectedProvider.available) {
    modelSelect.disabled = true;
    return;
  }

  modelSelect.disabled = false;
  for (const model of selectedProvider.models) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    modelSelect.appendChild(option);
  }
}

async function loadModels() {
  const response = await fetch("/api/models");
  const payload = await response.json();
  providers = payload.providers;
  providerSelect.innerHTML = "";

  for (const provider of providers) {
    const option = document.createElement("option");
    option.value = provider.id;
    option.textContent = provider.available ? provider.label : `${provider.label} (unavailable)`;
    option.disabled = !provider.available;
    providerSelect.appendChild(option);
  }

  updateModelOptions();
}

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragover");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragover");
  const file = event.dataTransfer.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

providerSelect.addEventListener("change", updateModelOptions);

parseButton.addEventListener("click", async () => {
  if (!selectedFile) {
    setStatus("Choose a resume file first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("provider", providerSelect.value);
  formData.append("model", modelSelect.value);

  parseButton.disabled = true;
  setStatus("Parsing resume...");

  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Resume parsing failed.");
    }

    jsonOutput.textContent = JSON.stringify(payload.data, null, 2);
    setStatus("Parsed successfully.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    parseButton.disabled = false;
  }
});

loadModels().catch((error) => {
  setStatus(error.message, true);
});
