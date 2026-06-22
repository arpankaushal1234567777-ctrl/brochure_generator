import { useState } from "react";
const API_BASE = "/api";

export default function App() {
  const [url, setUrl]           = useState("");
  const [status, setStatus]     = useState({ msg: "", type: "" });
  const [loading, setLoading]   = useState(false);
  const [brochure, setBrochure] = useState(null);
  const [pdfBlob, setPdfBlob]   = useState(null);

  function setMsg(msg, type = "") {
    setStatus({ msg, type });
  }

  async function handleGenerate() {
    const trimmed = url.trim();
    if (!trimmed) { setMsg("Please enter a website URL.", "error"); return; }
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
      setMsg("URL must start with http:// or https://", "error"); return;
    }

    setLoading(true);
    setBrochure(null);
    setPdfBlob(null);
    setMsg("Crawling website and discovering links…", "loading");

    try {
      const resp = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmed }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${resp.status}`);
      }

      const data = await resp.json();

      if (data.pdf_data) {
        const bytes = atob(data.pdf_data);
        const arr   = new Uint8Array([...bytes].map(c => c.charCodeAt(0)));
        setPdfBlob(new Blob([arr], { type: "application/pdf" }));
      }

      setBrochure(data);
      setMsg("Brochure generated successfully.", "ok");
    } catch (e) {
      setMsg(e.message || "Something went wrong.", "error");
    } finally {
      setLoading(false);
    }
  }

  function fillSection(text) {
    if (!text || !text.trim()) {
      return <p className="b-card-empty">No data found for this section.</p>;
    }
    const lines = text.split("\n").filter(l => l.trim());
    const isList = lines.some(l => l.trim().startsWith("- ") || l.trim().startsWith("• "));
    if (isList) {
      return (
        <ul>
          {lines
            .filter(l => l.trim().startsWith("- ") || l.trim().startsWith("• "))
            .map((l, i) => <li key={i}>{l.replace(/^[-•]\s*/, "")}</li>)}
        </ul>
      );
    }
    return <p dangerouslySetInnerHTML={{ __html: text.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br/>") }} />;
  }

  function downloadJSON() {
    if (!brochure) return;
    const blob = new Blob([JSON.stringify(brochure, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${(brochure.company_name || "brochure").replace(/\s+/g, "_")}.json`;
    a.click();
  }

  function downloadPDF() {
    if (!pdfBlob) { setMsg("PDF not available.", "error"); return; }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(pdfBlob);
    a.download = `${(brochure?.company_name || "brochure").replace(/\s+/g, "_")}.pdf`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function copyJSON() {
    if (!brochure) return;
    navigator.clipboard.writeText(JSON.stringify(brochure, null, 2))
      .then(() => setMsg("JSON copied to clipboard.", "ok"))
      .catch(() => setMsg("Copy failed — try manually.", "error"));
  }

  const contact = brochure?.contact || {};

  return (
    <>
      <header>
        <div className="logo-mark">
          <svg viewBox="0 0 16 16"><path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z"/></svg>
        </div>
        <span className="logo-text">Brochure<span>AI</span></span>
      </header>

      <section className="hero">
        <span className="hero-eyebrow">AI-Powered · Instant</span>
        <h1>Turn any website into a<br/><em>company brochure</em></h1>
        <p className="hero-sub">
          Paste a URL. We crawl the site, extract the right pages, and generate
          a structured brochure — ready in seconds.
        </p>
      </section>

      <div className="input-card">
        <div className="input-row">
          <input
            className="url-input"
            type="url"
            placeholder="https://company.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleGenerate()}
            autoComplete="off"
            spellCheck="false"
          />
          <button
            className="btn-generate"
            onClick={handleGenerate}
            disabled={loading}
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path d="M5 12h14M13 6l6 6-6 6"/>
            </svg>
            Generate
          </button>
        </div>

        {status.msg && (
          <div id="status">
            {status.type === "loading" && <div className="spinner"/>}
            <span className={
              status.type === "error" ? "status-error" :
              status.type === "ok"    ? "status-ok"    : ""
            }>
              {status.type === "error" ? `✕ ${status.msg}` :
               status.type === "ok"   ? `✓ ${status.msg}` : status.msg}
            </span>
          </div>
        )}
      </div>

      {brochure && (
        <section id="output">
          <div className="brochure-header">
            <div className="brochure-company">{brochure.company_name || "Unknown Company"}</div>
            <div className="brochure-meta">Generated {new Date().toLocaleString()}</div>
          </div>

          <div className="brochure-grid">
            <div className="b-card card-span2">
              <div className="b-card-label">Company Overview</div>
              {fillSection(brochure.overview)}
            </div>

            <div className="b-card card-span2">
              <div className="b-card-label">Products &amp; Services</div>
              {fillSection(brochure.offerings)}
            </div>

            <div className="b-card">
              <div className="b-card-label">Industry &amp; Sectors</div>
              {fillSection(brochure.industry)}
            </div>

            <div className="b-card">
              <div className="b-card-label">Contact</div>
              {contact.emails?.length || contact.phones?.length ? (
                <div className="contact-chips">
                  {(contact.emails || []).map((e, i) => (
                    <span key={i} className="chip">✉ {e}</span>
                  ))}
                  {(contact.phones || []).map((p, i) => (
                    <span key={i} className="chip">📞 {p}</span>
                  ))}
                </div>
              ) : (
                <p className="b-card-empty">No contact info found.</p>
              )}
            </div>
          </div>

          <div className="brochure-actions">
            <button className="btn-secondary" onClick={copyJSON}>Copy JSON</button>
            <button className="btn-secondary" onClick={downloadJSON}>Download JSON</button>
            <button className="btn-primary"   onClick={downloadPDF}>Download PDF</button>
          </div>
        </section>
      )}

      <footer/>
    </>
  );
}