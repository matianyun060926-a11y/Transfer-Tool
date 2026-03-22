const state = {
  sessionToken: window.localStorage.getItem("transfer_tool_session") || "",
  mobileName: window.localStorage.getItem("transfer_tool_mobile_name") || "",
  selectedFiles: [],
  device: null,
};

const sessionHeader = "X-Session-Token";

const els = {
  deviceName: document.querySelector("#device-name"),
  deviceStatus: document.querySelector("#device-status"),
  hostOrigin: document.querySelector("#host-origin"),
  mobileName: document.querySelector("#mobile-name"),
  pairingCode: document.querySelector("#pairing-code"),
  pairButton: document.querySelector("#pair-button"),
  pairMessage: document.querySelector("#pair-message"),
  sessionBadge: document.querySelector("#session-badge"),
  uploadInput: document.querySelector("#upload-input"),
  uploadSummary: document.querySelector("#upload-summary"),
  uploadButton: document.querySelector("#upload-button"),
  uploadState: document.querySelector("#upload-state"),
  uploadProgress: document.querySelector("#upload-progress"),
  uploadProgressLabel: document.querySelector("#upload-progress-label"),
  downloadsList: document.querySelector("#downloads-list"),
  historyList: document.querySelector("#history-list"),
  refreshDownloads: document.querySelector("#refresh-downloads"),
  refreshHistory: document.querySelector("#refresh-history"),
  downloadTemplate: document.querySelector("#download-template"),
  historyTemplate: document.querySelector("#history-template"),
};

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function setPill(element, text, variant) {
  element.textContent = text;
  element.className = `pill pill-${variant}`;
}

function setUploadProgress(percent) {
  const safePercent = Math.min(100, Math.max(0, percent));
  els.uploadProgress.style.width = `${safePercent}%`;
  els.uploadProgressLabel.textContent = `${Math.round(safePercent)}%`;
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.sessionToken) {
    headers.set(sessionHeader, state.sessionToken);
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.error || message;
    } catch (error) {
      /* ignore parse errors */
    }
    throw new Error(message);
  }
  return response;
}

async function loadDeviceInfo() {
  const response = await fetch("/api/device");
  const payload = await response.json();
  state.device = payload;
  els.deviceName.textContent = payload.device_name;
  els.hostOrigin.textContent = window.location.origin;
  setPill(els.deviceStatus, payload.ready_to_receive ? "Ready" : "Off", payload.ready_to_receive ? "ready" : "warning");
}

async function pairDevice() {
  const senderDeviceName = (els.mobileName.value || "iPhone/iPad").trim();
  const pairingCode = els.pairingCode.value.trim();
  if (!pairingCode) {
    els.pairMessage.textContent = "Enter the current 6-digit code from the Windows app.";
    return;
  }

  els.pairButton.disabled = true;
  els.pairMessage.textContent = "Pairing...";
  try {
    const response = await fetch("/api/pair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender_device_id: `mobile-${Math.random().toString(36).slice(2, 10)}`,
        sender_device_name: senderDeviceName,
        pairing_code: pairingCode,
      }),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || "Pairing failed");
    }
    const payload = await response.json();
    state.sessionToken = payload.session_token;
    window.localStorage.setItem("transfer_tool_session", state.sessionToken);
    window.localStorage.setItem("transfer_tool_mobile_name", senderDeviceName);
    setPill(els.sessionBadge, "Paired", "ready");
    els.pairMessage.textContent = `Paired until ${new Date(payload.expires_at).toLocaleTimeString()}.`;
    if (state.selectedFiles.length > 0) {
      els.uploadButton.disabled = false;
    }
    await Promise.all([refreshDownloads(), refreshHistory()]);
  } catch (error) {
    setPill(els.sessionBadge, "Not paired", "neutral");
    els.pairMessage.textContent = error.message;
  } finally {
    els.pairButton.disabled = false;
  }
}

function updateSelectedFiles() {
  state.selectedFiles = Array.from(els.uploadInput.files || []);
  if (state.selectedFiles.length === 0) {
    els.uploadSummary.textContent = "No files selected.";
    els.uploadButton.disabled = true;
    return;
  }
  const totalBytes = state.selectedFiles.reduce((sum, file) => sum + file.size, 0);
  els.uploadSummary.textContent = `${state.selectedFiles.length} file(s) selected, ${formatBytes(totalBytes)}`;
  els.uploadButton.disabled = !state.sessionToken;
}

function uploadFiles() {
  if (!state.sessionToken) {
    els.uploadSummary.textContent = "Pair with the Windows app before uploading.";
    return;
  }
  if (state.selectedFiles.length === 0) {
    return;
  }

  const formData = new FormData();
  state.selectedFiles.forEach((file) => formData.append("files", file));
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/uploads");
  xhr.setRequestHeader(sessionHeader, state.sessionToken);
  setPill(els.uploadState, "Uploading", "ready");
  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      setUploadProgress((event.loaded / event.total) * 100);
    }
  };
  xhr.onload = async () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const payload = JSON.parse(xhr.responseText);
      els.uploadSummary.textContent = `Uploaded to ${payload.saved_to}`;
      setPill(els.uploadState, "Done", "ready");
      setUploadProgress(100);
      els.uploadInput.value = "";
      state.selectedFiles = [];
      els.uploadButton.disabled = true;
      await refreshHistory();
    } else {
      let message = "Upload failed";
      try {
        message = JSON.parse(xhr.responseText).error || message;
      } catch (error) {
        /* ignore parse errors */
      }
      els.uploadSummary.textContent = message;
      setPill(els.uploadState, "Failed", "warning");
      setUploadProgress(0);
    }
  };
  xhr.onerror = () => {
    els.uploadSummary.textContent = "Upload failed because the connection was interrupted.";
    setPill(els.uploadState, "Failed", "warning");
    setUploadProgress(0);
  };
  xhr.send(formData);
}

async function refreshDownloads() {
  if (!state.sessionToken) {
    els.downloadsList.innerHTML = '<p class="helper-text">Pair first to view available downloads.</p>';
    return;
  }
  try {
    const response = await apiFetch("/api/shares");
    const payload = await response.json();
    renderDownloads(payload.items || []);
  } catch (error) {
    els.downloadsList.innerHTML = `<p class="helper-text">${error.message}</p>`;
  }
}

function renderDownloads(items) {
  if (!items.length) {
    els.downloadsList.innerHTML = '<p class="helper-text">No files are currently shared from Windows.</p>';
    return;
  }
  els.downloadsList.innerHTML = "";
  items.forEach((item) => {
    const node = els.downloadTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".item-title").textContent = item.download_name;
    node.querySelector(".item-meta").textContent = `${item.file_count} file(s), ${formatBytes(item.total_bytes)}, ${item.package_kind === "zip" ? "ZIP package" : "Single file"}`;
    node.querySelector(".item-note").textContent = `Shared ${new Date(item.created_at).toLocaleString()} • Downloads: ${item.downloads_count || 0}`;
    const progressFill = node.querySelector(".progress-fill");
    const progressLabel = node.querySelector(".progress-label");
    node.querySelector(".download-button").addEventListener("click", () => {
      downloadShare(item.share_id, item.download_name, progressFill, progressLabel);
    });
    els.downloadsList.appendChild(node);
  });
}

function downloadShare(shareId, fileName, progressFill, progressLabel) {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", `/api/downloads/${encodeURIComponent(shareId)}`);
  xhr.responseType = "blob";
  xhr.setRequestHeader(sessionHeader, state.sessionToken);
  xhr.onprogress = (event) => {
    if (event.lengthComputable) {
      const percent = (event.loaded / event.total) * 100;
      progressFill.style.width = `${percent}%`;
      progressLabel.textContent = `${Math.round(percent)}%`;
    } else {
      progressLabel.textContent = "Downloading";
    }
  };
  xhr.onload = async () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const blob = xhr.response;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      progressFill.style.width = "100%";
      progressLabel.textContent = "Saved";
      await Promise.all([refreshDownloads(), refreshHistory()]);
    } else {
      progressLabel.textContent = "Failed";
    }
  };
  xhr.onerror = () => {
    progressLabel.textContent = "Failed";
  };
  xhr.send();
}

async function refreshHistory() {
  if (!state.sessionToken) {
    els.historyList.innerHTML = '<p class="helper-text">Pair first to view recent transfers.</p>';
    return;
  }
  try {
    const response = await apiFetch("/api/history");
    const payload = await response.json();
    renderHistory(payload.items || []);
  } catch (error) {
    els.historyList.innerHTML = `<p class="helper-text">${error.message}</p>`;
  }
}

function renderHistory(items) {
  if (!items.length) {
    els.historyList.innerHTML = '<p class="helper-text">No transfers yet.</p>';
    return;
  }
  els.historyList.innerHTML = "";
  items.forEach((item) => {
    const node = els.historyTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".item-title").textContent = item.direction === "incoming" ? "Uploaded to Windows" : "Downloaded from Windows";
    node.querySelector(".history-pill").textContent = item.status;
    node.querySelector(".item-meta").textContent = `${item.peer_device_name} • ${new Date(item.timestamp).toLocaleString()}`;
    node.querySelector(".item-note").textContent = item.filenames.join(", ");
    els.historyList.appendChild(node);
  });
}

async function bootstrap() {
  els.mobileName.value = state.mobileName;
  setPill(els.sessionBadge, state.sessionToken ? "Saved session" : "Not paired", state.sessionToken ? "ready" : "neutral");
  setPill(els.uploadState, "Idle", "neutral");
  els.pairButton.addEventListener("click", pairDevice);
  els.uploadInput.addEventListener("change", updateSelectedFiles);
  els.uploadButton.addEventListener("click", uploadFiles);
  els.refreshDownloads.addEventListener("click", refreshDownloads);
  els.refreshHistory.addEventListener("click", refreshHistory);
  await loadDeviceInfo();
  if (state.sessionToken) {
    await Promise.all([refreshDownloads(), refreshHistory()]);
  }
}

bootstrap();
