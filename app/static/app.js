// DocuParse AI - Dynamic Multimodal Document & Vision Controller

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

  const badgeDocType = document.getElementById("badge-doc-type");
  const badgeEngine = document.getElementById("badge-engine");
  const extractedHeading = document.getElementById("extracted-heading");
  const extractedSubheading = document.getElementById("extracted-subheading");

  // Metadata Card Elements
  const labelMerchant = document.getElementById("label-merchant");
  const valMerchant = document.getElementById("val-merchant");
  const labelInvoiceNo = document.getElementById("label-invoice-no");
  const valInvoiceNo = document.getElementById("val-invoice-no");
  const labelDate = document.getElementById("label-date");
  const valDate = document.getElementById("val-date");
  const cardTotalBox = document.getElementById("card-total-box");
  const labelCard4 = document.getElementById("label-card-4");
  const valCard4 = document.getElementById("val-card-4");

  const notesBanner = document.getElementById("notes-banner");
  const valNotes = document.getElementById("val-notes");

  // Dynamic Table Elements
  const dynamicThead = document.getElementById("dynamic-thead");
  const dynamicTbody = document.getElementById("dynamic-tbody");
  const rowsCount = document.getElementById("rows-count");
  const colsCount = document.getElementById("cols-count");
  const tableModeBadge = document.getElementById("table-mode-badge");

  const valDocId = document.getElementById("val-doc-id");
  const valTax = document.getElementById("val-tax");
  const taxContainer = document.getElementById("tax-container");
  const taxDivider = document.getElementById("tax-divider");
  const valInspector = document.getElementById("val-inspector");
  const inspectorContainer = document.getElementById("inspector-container");
  const inspectorDivider = document.getElementById("inspector-divider");

  const btnExportCsv = document.getElementById("btn-export-csv");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnLoadAudit = document.getElementById("btn-load-audit");

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
      apiKeyStatus.textContent = "Custom Key: Active";
      apiKeyStatus.classList.add("text-emerald-700", "font-bold");
    } else {
      apiKeyStatus.textContent = "Custom API Key";
      apiKeyStatus.classList.remove("text-emerald-700", "font-bold");
    }
  }
  updateApiKeyStatus();

  // Load Document History
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

  function renderHistoryList(docs) {
    if (!docs || docs.length === 0) {
      historyListContainer.innerHTML = `
        <div class="text-center py-8 text-slate-400 text-xs">
          No documents parsed yet. Upload your first invoice or stock audit above!
        </div>
      `;
      return;
    }

    historyListContainer.innerHTML = docs.map(d => {
      const isInvoice = (d.doc_type || "").includes("invoice");
      const icon = isInvoice ? "receipt" : "clipboard-check";
      const iconBg = isInvoice ? "bg-indigo-50 text-indigo-600" : "bg-emerald-50 text-emerald-600";
      const badgeText = isInvoice ? `${d.currency || '$'}${Number(d.grand_total || 0).toFixed(2)}` : `${(d.rows || []).length || (d.line_items || []).length} items`;

      return `
        <div class="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-slate-50 transition cursor-pointer group" data-doc-id="${d.id}">
          <div class="flex items-center space-x-3 overflow-hidden">
            <div class="w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center shrink-0">
              <i data-lucide="${icon}" class="w-4 h-4"></i>
            </div>
            <div class="truncate">
              <p class="text-xs font-semibold text-slate-800 truncate">${escapeHtml(d.merchant || d.title || d.filename)}</p>
              <p class="text-[11px] text-slate-500">${escapeHtml(d.invoice_no || d.reference_no || 'Ref')} • ${escapeHtml(d.date || 'No Date')} • <span class="capitalize text-slate-600">${escapeHtml(d.doc_type || 'doc')}</span></p>
            </div>
          </div>
          <div class="flex items-center space-x-3 shrink-0">
            <span class="text-xs font-bold text-slate-800">${badgeText}</span>
            <button class="btn-delete-doc p-1 text-slate-400 hover:text-red-600 rounded transition" data-delete-id="${d.id}" title="Delete document">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>
      `;
    }).join("");

    lucide.createIcons();

    // Attach listeners
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
        if (confirm("Delete this document record?")) {
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

  // Load document by ID
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

  // Upload handlers
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

  // Upload & Parse API Call
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    uploadLoading.classList.remove("hidden");
    loadingStatusText.textContent = `Analyzing ${file.name} with Gemini 2.5 Flash Vision...`;

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
      alert("Document parsing failed: " + err.message);
    } finally {
      uploadLoading.classList.add("hidden");
      fileInput.value = "";
    }
  }

  // Display Document & Adapt UI to Dynamic Columns and Rows
  function displayDocumentData(doc) {
    currentDocument = doc;
    workspaceSection.classList.remove("hidden");
    workspaceSection.scrollIntoView({ behavior: "smooth" });

    // 1. Document Preview
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
          <img src="${doc.file_path}" alt="Document Preview" class="max-w-full max-h-full object-contain rounded-lg shadow-xs border border-slate-200">
        </div>
      `;
    }

    // 2. Determine Document Type and Style
    const docType = (doc.doc_type || "invoice").toLowerCase();
    const isInvoice = docType.includes("invoice") || docType.includes("receipt");

    badgeDocType.textContent = isInvoice ? "Invoice" : docType.replace("_", " ").toUpperCase();
    if (isInvoice) {
      badgeDocType.className = "bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider";
      extractedHeading.textContent = "Extracted Invoice Record";
      extractedSubheading.textContent = "Relational financial line items & tax calculations";
    } else {
      badgeDocType.className = "bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider";
      extractedHeading.textContent = "Extracted Tabular & Audit Record";
      extractedSubheading.textContent = "Dynamic grid adapted to document headers and handwriting";
    }

    // 3. Adaptive Metadata Cards
    if (isInvoice) {
      labelMerchant.textContent = "Merchant / Vendor";
      valMerchant.textContent = doc.merchant || doc.title || "Unknown Merchant";

      labelInvoiceNo.textContent = "Invoice #";
      valInvoiceNo.textContent = doc.invoice_no || doc.reference_no || "N/A";

      labelDate.textContent = "Invoice Date";
      valDate.textContent = doc.date || "N/A";

      cardTotalBox.className = "p-3 bg-indigo-50/60 rounded-xl border border-indigo-100";
      labelCard4.textContent = "Grand Total";
      labelCard4.className = "text-[11px] font-medium text-indigo-600 uppercase tracking-wider block";
      const curr = doc.currency || "$";
      valCard4.textContent = `${curr}${Number(doc.grand_total || 0).toFixed(2)}`;
      valCard4.className = "text-base font-bold text-indigo-700 block truncate mt-0.5";

      taxContainer.classList.remove("hidden");
      taxDivider.classList.remove("hidden");
      valTax.textContent = `${curr}${Number(doc.tax || 0).toFixed(2)}`;

      inspectorContainer.classList.add("hidden");
      inspectorDivider.classList.add("hidden");
    } else {
      // Stock Audit / Custom Table Mode
      labelMerchant.textContent = "Document / Audit Title";
      valMerchant.textContent = doc.title || doc.merchant || "Stock Audit Sheet";

      labelInvoiceNo.textContent = "Audit / Sheet #";
      valInvoiceNo.textContent = doc.reference_no || doc.invoice_no || "N/A";

      labelDate.textContent = "Audit Date";
      valDate.textContent = doc.date || "N/A";

      cardTotalBox.className = "p-3 bg-emerald-50/60 rounded-xl border border-emerald-200";
      if (doc.inspector) {
        labelCard4.textContent = "Auditor / Checked By";
        labelCard4.className = "text-[11px] font-medium text-emerald-700 uppercase tracking-wider block";
        valCard4.textContent = doc.inspector;
        valCard4.className = "text-sm font-bold text-emerald-900 block truncate mt-0.5";
      } else {
        labelCard4.textContent = "Total Items Count";
        labelCard4.className = "text-[11px] font-medium text-emerald-700 uppercase tracking-wider block";
        valCard4.textContent = `${(doc.rows || []).length || (doc.line_items || []).length} Rows`;
        valCard4.className = "text-base font-bold text-emerald-800 block truncate mt-0.5";
      }

      taxContainer.classList.add("hidden");
      taxDivider.classList.add("hidden");

      if (doc.inspector) {
        inspectorContainer.classList.remove("hidden");
        inspectorDivider.classList.remove("hidden");
        valInspector.textContent = doc.inspector;
      } else {
        inspectorContainer.classList.add("hidden");
        inspectorDivider.classList.add("hidden");
      }
    }

    valDocId.textContent = `#${doc.id}`;

    // 4. Notes / Handwritten Remarks Banner
    if (doc.notes && doc.notes.trim()) {
      notesBanner.classList.remove("hidden");
      valNotes.textContent = doc.notes.trim();
    } else {
      notesBanner.classList.add("hidden");
    }

    // 5. Dynamic Table Rendering
    renderDynamicTable(doc, isInvoice);

    lucide.createIcons();
  }

  // Render Dynamic Columns & Rows
  function renderDynamicTable(doc, isInvoice) {
    let columns = doc.columns || [];
    let rows = doc.rows || [];

    // Fallback if columns not set but line_items present
    if ((!columns || columns.length === 0) && doc.line_items && doc.line_items.length > 0) {
      columns = ["Description", "Quantity", "Unit Price", "Total"];
      const curr = doc.currency || "$";
      rows = doc.line_items.map(item => ({
        "Description": item.description,
        "Quantity": String(item.quantity),
        "Unit Price": `${curr}${Number(item.unit_price).toFixed(2)}`,
        "Total": `${curr}${Number(item.total_price).toFixed(2)}`
      }));
    }

    rowsCount.textContent = rows.length;
    colsCount.textContent = columns.length;
    tableModeBadge.textContent = isInvoice ? "Mode: Financial Invoice" : "Mode: Dynamic Table";

    // Build Table Headers
    dynamicThead.innerHTML = `
      <tr>
        <th scope="col" class="py-3 px-3 w-10 text-center uppercase tracking-wider">#</th>
        ${columns.map(col => `
          <th scope="col" class="py-3 px-3.5 uppercase tracking-wider font-semibold whitespace-nowrap">
            ${escapeHtml(col)}
          </th>
        `).join("")}
      </tr>
    `;

    // Build Table Body
    if (rows.length === 0) {
      dynamicTbody.innerHTML = `
        <tr>
          <td colspan="${columns.length + 1}" class="py-8 text-center text-slate-400">
            No rows found in this document.
          </td>
        </tr>
      `;
      return;
    }

    dynamicTbody.innerHTML = rows.map((row, idx) => {
      return `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-2.5 px-3 text-center text-slate-400 font-mono text-[11px]">${idx + 1}</td>
          ${columns.map(col => {
            const rawVal = row[col] !== undefined && row[col] !== null ? String(row[col]) : "";
            const isNumeric = /^-?\$?[\d,]+(\.\d+)?$/.test(rawVal.trim());
            const isDiff = col.toLowerCase().includes("diff") || col.toLowerCase().includes("variance");
            
            let cellClass = "py-2.5 px-3.5 text-slate-700 whitespace-nowrap";
            let formattedContent = escapeHtml(rawVal);

            if (isDiff) {
              if (rawVal.startsWith("-")) {
                formattedContent = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-red-50 text-red-700 border border-red-200">${formattedContent}</span>`;
              } else if (rawVal.startsWith("+")) {
                formattedContent = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">${formattedContent}</span>`;
              } else if (rawVal === "0") {
                formattedContent = `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600">0</span>`;
              }
            } else if (isNumeric) {
              cellClass += " font-mono";
            }

            return `<td class="${cellClass}">${formattedContent}</td>`;
          }).join("")}
        </tr>
      `;
    }).join("");
  }

  // Export CSV Action
  btnExportCsv.addEventListener("click", () => {
    if (!currentDocument || !currentDocument.id) {
      alert("No active document loaded.");
      return;
    }
    // Direct API CSV download matching exact dynamic columns
    window.location.href = `/api/documents/${currentDocument.id}/export-csv`;
  });

  // Sample Loaders
  btnLoadSample.addEventListener("click", async () => {
    try {
      uploadLoading.classList.remove("hidden");
      loadingStatusText.textContent = "Loading and parsing Acme Cloud invoice sample...";

      const sampleResp = await fetch("/static/sample_invoice.pdf");
      if (!sampleResp.ok) throw new Error("Sample invoice file not found");
      const blob = await sampleResp.blob();
      const file = new File([blob], "sample_invoice.pdf", { type: "application/pdf" });

      await uploadFile(file);
    } catch (err) {
      alert("Error loading sample: " + err.message);
      uploadLoading.classList.add("hidden");
    }
  });

  btnLoadAudit.addEventListener("click", async () => {
    try {
      uploadLoading.classList.remove("hidden");
      loadingStatusText.textContent = "Loading and parsing Central Warehouse Stock Audit sheet...";

      const sampleResp = await fetch("/static/sample_stock_audit.pdf");
      if (!sampleResp.ok) throw new Error("Sample stock audit file not found");
      const blob = await sampleResp.blob();
      const file = new File([blob], "sample_stock_audit.pdf", { type: "application/pdf" });

      await uploadFile(file);
    } catch (err) {
      alert("Error loading stock audit: " + err.message);
      uploadLoading.classList.add("hidden");
    }
  });

  // History Modal handlers
  btnToggleHistory.addEventListener("click", () => historyModal.classList.remove("hidden"));
  btnCloseHistory.addEventListener("click", () => historyModal.classList.add("hidden"));
  historyModal.addEventListener("click", (e) => {
    if (e.target === historyModal) historyModal.classList.add("hidden");
  });

  // API Key Modal handlers
  btnConfigKey.addEventListener("click", () => {
    inputGeminiKey.value = geminiApiKey;
    apiKeyModal.classList.remove("hidden");
  });
  btnCloseApiKey.addEventListener("click", () => apiKeyModal.classList.add("hidden"));
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

  // Helper
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
