const STORAGE_KEYS = {
  sessionToken: "transfer_tool_session",
  mobileName: "transfer_tool_mobile_name",
  mobileDeviceId: "transfer_tool_mobile_device_id",
  trustedDeviceToken: "transfer_tool_trusted_device_token",
};

function ensureStoredId(key) {
  let value = window.localStorage.getItem(key);
  if (!value) {
    value = `mobile-${crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2, 12)}`;
    window.localStorage.setItem(key, value);
  }
  return value;
}

const state = {
  sessionToken: window.localStorage.getItem(STORAGE_KEYS.sessionToken) || "",
  trustedDeviceToken: window.localStorage.getItem(STORAGE_KEYS.trustedDeviceToken) || "",
  mobileName: window.localStorage.getItem(STORAGE_KEYS.mobileName) || "",
  mobileDeviceId: ensureStoredId(STORAGE_KEYS.mobileDeviceId),
  selectedFiles: [],
  activeTransfer: null,
  lastFailedTransfer: null,
  restoringTrust: null,
};

const sessionHeader = "X-Session-Token";

const els = {
  sessionBadge: document.querySelector("#session-badge"),
  refreshAll: document.querySelector("#refresh-all"),
  guidanceCard: document.querySelector("#guidance-card"),
  guidanceText: document.querySelector("#guidance-text"),
  pairingCard: document.querySelector("#pairing-card"),
  deviceStatus: document.querySelector("#device-status"),
  pairMessage: document.querySelector("#pair-message"),
  mobileName: document.querySelector("#mobile-name"),
  pairingCode: document.querySelector("#pairing-code"),
  pairButton: document.querySelector("#pair-button"),
  uploadInput: document.querySelector("#upload-input"),
  uploadSummary: document.querySelector("#upload-summary"),
  uploadButton: document.querySelector("#upload-button"),
  uploadState: document.querySelector("#upload-state"),
  uploadProgress: document.querySelector("#upload-progress"),
  uploadProgressLabel: document.querySelector("#upload-progress-label"),
  downloadsList: document.querySelector("#downloads-list"),
  historyList: document.querySelector("#history-list"),
  transferState: document.querySelector("#transfer-state"),
  transferMessage: document.querySelector("#transfer-message"),
  transferDetail: document.querySelector("#transfer-detail"),
  transferProgress: document.querySelector("#transfer-progress"),
  transferProgressLabel: document.querySelector("#transfer-progress-label"),
  retryTransfer: document.querySelector("#retry-transfer"),
  cancelTransfer: document.querySelector("#cancel-transfer"),
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

function setTransferProgress(percent) {
  const safePercent = Math.min(100, Math.max(0, percent));
  els.transferProgress.style.width = `${safePercent}%`;
  els.transferProgressLabel.textContent = `${Math.round(safePercent)}%`;
}

function updateTransferButtons() {
  els.cancelTransfer.disabled = !state.activeTransfer;
  els.retryTransfer.disabled = !state.lastFailedTransfer || !!state.activeTransfer;
  els.uploadButton.disabled = !state.sessionToken || state.selectedFiles.length === 0 || !!state.activeTransfer;
}

function setSessionToken(token) {
  state.sessionToken = token || "";
  if (state.sessionToken) {
    window.localStorage.setItem(STORAGE_KEYS.sessionToken, state.sessionToken);
  } else {
    window.localStorage.removeItem(STORAGE_KEYS.sessionToken);
  }
}

function storeTrustedToken(token) {
  state.trustedDeviceToken = token || "";
  if (state.trustedDeviceToken) {
    window.localStorage.setItem(STORAGE_KEYS.trustedDeviceToken, state.trustedDeviceToken);
  } else {
    window.localStorage.removeItem(STORAGE_KEYS.trustedDeviceToken);
  }
}

function clearStoredTrust() {
  setSessionToken("");
  storeTrustedToken("");
  setPill(els.sessionBadge, "Pairing needed", "neutral");
  showPairingUI(true);
  updateTransferButtons();
}

function showPairingUI(visible) {
  els.pairingCard.hidden = !visible;
  els.guidanceText.textContent = visible
    ? "Step 1: Scan the QR code shown on Windows. Step 2: Select files to upload or download shared files below."
    : "Connected. Select files to upload or download shared files below.";
}

function startTransfer(options) {
  state.activeTransfer = {
    type: options.type,
    xhr: options.xhr,
    retryAction: options.retryAction || null,
  };
  state.lastFailedTransfer = null;
  setPill(els.transferState, options.type === "download" ? "Downloading" : "Uploading", "ready");
  els.transferMessage.textContent = options.label;
  els.transferDetail.textContent = "Transfer in progress.";
  setTransferProgress(0);
  updateTransferButtons();
}

function finishTransfer(message, detail) {
  state.activeTransfer = null;
  setPill(els.transferState, "Done", "ready");
  els.transferMessage.textContent = message;
  els.transferDetail.textContent = detail;
  setTransferProgress(100);
  updateTransferButtons();
}

function failTransfer(message, detail, retryAction) {
  state.activeTransfer = null;
  state.lastFailedTransfer = retryAction || null;
  setPill(els.transferState, "Failed", "warning");
  els.transferMessage.textContent = message;
  els.transferDetail.textContent = detail;
  setTransferProgress(0);
  updateTransferButtons();
}

function cancelActiveTransfer() {
  if (!state.activeTransfer) return;
  state.lastFailedTransfer = state.activeTransfer.retryAction;
  state.activeTransfer.xhr.abort();
  state.activeTransfer = null;
  setPill(els.transferState, "Cancelled", "neutral");
  els.transferMessage.textContent = "Transfer cancelled";
  els.transferDetail.textContent = "You can retry the last transfer.";
  setTransferProgress(0);
  updateTransferButtons();
}

function buildSenderPayload() {
  const senderDeviceName = (els.mobileName.value || state.mobileName || "iPhone/iPad").trim() || "iPhone/iPad";
  state.mobileName = senderDeviceName;
  window.localStorage.setItem(STORAGE_KEYS.mobileName, senderDeviceName);
  return {
    sender_device_id: state.mobileDeviceId,
    sender_device_name: senderDeviceName,
  };
}

async function apiFetch(path, options = {}, allowTrustRetry = true) {
  const headers = new Headers(options.headers || {});
  if (state.sessionToken) {
    headers.set(sessionHeader, state.sessionToken);
  }
  const response = await fetch(path, { ...options, headers });
  if (response.ok) {
    return response;
  }

  if (response.status === 401 && allowTrustRetry && state.trustedDeviceToken) {
    const restored = await restoreTrustedSession({ silent: true });
    if (restored) {
      return apiFetch(path, options, false);
    }
  }

  let message = `Request failed (${response.status})`;
  try {
    const payload = await response.json();
    message = payload.error || message;
  } catch (error) {
    /* ignore parse errors */
  }
  throw new Error(message);
}

async function loadDeviceInfo() {
  const response = await fetch("/api/device");
  const payload = await response.json();
  setPill(els.deviceStatus, payload.ready_to_receive ? "Ready" : "Off", payload.ready_to_receive ? "ready" : "warning");
}

function applyTrustedState() {
  const trusted = !!state.trustedDeviceToken || !!state.sessionToken;
  setPill(els.sessionBadge, trusted ? "Trusted" : "Pairing needed", trusted ? "ready" : "neutral");
  showPairingUI(!trusted);
}

async function restoreTrustedSession({ silent = false } = {}) {
  if (!state.trustedDeviceToken) {
    return false;
  }
  if (state.restoringTrust) {
    return state.restoringTrust;
  }

  state.restoringTrust = (async () => {
    try {
      const response = await fetch("/api/trusted-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trusted_device_token: state.trustedDeviceToken,
          ...buildSenderPayload(),
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || "Trusted access expired");
      }
      const payload = await response.json();
      setSessionToken(payload.session_token);
      applyTrustedState();
      if (!silent) {
        els.transferMessage.textContent = "Connected";
        els.transferDetail.textContent = "This device is already trusted.";
      }
      updateTransferButtons();
      return true;
    } catch (error) {
      clearStoredTrust();
      if (!silent) {
        els.pairMessage.textContent = error.message;
      }
      return false;
    } finally {
      state.restoringTrust = null;
    }
  })();

  return state.restoringTrust;
}

function storeSuccessfulPairing(payload, successMessage) {
  setSessionToken(payload.session_token);
  if (payload.trusted_device_token) {
    storeTrustedToken(payload.trusted_device_token);
  }
  applyTrustedState();
  els.pairMessage.textContent = successMessage;
  updateTransferButtons();
}

async function pairDevice() {
  const pairingCode = els.pairingCode.value.trim();
  if (!pairingCode) {
    els.pairMessage.textContent = "Enter the 6-digit code shown on Windows.";
    return;
  }

  els.pairButton.disabled = true;
  els.pairMessage.textContent = "Pairing...";
  try {
    const response = await fetch("/api/pair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...buildSenderPayload(),
        pairing_code: pairingCode,
      }),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || "Pairing failed");
    }
    const payload = await response.json();
    storeSuccessfulPairing(payload, "Connected. You can upload or download files now.");
    await refreshMainData();
  } catch (error) {
    setPill(els.sessionBadge, "Pairing needed", "neutral");
    els.pairMessage.textContent = error.message;
    updateTransferButtons();
  } finally {
    els.pairButton.disabled = false;
  }
}

async function pairFromQrToken(pairToken) {
  if (!pairToken) {
    return false;
  }
  els.pairMessage.textContent = "Finishing pairing from QR code...";
  try {
    const response = await fetch("/api/pair/direct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...buildSenderPayload(),
        pair_token: pairToken,
      }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "QR pairing failed");
    }
    const payload = await response.json();
    storeSuccessfulPairing(payload, "Connected. You can upload or download files now.");
    await refreshMainData();
    return true;
  } catch (error) {
    els.pairMessage.textContent = error.message;
    setPill(els.sessionBadge, "Pairing needed", "neutral");
    return false;
  }
}

async function ensureActiveSession() {
  if (state.sessionToken) {
    return true;
  }
  return restoreTrustedSession();
}

function updateSelectedFiles() {
  state.selectedFiles = Array.from(els.uploadInput.files || []);
  if (state.selectedFiles.length === 0) {
    els.uploadSummary.textContent = "No files selected.";
    setUploadProgress(0);
    updateTransferButtons();
    return;
  }
  const totalBytes = state.selectedFiles.reduce((sum, file) => sum + file.size, 0);
  els.uploadSummary.textContent = `${state.selectedFiles.length} file(s) selected, ${formatBytes(totalBytes)}`;
  updateTransferButtons();
}

async function uploadFiles() {
  if (state.activeTransfer) {
    els.uploadSummary.textContent = "Finish or cancel the current transfer first.";
    return;
  }
  if (!(await ensureActiveSession())) {
    els.uploadSummary.textContent = "Pair again to keep using this device.";
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
  startTransfer({
    type: "upload",
    xhr,
    label: "Uploading files",
    retryAction: () => uploadFiles(),
  });

  xhr.upload.onprogress = (event) => {
    if (!event.lengthComputable) {
      return;
    }
    const percent = (event.loaded / event.total) * 100;
    setUploadProgress(percent);
    setTransferProgress(percent);
    els.transferDetail.textContent = `${formatBytes(event.loaded)} of ${formatBytes(event.total)} uploaded`;
  };

  xhr.onload = async () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      els.uploadSummary.textContent = "Upload complete";
      setPill(els.uploadState, "Done", "ready");
      setUploadProgress(100);
      finishTransfer("Upload complete", "Saved on Windows.");
      els.uploadInput.value = "";
      state.selectedFiles = [];
      updateTransferButtons();
      await refreshHistory();
      return;
    }

    let message = "Upload failed";
    try {
      message = JSON.parse(xhr.responseText).error || message;
    } catch (error) {
      /* ignore parse errors */
    }
    els.uploadSummary.textContent = message;
    setPill(els.uploadState, "Failed", "warning");
    setUploadProgress(0);
    failTransfer("Upload failed", message, () => uploadFiles());
  };

  xhr.onerror = () => {
    const message = "The connection was interrupted.";
    els.uploadSummary.textContent = "Upload failed";
    setPill(els.uploadState, "Failed", "warning");
    setUploadProgress(0);
    failTransfer("Upload failed", message, () => uploadFiles());
  };

  xhr.onabort = () => {
    els.uploadSummary.textContent = "Upload cancelled.";
    setPill(els.uploadState, "Idle", "neutral");
    setUploadProgress(0);
  };

  xhr.send(formData);
}

async function refreshDownloads() {
  if (!(await ensureActiveSession())) {
    els.downloadsList.innerHTML = '<p class="body-copy">Pair this device to see shared files.</p>';
    return;
  }
  try {
    const response = await apiFetch("/api/shares");
    const payload = await response.json();
    renderDownloads(payload.items || []);
  } catch (error) {
    els.downloadsList.innerHTML = `<p class="body-copy">${error.message}</p>`;
  }
}

function renderDownloads(items) {
  if (!items.length) {
    els.downloadsList.innerHTML = '<p class="body-copy">No shared files right now.</p>';
    return;
  }

  els.downloadsList.innerHTML = "";
  items.forEach((item) => {
    const node = els.downloadTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".item-title").textContent = item.download_name;
    node.querySelector(".item-meta").textContent = `${item.file_count} file(s) • ${formatBytes(item.total_bytes)}`;
    node.querySelector(".item-note").textContent = `Shared ${new Date(item.created_at).toLocaleString()}`;
    const progressFill = node.querySelector(".progress-fill");
    const progressLabel = node.querySelector(".progress-label");
    const downloadPill = node.querySelector(".download-pill");
    node.querySelector(".download-button").addEventListener("click", () => {
      downloadShare(item.share_id, item.download_name, progressFill, progressLabel, downloadPill);
    });
    els.downloadsList.appendChild(node);
  });
}

async function downloadShare(shareId, fileName, progressFill, progressLabel, downloadPill) {
  if (state.activeTransfer) {
    els.transferMessage.textContent = "Finish or cancel the current transfer first.";
    return;
  }
  if (!(await ensureActiveSession())) {
    failTransfer("Download blocked", "Pair again to keep using this device.", null);
    return;
  }

  const xhr = new XMLHttpRequest();
  xhr.open("GET", `/api/downloads/${encodeURIComponent(shareId)}`);
  xhr.responseType = "blob";
  xhr.setRequestHeader(sessionHeader, state.sessionToken);
  downloadPill.textContent = "Downloading";
  startTransfer({
    type: "download",
    xhr,
    label: `Downloading ${fileName}`,
    retryAction: () => downloadShare(shareId, fileName, progressFill, progressLabel, downloadPill),
  });

  xhr.onprogress = (event) => {
    if (event.lengthComputable) {
      const percent = (event.loaded / event.total) * 100;
      progressFill.style.width = `${percent}%`;
      progressLabel.textContent = `${Math.round(percent)}%`;
      setTransferProgress(percent);
      els.transferDetail.textContent = `${formatBytes(event.loaded)} of ${formatBytes(event.total)} downloaded`;
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
      progressLabel.textContent = "100%";
      downloadPill.textContent = "Ready";
      finishTransfer("Download ready", "Check Safari Downloads.");
      await Promise.all([refreshDownloads(), refreshHistory()]);
      return;
    }

    let message = "Download failed";
    try {
      message = JSON.parse(xhr.responseText).error || message;
    } catch (error) {
      /* ignore parse errors */
    }
    progressFill.style.width = "0%";
    progressLabel.textContent = "0%";
    downloadPill.textContent = "Ready";
    failTransfer("Download failed", message, () => downloadShare(shareId, fileName, progressFill, progressLabel, downloadPill));
  };

  xhr.onerror = () => {
    progressFill.style.width = "0%";
    progressLabel.textContent = "0%";
    downloadPill.textContent = "Ready";
    failTransfer(
      "Download failed",
      "The connection was interrupted.",
      () => downloadShare(shareId, fileName, progressFill, progressLabel, downloadPill),
    );
  };

  xhr.onabort = () => {
    progressFill.style.width = "0%";
    progressLabel.textContent = "0%";
    downloadPill.textContent = "Ready";
  };

  xhr.send();
}

async function refreshHistory() {
  if (!(await ensureActiveSession())) {
    els.historyList.innerHTML = '<p class="body-copy">Recent activity will appear here after pairing.</p>';
    return;
  }
  try {
    const response = await apiFetch("/api/history");
    const payload = await response.json();
    renderHistory(payload.items || []);
  } catch (error) {
    els.historyList.innerHTML = `<p class="body-copy">${error.message}</p>`;
  }
}

function renderHistory(items) {
  if (!items.length) {
    els.historyList.innerHTML = '<p class="body-copy">No recent transfers yet.</p>';
    return;
  }

  els.historyList.innerHTML = "";
  items.slice(0, 5).forEach((item) => {
    const node = els.historyTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".item-title").textContent = item.direction === "incoming" ? "Uploaded to Windows" : "Downloaded from Windows";
    node.querySelector(".history-pill").textContent = item.status;
    node.querySelector(".item-meta").textContent = new Date(item.timestamp).toLocaleString();
    node.querySelector(".item-note").textContent = item.filenames.join(", ");
    els.historyList.appendChild(node);
  });
}

async function refreshMainData() {
  await Promise.all([refreshDownloads(), refreshHistory()]);
}

async function retryLastTransfer() {
  if (!state.lastFailedTransfer || state.activeTransfer) {
    return;
  }
  const retryAction = state.lastFailedTransfer;
  state.lastFailedTransfer = null;
  updateTransferButtons();
  retryAction();
}

function removePairTokenFromUrl() {
  const url = new URL(window.location.href);
  url.searchParams.delete("pair_token");
  window.history.replaceState({}, "", url.toString());
}

function wireEvents() {
  els.refreshAll.addEventListener("click", refreshMainData);
  els.pairButton.addEventListener("click", pairDevice);
  els.uploadInput.addEventListener("change", updateSelectedFiles);
  els.uploadButton.addEventListener("click", uploadFiles);
  els.retryTransfer.addEventListener("click", retryLastTransfer);
  els.cancelTransfer.addEventListener("click", cancelActiveTransfer);
}

async function bootstrap() {
  els.mobileName.value = state.mobileName;
  setPill(els.uploadState, "Idle", "neutral");
  setPill(els.transferState, "Idle", "neutral");
  wireEvents();
  applyTrustedState();
  updateTransferButtons();
  await loadDeviceInfo();

  const pairToken = new URL(window.location.href).searchParams.get("pair_token");
  if (pairToken) {
    const paired = await pairFromQrToken(pairToken);
    removePairTokenFromUrl();
    if (paired) {
      return;
    }
  }

  if (state.trustedDeviceToken) {
    const restored = await restoreTrustedSession();
    if (restored) {
      await refreshMainData();
      return;
    }
  }

  if (state.sessionToken) {
    await refreshMainData();
  } else {
    els.historyList.innerHTML = '<p class="body-copy">Recent activity will appear here after pairing.</p>';
    els.downloadsList.innerHTML = '<p class="body-copy">Shared files from Windows will appear here after pairing.</p>';
  }
}

bootstrap();
