// DocuParse AI - Interactive Frontend Controller

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // State
  let currentDocument = null;
  let geminiApiKey = localStorage.getItem("docu_gemini_api_key") || "";

  // DOM Elements
  const uploadSection = document.getElementById("upload-section");
  const fileInput = document.getElementById("file-input");
  const uploadLoading = document.getElementById("upload-loading");
  const loadingStatusText = document.getElementById("loading-status-text");
  const workspaceSection = document.getElementById("workspace-section");

  const previewContainer = document.getElementById("preview-container");
  const previewFilename = document.getElementById("preview-filename");
  const previewOpenLink = document.getElementById("preview-open-link");

  const valMerchant = document.getElementById("val-merchant");
  const valInvoiceNo = document.getElementById("val-invoice-no");
  const valDate = document.getElementById("val-date");
  const valGrandTotal = document.getElementById("val-grand-total");
  const valDocId = document.getElementById("val-doc-id");
  const valTax = document.getElementById("val-tax");
  const valCalculatedSum = document.getElementById("val-calculated-sum");
  const lineItemsCount = document.getElementById("line-items-count");
  const lineItemsTbody = document.getElementById("line-items-tbody");
  const btnExportCsv = document.getElementById("btn-export-csv");

  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnToggleHistory = document.getElementById("btn-toggle-history");
  const historyModal = document.getElementById("history-modal");
  const btnCloseHistory = document.getElementById("btn-close-history");
  const historyListContainer = document.getElementById("history-list-container");
  const historyCount = document.getElementById("history-count");

  const btnConfigKey = document.getElementById("btn-config-key");
  const apiKeyModal = document.getElementById("apikey-modal");
  const btnCloseApiKey = document.getElementById("btn-close-apikey");
  const inputGeminiKey = document.getElementById("input-gemini-key");
  const btnSaveKey = document.getElementById("btn-save-key");
  const btnClearKey = document.getElementById("btn-clear-key");
  const apiKeyStatus = document.getElementById("api-key-status");

  // Update API Key UI State
  function updateApiKeyStatus() {
    if (geminiApiKey) {
      apiKeyStatus.textContent = "LLM: Custom Gemini Key";
      apiKeyStatus.classList.add("text-indigo-600");
    } else {
      apiKeyStatus.textContent = "LLM: Fallback/Env";
      apiKeyStatus.classList.remove("text-indigo-600");
    }
  }
  updateApiKeyStatus();

  // Load Document History count
  async function refreshHistory() {
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const docs = await res.json();
        historyCount.textContent = docs.length;
        renderHistoryList(docs);
      }
    } catch (e) {
      console.warn("Could not load history:", e);
    }
  }
  refreshHistory();

  // Render History List
  function renderHistoryList(docs) {
    if (!docs || docs.length === 0) {
      historyListContainer.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs">
          No documents parsed yet. Upload your first invoice above!
        </div>
      `;
      return;
    }

    historyListContainer.innerHTML = docs.map(d => `
      <div class="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition cursor-pointer group" data-doc-id="${d.id}">
        <div class="flex items-center space-x-3 overflow-hidden">
          <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <i data-lucide="file-text" class="w-4 h-4"></i>
          </div>
          <div class="truncate">
            <p class="text-xs font-semibold text-slate-800 truncate">${escapeHtml(d.merchant || d.filename)}</p>
            <p class="text-[11px] text-slate-500">${escapeHtml(d.invoice_no || 'No Inv #')} • ${escapeHtml(d.date || 'No Date')}</p>
          </div>
        </div>
        <div class="flex items-center space-x-3 flex-shrink-0">
          <span class="text-xs font-bold text-slate-800">${d.currency || '$'}${Number(d.grand_total || 0).toFixed(2)}</span>
          <button class="btn-delete-doc p-1 text-slate-400 hover:text-red-600 rounded transition" data-delete-id="${d.id}" title="Delete document">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `).join("");

    lucide.createIcons();

    // Attach click listeners
    historyListContainer.querySelectorAll("[data-doc-id]").forEach(item => {
      item.addEventListener("click", async (e) => {
        if (e.target.closest(".btn-delete-doc")) return;
        const id = item.getAttribute("data-doc-id");
        historyModal.classList.add("hidden");
        loadDocumentById(id);
      });
    });

    historyListContainer.querySelectorAll(".btn-delete-doc").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-delete-id");
        if (confirm("Delete this document and its line items?")) {
          await fetch(`/api/documents/${id}`, { method: "DELETE" });
          refreshHistory();
          if (currentDocument && currentDocument.id == id) {
            workspaceSection.classList.add("hidden");
            currentDocument = null;
          }
        }
      });
    });
  }

  // Load specific document by ID
  async function loadDocumentById(id) {
    try {
      const res = await fetch(`/api/documents/${id}`);
      if (!res.ok) throw new Error("Document not found");
      const doc = await res.json();
      displayDocumentData(doc);
    } catch (e) {
      alert("Error loading document: " + e.message);
    }
  }

  // Drag-and-Drop & File Input Handlers
  uploadSection.addEventListener("click", () => fileInput.click());

  uploadSection.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadSection.classList.add("border-indigo-500", "bg-indigo-50/20");
  });

  ["dragleave", "dragend"].forEach(type => {
    uploadSection.addEventListener(type, () => {
      uploadSection.classList.remove("border-indigo-500", "bg-indigo-50/20");
    });
  });

  uploadSection.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadSection.classList.remove("border-indigo-500", "bg-indigo-50/20");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      uploadFile(fileInput.files[0]);
    }
  });

  // Upload and Parse API Call
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    uploadLoading.classList.remove("hidden");
    loadingStatusText.textContent = `Processing ${file.name} with LLM schema...`;

    try {
      const headers = {};
      if (geminiApiKey) {
        headers["X-Gemini-Api-Key"] = geminiApiKey;
      }

      const response = await fetch("/api/parse", {
        method: "POST",
        headers: headers,
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned ${response.status}`);
      }

      const result = await response.json();
      currentDocument = result.document;
      displayDocumentData(result.document);
      refreshHistory();

    } catch (err) {
      alert("Failed to parse document: " + err.message);
    } finally {
      uploadLoading.classList.add("hidden");
      fileInput.value = "";
    }
  }

  // Display Document & Extracted Data in Workspace
  function displayDocumentData(doc) {
    currentDocument = doc;
    workspaceSection.classList.remove("hidden");

    // Scroll smoothly to workspace
    workspaceSection.scrollIntoView({ behavior: "smooth" });

    // 1. Render Left Preview Column
    previewFilename.textContent = doc.filename;
    previewOpenLink.href = doc.file_path;

    const isPdf = doc.filename.toLowerCase().endsWith(".pdf") || (doc.content_type && doc.content_type.includes("pdf"));

    if (isPdf) {
      previewContainer.innerHTML = `
        <iframe src="${doc.file_path}#view=FitH" class="w-full h-full rounded-lg border-0 shadow-inner bg-white"></iframe>
      `;
    } else {
      previewContainer.innerHTML = `
        <div class="w-full h-full flex items-center justify-center p-2">
          <img src="${doc.file_path}" alt="Document Preview" class="max-w-full max-h-full object-contain rounded-lg shadow-sm border border-slate-200">
        </div>
      `;
    }

    // 2. Render Right Extracted Data Column
    valMerchant.textContent = doc.merchant || "Unknown Merchant";
    valInvoiceNo.textContent = doc.invoice_no || "N/A";
    valDate.textContent = doc.date || "N/A";
    
    const curr = doc.currency || "$";
    valGrandTotal.textContent = `${curr}${Number(doc.grand_total || 0).toFixed(2)}`;
    valDocId.textContent = `#${doc.id}`;
    valTax.textContent = `${curr}${Number(doc.tax || 0).toFixed(2)}`;

    // Render Line Items
    const items = doc.line_items || [];
    lineItemsCount.textContent = items.length;

    let itemsSum = 0;
    if (items.length === 0) {
      lineItemsTbody.innerHTML = `
        <tr>
          <td colspan="5" class="py-6 text-center text-slate-400">No line items identified.</td>
        </tr>
      `;
    } else {
      lineItemsTbody.innerHTML = items.map((item, idx) => {
        itemsSum += Number(item.total_price || 0);
        return `
          <tr class="hover:bg-slate-50/70 transition">
            <td class="py-3 px-3 text-center text-slate-400 font-mono text-[11px]">${idx + 1}</td>
            <td class="py-3 px-4 font-medium text-slate-800">${escapeHtml(item.description)}</td>
            <td class="py-3 px-3 text-right text-slate-600 font-mono">${item.quantity}</td>
            <td class="py-3 px-3 text-right text-slate-600 font-mono">${curr}${Number(item.unit_price).toFixed(2)}</td>
            <td class="py-3 px-4 text-right font-semibold text-slate-800 font-mono">${curr}${Number(item.total_price).toFixed(2)}</td>
          </tr>
        `;
      }).join("");
    }

    valCalculatedSum.textContent = `${curr}${itemsSum.toFixed(2)}`;
    lucide.createIcons();
  }

  // Export CSV Action
  btnExportCsv.addEventListener("click", () => {
    if (!currentDocument || !currentDocument.id) {
      alert("No active document loaded.");
      return;
    }
    // Direct browser download from the API endpoint
    window.location.href = `/api/documents/${currentDocument.id}/export-csv`;
  });

  // Load Sample Invoice Quick Test
  btnLoadSample.addEventListener("click", async () => {
    try {
      uploadLoading.classList.remove("hidden");
      loadingStatusText.textContent = "Loading and parsing Acme Cloud sample invoice...";

      // Fetch the sample invoice file from static assets
      const sampleResp = await fetch("/static/sample_invoice.pdf");
      if (!sampleResp.ok) throw new Error("Sample file not found");
      const blob = await sampleResp.blob();
      const file = new File([blob], "sample_invoice.pdf", { type: "application/pdf" });

      // Run parse
      await uploadFile(file);
    } catch (err) {
      alert("Error loading sample invoice: " + err.message);
      uploadLoading.classList.add("hidden");
    }
  });

  // History Modal handlers
  btnToggleHistory.addEventListener("click", () => {
    historyModal.classList.remove("hidden");
  });
  btnCloseHistory.addEventListener("click", () => {
    historyModal.classList.add("hidden");
  });
  historyModal.addEventListener("click", (e) => {
    if (e.target === historyModal) historyModal.classList.add("hidden");
  });

  // API Key Modal handlers
  btnConfigKey.addEventListener("click", () => {
    inputGeminiKey.value = geminiApiKey;
    apiKeyModal.classList.remove("hidden");
  });
  btnCloseApiKey.addEventListener("click", () => {
    apiKeyModal.classList.add("hidden");
  });
  apiKeyModal.addEventListener("click", (e) => {
    if (e.target === apiKeyModal) apiKeyModal.classList.add("hidden");
  });
  btnSaveKey.addEventListener("click", () => {
    geminiApiKey = inputGeminiKey.value.trim();
    localStorage.setItem("docu_gemini_api_key", geminiApiKey);
    updateApiKeyStatus();
    apiKeyModal.classList.add("hidden");
  });
  btnClearKey.addEventListener("click", () => {
    geminiApiKey = "";
    inputGeminiKey.value = "";
    localStorage.removeItem("docu_gemini_api_key");
    updateApiKeyStatus();
    apiKeyModal.classList.add("hidden");
  });

  // Helper: Escape HTML to avoid XSS
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
