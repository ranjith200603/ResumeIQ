import re
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from docx import Document
from pypdf import PdfReader


app = FastAPI(
    title="ResumeIQ API",
    description="Resume quality checks and job-role skill matching",
    version="3.0.0",
)

# Keep the existing deployed frontend and local development origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://resume-iq-nu-sooty.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_PDF_PAGES = 50

# Canonical skill names and commonly used resume variations.
SKILL_ALIASES = {
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "java script"],
    "TypeScript": ["typescript", "type script"],
    "React": ["react", "react.js", "reactjs"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Express.js": ["express.js", "expressjs", "express js"],
    "SQL": ["sql"],
    "MySQL": ["mysql", "my sql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb", "mongo db"],
    "FastAPI": ["fastapi", "fast api"],
    "Django": ["django"],
    "Flask": ["flask"],
    "REST API": ["rest api", "restful api", "rest apis"],
    "GraphQL": ["graphql"],
    "HTML": ["html"],
    "CSS": ["css"],
    "Tailwind CSS": ["tailwind css", "tailwind"],
    "Bootstrap": ["bootstrap"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["microsoft azure", "azure"],
    "Google Cloud": ["google cloud", "gcp"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Jenkins": ["jenkins"],
    "GitHub Actions": ["github actions"],
    "GitLab CI/CD": ["gitlab ci", "gitlab ci/cd"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "Linux": ["linux"],
    "Bash": ["bash", "shell scripting"],
    "Git": ["git"],
    "GitHub": ["github"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "DevOps": ["devops", "dev ops"],
    "Python Automation": ["python automation"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "Natural Language Processing": [
        "natural language processing",
        "nlp",
    ],
    "Data Analysis": ["data analysis", "data analytics"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Power BI": ["power bi"],
    "Tableau": ["tableau"],
    "Excel": ["microsoft excel", "excel"],
    "n8n": ["n8n"],
    "OpenAI API": ["openai api"],
    "Figma": ["figma"],
    "Agile": ["agile"],
    "Communication": ["communication"],
}

# Skills used for each supported target role.
ROLE_SKILLS = {
    "python developer": [
        "Python", "FastAPI", "Django", "SQL", "Git",
    ],
    "python": [
        "Python", "FastAPI", "Django", "SQL", "Git",
    ],
    "backend developer": [
        "Python", "FastAPI", "SQL", "REST API", "Git",
    ],
    "devops engineer": [
        "Linux", "Docker", "Kubernetes", "Jenkins",
        "AWS", "CI/CD", "Git",
    ],
    "devops": [
        "Linux", "Docker", "Kubernetes", "Jenkins",
        "AWS", "CI/CD", "Git",
    ],
    "cloud engineer": [
        "Linux", "AWS", "Azure", "Docker", "Terraform", "Git",
    ],
    "frontend developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React",
    ],
    "frontend": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React",
    ],
    "full stack developer": [
        "HTML", "CSS", "JavaScript", "React", "Node.js", "SQL",
    ],
    "data analyst": [
        "SQL", "Python", "Power BI", "Data Analysis", "Excel",
    ],
    "machine learning engineer": [
        "Python", "Machine Learning", "Deep Learning", "SQL",
    ],
    "machine learning": [
        "Python", "Machine Learning", "Deep Learning", "SQL",
    ],
    "ai automation engineer": [
        "Python", "n8n", "REST API", "SQL", "Git",
    ],
    "automation engineer": [
        "Python", "REST API", "Git", "Linux",
    ],
}


def normalize_text(text: str) -> str:
    """Normalize whitespace and case for reliable matching."""
    return re.sub(r"\s+", " ", text).strip().lower()


def contains_term(text: str, term: str) -> bool:
    """Match a complete term instead of an unrelated substring."""
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def extract_text(filename: str, content: bytes) -> str:
    """Extract readable text from PDF or DOCX resumes."""
    extension = filename.lower().rsplit(".", 1)[-1]

    try:
        if extension == "pdf":
            reader = PdfReader(BytesIO(content), strict=False)

            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "This PDF is password-protected. "
                                "Upload an unlocked PDF."
                            ),
                        )
                except HTTPException:
                    raise
                except Exception as exc:
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to open the protected PDF.",
                    ) from exc

            if len(reader.pages) > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"PDF contains too many pages. "
                        f"Maximum supported: {MAX_PDF_PAGES}."
                    ),
                )

            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        if extension == "docx":
            document = Document(BytesIO(content))
            parts = [
                paragraph.text
                for paragraph in document.paragraphs
            ]

            # Include content stored inside Word tables.
            for table in document.tables:
                for row in table.rows:
                    parts.append(
                        " ".join(cell.text for cell in row.cells)
                    )

            return "\n".join(parts)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not read this resume. "
                "Please upload a valid text-based PDF or DOCX."
            ),
        ) from exc

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Upload a PDF or DOCX file.",
    )


def detect_skills(text: str) -> list[str]:
    """Return canonical skill names detected in resume text."""
    found = []
    normalized = normalize_text(text)

    for canonical_name, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if contains_term(normalized, alias):
                found.append(canonical_name)
                break

    return found


def detect_sections(text: str) -> list[str]:
    """Detect common resume sections from their headings."""
    section_patterns = {
        "Education": [
            r"education",
            r"academic background",
            r"educational qualifications?",
            r"qualifications?",
        ],
        "Skills": [
            r"skills",
            r"technical skills",
            r"core competencies",
            r"key skills",
            r"technologies",
        ],
        "Projects": [
            r"projects",
            r"personal projects",
            r"academic projects",
            r"project experience",
        ],
        "Experience": [
            r"experience",
            r"work experience",
            r"professional experience",
            r"internships?",
            r"employment history",
        ],
        "Certifications": [
            r"certifications?",
            r"certificates",
            r"courses",
            r"licenses",
        ],
    }

    # Match headings line by line to reduce accidental matches
    # inside ordinary sentences.
    lines = [
        re.sub(r"\s+", " ", line).strip().lower()
        for line in text.splitlines()
        if line.strip()
    ]

    found = []

    for section, patterns in section_patterns.items():
        for line in lines:
            cleaned_line = re.sub(r"^[\W_]+|[\W_]+$", "", line)

            # Headings may include a short suffix, such as a colon
            # or a count, but should not be full paragraphs.
            if len(cleaned_line) > 90:
                continue

            if any(
                re.match(
                    r"^\s*" + pattern + r"(?:\s*[:|\-–—]?\s*)$",
                    cleaned_line,
                    re.IGNORECASE,
                )
                for pattern in patterns
            ):
                found.append(section)
                break

    return found


def analyze_text(text: str, job_role: str) -> dict:
    """Analyze resume quality and match skills to a known role."""
    word_count = len(re.findall(r"\b[\w+#./-]+\b", text))
    normalized_text = normalize_text(text)

    email_found = bool(
        re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text,
            re.IGNORECASE,
        )
    )

    # Check for a plausible phone number with 8 to 15 digits.
    phone_found = any(
        8 <= len(re.sub(r"\D", "", match)) <= 15
        for match in re.findall(
            r"(?<!\w)\+?\d[\d\s().-]{6,}\d(?!\w)",
            text,
        )
    )

    date_found = bool(
        re.search(
            r"\b(?:19|20)\d{2}\b|"
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]*\.?\s+\d{4}\b",
            text,
            re.IGNORECASE,
        )
    )

    quantified_achievement = bool(
        re.search(
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:%|percent|users|customers|projects|hours|"
            r"days|weeks|months|years|requests|seconds)\b",
            text,
            re.IGNORECASE,
        )
    )

    found_skills = detect_skills(text)
    sections_found = detect_sections(text)

    all_sections = [
        "Education",
        "Skills",
        "Projects",
        "Experience",
        "Certifications",
    ]

    missing_sections = [
        section
        for section in all_sections
        if section not in sections_found
    ]

    # Transparent resume-quality checklist, not a hiring prediction.
    score_breakdown = {
        "sections": min(len(sections_found) * 7, 35),
        "skills": min(len(found_skills) * 2, 25),
        "email": 10 if email_found else 0,
        "phone": 5 if phone_found else 0,
        "length": (
            10 if 100 <= word_count <= 1000
            else 5 if word_count > 0
            else 0
        ),
        "dates": 5 if date_found else 0,
        "measurable_achievements": (
            10 if quantified_achievement else 0
        ),
    }

    quality_score = min(sum(score_breakdown.values()), 100)

    # Normalize common role-name variations.
    normalized_role = normalize_text(job_role)
    role_aliases = {
        "frontend developer": "frontend developer",
        "front end developer": "frontend developer",
        "front-end developer": "frontend developer",
        "devops engineer": "devops engineer",
        "devops": "devops",
        "cloud engineer": "cloud engineer",
        "fullstack developer": "full stack developer",
        "full stack developer": "full stack developer",
        "ai automation": "ai automation engineer",
        "ai automation engineer": "ai automation engineer",
        "automation engineer": "automation engineer",
        "backend developer": "backend developer",
        "back end developer": "backend developer",
        "python developer": "python developer",
        "data analyst": "data analyst",
        "machine learning engineer": "machine learning engineer",
    }

    role_key = role_aliases.get(
        normalized_role,
        normalized_role,
    )
    expected_skills = ROLE_SKILLS.get(role_key, [])

    matched_role_skills = [
        skill for skill in expected_skills
        if skill in found_skills
    ]
    missing_role_skills = [
        skill for skill in expected_skills
        if skill not in matched_role_skills
    ]

    if expected_skills:
        skill_match_score = round(
            len(matched_role_skills)
            / len(expected_skills)
            * 100
        )
    else:
        skill_match_score = None

    strengths = []
    improvements = []

    if email_found:
        strengths.append("An email address was detected.")
    else:
        improvements.append(
            "Add a professional email address to your resume."
        )

    if phone_found:
        strengths.append("A possible contact phone number was detected.")
    else:
        improvements.append(
            "Consider adding a contact phone number."
        )

    if "Education" in sections_found:
        strengths.append("An Education section was detected.")
    else:
        improvements.append(
            "Add a clearly labelled Education section."
        )

    if "Skills" in sections_found and found_skills:
        strengths.append(
            "A Skills section and technical skills were detected."
        )
    elif not found_skills:
        improvements.append(
            "Add relevant technical skills that you actually know."
        )
    else:
        improvements.append(
            "Add a clearly labelled Skills section."
        )

    if "Projects" in sections_found:
        strengths.append("A Projects section was detected.")
    else:
        improvements.append(
            "Add relevant projects and explain your contribution."
        )

    if "Experience" in sections_found:
        strengths.append(
            "An Experience or internship section was detected."
        )
    else:
        improvements.append(
            "If applicable, add internships, work experience, "
            "or practical experience."
        )

    if "Certifications" not in sections_found:
        improvements.append(
            "Add relevant certifications or courses if you have them."
        )

    if not date_found:
        improvements.append(
            "Include relevant dates for education, projects, "
            "certifications, or experience."
        )

    if not quantified_achievement:
        improvements.append(
            "Where accurate, include measurable project outcomes "
            "or results."
        )

    if expected_skills and missing_role_skills:
        improvements.append(
            "For your target role, consider demonstrating these skills: "
            + ", ".join(missing_role_skills)
            + ". Only list skills you genuinely know."
        )

    if word_count < 100:
        improvements.append(
            "The extracted text is short. Check that your resume "
            "contains all pages and selectable text."
        )

    if word_count > 1000:
        improvements.append(
            "Consider removing repetitive content and keeping "
            "the resume concise and relevant."
        )

    if not improvements:
        improvements.append(
            "Keep your resume updated with relevant, accurate "
            "skills and project outcomes."
        )

    return {
        # Preserve the fields expected by the current frontend.
        "score": quality_score,
        "quality_score": quality_score,
        "skill_match_score": skill_match_score,
        "score_type": "rule-based estimate",
        "word_count": word_count,
        "skills": found_skills,
        "sections_found": sections_found,
        "missing_sections": missing_sections,
        "strengths": strengths,
        "improvements": improvements,
        "job_role": job_role.strip() or "Not specified",
        "matched_role_skills": matched_role_skills,
        "missing_role_skills": missing_role_skills,
        "note": (
            "Scores are rule-based guidance, not an official ATS score "
            "or a prediction of hiring success. Results depend on the "
            "text extracted from your resume and the supported skill list."
        ),
        # Additional optional data for future improvements.
        "score_breakdown": score_breakdown,
        "email_detected": email_found,
        "phone_detected": phone_found,
        "date_detected": date_found,
        "measurable_achievement_detected": quantified_achievement,
        "detected_sections_count": len(sections_found),
    }


@app.get("/")
def home():
    return {
        "message": "ResumeIQ API is running",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ResumeIQ API",
    }


@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_role: str = Form(""),
):
    filename = file.filename or ""

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a resume file.",
        )

    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX resume.",
        )

    try:
        # Read only up to the allowed limit plus one byte.
        content = await file.read(MAX_FILE_SIZE + 1)
    finally:
        await file.close()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum size is 5 MB.",
        )

    text = extract_text(filename, content)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text was found. Try a text-based PDF "
                "or DOCX. Scanned image-only PDFs are not supported."
            ),
        )

    return analyze_text(text, job_role)
