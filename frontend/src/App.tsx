
import { useState } from "react";
import type { CSSProperties } from "react";
import jsPDF from "jspdf";
import {
  FileText,
  Upload,
  Sparkles,
  BriefcaseBusiness,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  LoaderCircle,
  Target,
  Lightbulb,
  ShieldCheck,
  TrendingUp,
  Download,
} from "lucide-react";
import "./App.css";

interface AnalysisReport {
  score: number;
  quality_score?: number;
  skill_match_score?: number | null;
  score_type: string;
  word_count: number;
  skills: string[];
  sections_found: string[];
  missing_sections: string[];
  strengths: string[];
  improvements: string[];
  job_role: string | null;
  matched_role_skills: string[];
  missing_role_skills: string[];
  note: string;
}

function App() {
  const [resume, setResume] = useState<File | null>(null);
  const [jobRole, setJobRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<AnalysisReport | null>(null);

  async function handleAnalyze() {
    if (!resume) {
      setError("Please upload your resume first.");
      return;
    }

    if (!/\.(pdf|docx)$/i.test(resume.name)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }

    if (resume.size > 5 * 1024 * 1024) {
      setError("File size must be less than 5 MB.");
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const formData = new FormData();
      formData.append("file", resume);
      formData.append("job_role", jobRole);

      const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const response = await fetch(`${API_URL}/analyze`, {
  method: "POST",
  body: formData,
});

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to analyze the resume."
        );
      }

      setReport(data as AnalysisReport);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to the backend. Check that the API is running."
      );
    } finally {
      setLoading(false);
    }
  }

  function resetAnalyzer() {
    setResume(null);
    setJobRole("");
    setReport(null);
    setError("");

    const fileInput = document.getElementById(
      "resume-file"
    ) as HTMLInputElement | null;

    if (fileInput) {
      fileInput.value = "";
    }
  }

  const qualityScore = report
    ? report.quality_score ?? report.score
    : 0;

  function downloadPDFReport() {
    if (!report) return;

    const pdf = new jsPDF();
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 18;
    const contentWidth = pageWidth - margin * 2;
    let y = 20;

    function ensureSpace(requiredHeight = 12) {
      if (y + requiredHeight > pageHeight - 18) {
        pdf.addPage();
        y = 20;
      }
    }

    function addText(
      text: string,
      size = 10,
      bold = false
    ) {
      pdf.setFont("helvetica", bold ? "bold" : "normal");
      pdf.setFontSize(size);

      const lines = pdf.splitTextToSize(text, contentWidth);
      const lineHeight = size * 0.5 + 3;

      for (const line of lines) {
        ensureSpace(lineHeight);
        pdf.text(line, margin, y);
        y += lineHeight;
      }

      y += 2;
    }

    function addSection(title: string, items: string[]) {
      ensureSpace(24);
      y += 4;
      addText(title, 13, true);

      if (items.length === 0) {
        addText("None identified.");
        return;
      }

      items.forEach((item) => {
        addText(`- ${item}`);
      });
    }

    // Report heading
    pdf.setTextColor(90, 55, 190);
    addText("ResumeIQ", 24, true);

    pdf.setTextColor(50, 50, 65);
    addText("AI Resume Analysis Report", 12);

    pdf.setDrawColor(120, 90, 220);
    pdf.line(margin, y, pageWidth - margin, y);
    y += 8;

    // Overview
    addSection("Resume Overview", [
      `Resume Quality Score: ${qualityScore}/100`,
      `Word Count: ${report.word_count}`,
      `Target Job Role: ${report.job_role || "Not specified"}`,
      `Role Skill Match: ${
        report.skill_match_score == null
          ? "Not available for this role"
          : `${report.skill_match_score}%`
      }`,
      `Uploaded File: ${resume?.name || "Resume"}`,
      `Report Date: ${new Date().toLocaleDateString()}`,
    ]);

    // Skills and sections
    addSection("Detected Skills", report.skills);
    addSection("Matched Role Skills", report.matched_role_skills);
    addSection("Missing Role Skills", report.missing_role_skills);
    addSection("Resume Sections Found", report.sections_found);
    addSection("Missing Resume Sections", report.missing_sections);
    addSection("Resume Strengths", report.strengths);
    addSection("Improvement Suggestions", report.improvements);

    if (report.note) {
      addSection("Analysis Note", [report.note]);
    }

    // Footer on every page
    const pageCount = pdf.getNumberOfPages();

    for (let page = 1; page <= pageCount; page++) {
      pdf.setPage(page);
      pdf.setTextColor(110, 110, 125);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(8);

      pdf.text(
        `ResumeIQ | Page ${page} of ${pageCount}`,
        pageWidth / 2,
        pageHeight - 8,
        { align: "center" }
      );
    }

    pdf.save("ResumeIQ-Analysis-Report.pdf");
  }

  return (
    <div className="app">
      <nav className="navbar">
        <h2>
          <Sparkles size={23} />
          ResumeIQ
        </h2>

        <span>Resume Analyzer</span>
      </nav>

      <main className={`hero ${report ? "hero-report" : ""}`}>
        {!report ? (
          <>
            <div className="tag">
              <Sparkles size={16} />
              Smart Resume Analysis
            </div>

            <h1>
              Make Your Resume
              <br />
              <span>Stand Out.</span>
            </h1>

            <p className="subtitle">
              Analyze your resume, discover missing skills,
              and get actionable suggestions to improve your
              resume.
            </p>

            <section className="upload-card">
              <h2>Analyze Your Resume</h2>
              <p>Upload your resume to get started.</p>

              <label
                className="upload-area"
                htmlFor="resume-file"
              >
                <Upload size={35} />

                <strong>
                  {resume
                    ? resume.name
                    : "Click to upload your resume"}
                </strong>

                <span>PDF or DOCX · Maximum 5 MB</span>

                <input
                  id="resume-file"
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(event) => {
                    setResume(
                      event.target.files?.[0] ?? null
                    );
                    setError("");
                  }}
                />
              </label>

              <label
                className="field-label"
                htmlFor="jobRole"
              >
                <BriefcaseBusiness size={18} />
                Target Job Role (Optional)
              </label>

              <input
                id="jobRole"
                className="role-input"
                type="text"
                placeholder="e.g. Python Developer, DevOps Engineer"
                value={jobRole}
                onChange={(event) =>
                  setJobRole(event.target.value)
                }
              />

              {error && (
                <div
                  className="analysis-error"
                  role="alert"
                >
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </div>
              )}

              <button
                className="analyze-btn"
                onClick={handleAnalyze}
                disabled={loading}
                type="button"
              >
                {loading ? (
                  <>
                    <LoaderCircle
                      className="spin"
                      size={18}
                    />
                    Analyzing Resume...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Analyze Resume
                  </>
                )}
              </button>

              <div className="privacy">
                <ShieldCheck size={16} />
                Resume content is processed for analysis.
              </div>
            </section>

            <div className="features">
              <div>
                <CheckCircle2 size={15} />
                Resume Quality Score
              </div>

              <div>
                <CheckCircle2 size={15} />
                Skills Analysis
              </div>

              <div>
                <CheckCircle2 size={15} />
                Improvement Tips
              </div>
            </div>
          </>
        ) : (
          <section className="report-card">
            <div className="report-header">
              <div>
                <div className="tag">
                  <Sparkles size={16} />
                  Analysis Complete
                </div>

                <h1 className="report-title">
                  Your Resume Report
                </h1>

                <p className="report-filename">
                  <FileText size={15} />
                  {resume?.name}
                </p>
              </div>

              <div className="report-actions">
                <button
                  className="download-btn"
                  onClick={downloadPDFReport}
                  type="button"
                >
                  <Download size={16} />
                  Download PDF
                </button>

                <button
                  className="back-btn"
                  onClick={resetAnalyzer}
                  type="button"
                >
                  <ArrowLeft size={16} />
                  New Analysis
                </button>
              </div>
            </div>

            <div className="score-grid">
              <div className="score-panel">
                <div
                  className="score-circle"
                  style={
                    {
                      "--score-angle": `${qualityScore * 3.6}deg`,
                    } as CSSProperties
                  }
                >
                  <div className="score-circle-inner">
                    <strong>{qualityScore}</strong>
                    <span>/ 100</span>
                  </div>
                </div>

                <div className="score-description">
                  <h2>Resume Quality</h2>
                  <p>
                    Checks resume content, detected skills,
                    sections, and basic information.
                  </p>

                  <span className="word-count">
                    {report.word_count} words detected
                  </span>
                </div>
              </div>

              {report.skill_match_score !== null &&
                report.skill_match_score !== undefined && (
                  <div className="score-panel role-score-panel">
                    <div
                      className="score-circle role-score-circle"
                      style={
                        {
                          "--score-angle": `${
                            report.skill_match_score * 3.6
                          }deg`,
                        } as CSSProperties
                      }
                    >
                      <div className="score-circle-inner">
                        <strong>
                          {report.skill_match_score}
                        </strong>
                        <span>/ 100</span>
                      </div>
                    </div>

                    <div className="score-description">
                      <h2>Role Skill Match</h2>
                      <p>
                        Measures how many expected skills for
                        your selected role were detected.
                      </p>

                      <span className="word-count">
                        {report.matched_role_skills.length} of{" "}
                        {report.matched_role_skills.length +
                          report.missing_role_skills.length}{" "}
                        expected skills found
                      </span>
                    </div>
                  </div>
                )}
            </div>

            <div className="report-grid">
              <div className="report-section">
                <h3>
                  <CheckCircle2 size={18} />
                  Detected Skills
                </h3>

                <div className="skill-list">
                  {report.skills.length ? (
                    report.skills.map((skill) => (
                      <span
                        className="skill-chip"
                        key={skill}
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <p>
                      No listed technical skills were detected.
                    </p>
                  )}
                </div>
              </div>

              <div className="report-section">
                <h3>
                  <FileText size={18} />
                  Resume Sections
                </h3>

                <div className="skill-list">
                  {report.sections_found.map((section) => (
                    <span
                      className="skill-chip"
                      key={section}
                    >
                      <CheckCircle2 size={13} />
                      {section}
                    </span>
                  ))}

                  {report.missing_sections.map((section) => (
                    <span
                      className="skill-chip missing-chip"
                      key={section}
                    >
                      <AlertCircle size={13} />
                      {section}
                    </span>
                  ))}
                </div>
              </div>

              {report.job_role &&
                report.job_role !== "Not specified" && (
                  <div className="report-section">
                    <h3>
                      <Target size={18} />
                      Target Role: {report.job_role}
                    </h3>

                    <p className="section-caption">
                      Matching skills
                    </p>

                    <div className="skill-list">
                      {report.matched_role_skills.length ? (
                        report.matched_role_skills.map(
                          (skill) => (
                            <span
                              className="skill-chip matched-chip"
                              key={skill}
                            >
                              <CheckCircle2 size={13} />
                              {skill}
                            </span>
                          )
                        )
                      ) : (
                        <p>
                          No expected role skills were detected.
                        </p>
                      )}
                    </div>

                    <p className="section-caption">
                      Skills to consider
                    </p>

                    <div className="skill-list">
                      {report.missing_role_skills.length ? (
                        report.missing_role_skills.map(
                          (skill) => (
                            <span
                              className="skill-chip missing-chip"
                              key={skill}
                            >
                              <AlertCircle size={13} />
                              {skill}
                            </span>
                          )
                        )
                      ) : (
                        <p>
                          No listed skill gaps for this role.
                        </p>
                      )}
                    </div>
                  </div>
                )}

              <div className="report-section">
                <h3>
                  <TrendingUp size={18} />
                  Strengths
                </h3>

                {report.strengths.length ? (
                  <ul>
                    {report.strengths.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    Review your resume content to identify
                    strengths.
                  </p>
                )}
              </div>

              <div className="report-section">
                <h3>
                  <Lightbulb size={18} />
                  Improvement Suggestions
                </h3>

                {report.improvements.length ? (
                  <ul>
                    {report.improvements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    No basic content suggestions were generated.
                  </p>
                )}
              </div>
            </div>

            <p className="report-note">{report.note}</p>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
