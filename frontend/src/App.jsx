import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "/api";
const STORAGE_KEY = "brochure-generator-session";
const TAB_MARKER_KEY = "brochure-generator-active-tab";
const NOT_FOUND_MESSAGE = "Information not found on the website.";

const TEMPLATE_OPTIONS = [
  { value: "corporate", label: "Template 1 - Corporate" },
  { value: "modern", label: "Template 2 - Modern" },
  { value: "minimal", label: "Template 3 - Minimal" },
  { value: "executive", label: "Template 4 - Executive" },
];

const LOADING_STEPS = [
  "Crawling website...",
  "Extracting content...",
  "Generating brochure...",
  "Creating PDF...",
];

const EMPTY_STATUS = { msg: "", type: "" };

function safeString(value, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function safeArray(value, fallback = []) {
  return Array.isArray(value) ? value.filter(item => typeof item === "string") : fallback;
}

function normalizeBrochure(raw) {
  if (!raw || typeof raw !== "object") return null;

  const contact = raw.contact && typeof raw.contact === "object" ? raw.contact : {};
  const traceability = raw.traceability && typeof raw.traceability === "object" ? raw.traceability : {};

  return {
    ...raw,
    company_name: safeString(raw.company_name, "Unknown Company"),
    overview: safeString(raw.overview, NOT_FOUND_MESSAGE),
    services: safeArray(raw.services),
    products: safeArray(raw.products),
    industries: safeArray(raw.industries),
    generated_at: safeString(raw.generated_at, ""),
    template_used: safeString(raw.template_used, "corporate"),
    pdf_data: safeString(raw.pdf_data, ""),
    pdf_available: Boolean(raw.pdf_available),
    generation_time: typeof raw.generation_time === "number" ? raw.generation_time : 0,
    contact: {
      emails: safeArray(contact.emails, [NOT_FOUND_MESSAGE]),
      phones: safeArray(contact.phones, [NOT_FOUND_MESSAGE]),
    },
    traceability: {
      overview: safeArray(traceability.overview),
      services: safeArray(traceability.services),
      products: safeArray(traceability.products),
      industries: safeArray(traceability.industries),
      contact: safeArray(traceability.contact),
    },
  };
}

function createPdfBlob(pdfData) {
  if (!pdfData) return null;
  const bytes = atob(pdfData);
  const arr = new Uint8Array([...bytes].map(char => char.charCodeAt(0)));
  return new Blob([arr], { type: "application/pdf" });
}

function templateClass(templateUsed) {
  return `theme-${templateUsed || "corporate"}`;
}

function normalizeList(items) {
  return Array.isArray(items) && items.length ? items : [NOT_FOUND_MESSAGE];
}

export default function App() {
  const [url, setUrl] = useState("");
  const [template, setTemplate] = useState("corporate");
  const [status, setStatus] = useState(EMPTY_STATUS);
  const [loading, setLoading] = useState(false);
  const [progressIndex, setProgressIndex] = useState(0);
  const [brochure, setBrochure] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const progressTimerRef = useRef(null);

  useEffect(() => {
    const navigationEntry = performance.getEntriesByType("navigation")[0];
    const isReload = navigationEntry?.type === "reload";
    if (!isReload && !sessionStorage.getItem(TAB_MARKER_KEY)) {
      localStorage.removeItem(STORAGE_KEY);
    }
    sessionStorage.setItem(TAB_MARKER_KEY, "1");

    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved);
      const normalizedBrochure = normalizeBrochure(parsed.brochure);
      setUrl(safeString(parsed.url, ""));
      setTemplate(safeString(parsed.template, "corporate"));
      setBrochure(normalizedBrochure);
      setPdfBlob(createPdfBlob(normalizedBrochure?.pdf_data));
      if (normalizedBrochure) {
        setStatus({ msg: "Restored your last generated brochure.", type: "ok" });
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => () => {
    sessionStorage.removeItem(TAB_MARKER_KEY);
  }, []);

  useEffect(() => {
    if (!loading) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
      return undefined;
    }

    setProgressIndex(0);
    progressTimerRef.current = window.setInterval(() => {
      setProgressIndex(current => {
        if (current >= LOADING_STEPS.length - 1) return current;
        return current + 1;
      });
    }, 1800);

    return () => {
      window.clearInterval(progressTimerRef.current);
    };
  }, [loading]);

  function persistSession(nextUrl, nextTemplate, nextBrochure) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        url: nextUrl,
        template: nextTemplate,
        brochure: nextBrochure,
      }),
    );
  }

  function clearSession() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function setMsg(msg, type = "") {
    setStatus({ msg, type });
  }

  async function handleGenerate() {
    const trimmed = safeString(url).trim();
    if (!trimmed) {
      setMsg("Please enter a website URL.", "error");
      return;
    }
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
      setMsg("URL must start with http:// or https://", "error");
      return;
    }

    clearSession();
    setLoading(true);
    setBrochure(null);
    setPdfBlob(null);
    setMsg(LOADING_STEPS[0], "loading");

    try {
      const resp = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmed, template }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${resp.status}`);
      }

      const data = normalizeBrochure(await resp.json());
      setBrochure(data);
      setPdfBlob(createPdfBlob(data?.pdf_data));
      persistSession(trimmed, template, data);
      setMsg("Brochure generated successfully.", "ok");
    } catch (error) {
      setMsg(error.message || "Something went wrong.", "error");
    } finally {
      setLoading(false);
    }
  }

  function handleGenerateAnother() {
    setUrl("");
    setTemplate("corporate");
    setBrochure(null);
    setPdfBlob(null);
    setStatus(EMPTY_STATUS);
    clearSession();
  }

  function downloadPDF() {
    if (!pdfBlob || !brochure) {
      setMsg("PDF not available.", "error");
      return;
    }
    const safeName = (brochure.company_name || "company").replace(/[^\w-]+/g, "_");
    const href = URL.createObjectURL(pdfBlob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${safeName}_brochure.pdf`;
    link.click();
    URL.revokeObjectURL(href);
  }

  function renderList(items) {
    const values = normalizeList(items);
    if (values.length === 1 && values[0] === NOT_FOUND_MESSAGE) {
      return <p className="empty-state">{NOT_FOUND_MESSAGE}</p>;
    }
    return (
      <ul className="fact-list">
        {values.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    );
  }

  const activeStep = loading ? LOADING_STEPS[progressIndex] : status.msg;
  const progressValue = loading ? ((progressIndex + 1) / LOADING_STEPS.length) * 100 : brochure ? 100 : 0;

  return (
    <div className={`app-shell ${templateClass(brochure?.template_used || template)}`}>
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 16 16"><path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z" /></svg>
        </div>
        <div className="brand-copy">
          <span className="brand-title">BrochureAI</span>
          <span className="brand-subtitle">Grounded website brochures</span>
        </div>
      </header>

      <main className="page">
        <section className="hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Website crawl to PDF brochure</p>
            <h1>Generate clean company brochures without made-up details.</h1>
            <p className="hero-text">
              The pipeline now favors extracted evidence over assumptions, so missing data stays explicit instead of
              turning into hallucinated copy.
            </p>
          </div>

          <div className="control-card">
            <label className="field">
              <span>Website URL</span>
              <input
                className="url-input"
                type="url"
                placeholder="https://company.com"
                value={url}
                onChange={event => setUrl(event.target.value)}
                onKeyDown={event => event.key === "Enter" && handleGenerate()}
                disabled={loading}
              />
            </label>

            <label className="field">
              <span>Brochure template</span>
              <select
                className="template-select"
                value={template}
                onChange={event => setTemplate(event.target.value)}
                disabled={loading}
              >
                {TEMPLATE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <div className="action-row">
              <button className="primary-btn" onClick={handleGenerate} disabled={loading}>
                {loading ? "Generating..." : "Generate brochure"}
              </button>
              {brochure && (
                <button className="secondary-btn" onClick={handleGenerateAnother}>
                  Generate Another Brochure
                </button>
              )}
            </div>

            <div className="status-panel" aria-live="polite">
              <div className="progress-track">
                <div className="progress-bar" style={{ width: `${progressValue}%` }} />
              </div>
              <div className="status-row">
                <span className={`status-pill ${status.type}`}>{activeStep || "Ready to generate"}</span>
                {loading && <span className="status-step">{progressIndex + 1} / {LOADING_STEPS.length}</span>}
              </div>
            </div>
          </div>
        </section>

        {brochure && (
          <section className="results-panel">
            <div className="results-header">
              <div>
                <p className="results-kicker">{TEMPLATE_OPTIONS.find(item => item.value === brochure.template_used)?.label}</p>
                <h2>{brochure.company_name}</h2>
              </div>
              <div className="results-meta">
                <span>Generated {brochure.generated_at}</span>
                <span>Generated in {brochure.generation_time} seconds</span>
              </div>
            </div>

            <div className="results-grid">
              <article className="section-card section-card-wide">
                <h3>Company Overview</h3>
                <p>{brochure.overview || NOT_FOUND_MESSAGE}</p>
              </article>

              <article className="section-card">
                <h3>Services</h3>
                {renderList(brochure.services)}
              </article>

              <article className="section-card">
                <h3>Products</h3>
                {renderList(brochure.products)}
              </article>

              <article className="section-card">
                <h3>Industries</h3>
                {renderList(brochure.industries)}
              </article>

              <article className="section-card">
                <h3>Contact Information</h3>
                <div className="contact-block">
                  <div>
                    <h4>Emails</h4>
                    {renderList(brochure.contact?.emails)}
                  </div>
                  <div>
                    <h4>Phones</h4>
                    {renderList(brochure.contact?.phones)}
                  </div>
                </div>
              </article>

              <article className="section-card section-card-wide">
                <h3>Traceability</h3>
                <div className="trace-grid">
                  {Object.entries(brochure.traceability || {}).map(([section, pages]) => (
                    <div key={section} className="trace-item">
                      <h4>{section}</h4>
                      {Array.isArray(pages) && pages.length ? (
                        <ul className="trace-list">
                          {pages.map(page => (
                            <li key={page}>{page}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="empty-state">{NOT_FOUND_MESSAGE}</p>
                      )}
                    </div>
                  ))}
                </div>
              </article>
            </div>

            <div className="footer-actions">
              <button className="primary-btn" onClick={downloadPDF}>Download PDF</button>
              <span className="pdf-note">{brochure.pdf_available ? "PDF ready for download." : "PDF unavailable."}</span>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
