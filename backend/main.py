
import re
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from docx import Document
from pypdf import PdfReader


app = FastAPI(title="ResumeIQ API", version="2.0.0")

# Allow the local development frontend and deployed Vercel frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://resume-iq-nu-sooty.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024

SKILLS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "SQL",
    "MongoDB",
    "FastAPI",
    "Django",
    "AWS",
    "Azure",
    "Docker",
    "Kubernetes",
    "Jenkins",
    "Linux",
    "Git",
    "GitHub",
    "CI/CD",
    "DevOps",
    "Machine Learning",
    "Deep Learning",
    "Data Analysis",
    "HTML",
    "CSS",
    "REST API",
    "n8n",
    "Power BI",
]

ROLE_SKILLS = {
    "python developer": [
        "Python", "FastAPI", "Django", "SQL", "Git"
    ],
    "python": [
        "Python", "FastAPI", "Django", "SQL", "Git"
    ],
    "devops engineer": [
        "Linux", "Docker", "Kubernetes", "Jenkins", "AWS", "CI/CD"
    ],
    "devops": [
        "Linux", "Docker", "Kubernetes", "Jenkins", "AWS", "CI/CD"
    ],
    "frontend developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React"
    ],
    "frontend": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React"
    ],
    "data analyst": [
        "SQL", "Python", "Power BI", "Data Analysis"
    ],
    "machine learning engineer": [
        "Python", "Machine Learning", "Deep Learning", "SQL"
    ],
    "machine learning": [
        "Python", "Machine Learning", "Deep Learning", "SQL"
    ],
    "full stack developer": [
        "HTML", "CSS", "JavaScript", "React", "Node.js", "SQL"
    ],
    "ai automation engineer": [
        "Python", "n8n", "REST API", "SQL", "Git"
    ],
}


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from a PDF or DOCX resume."""
    extension = filename.lower().rsplit(".", 1)[-1]

    try:
        if extension == "pdf":
            reader = PdfReader(BytesIO(content))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )

        if extension == "docx":
            document = Document(BytesIO(content))
            paragraphs = [
                paragraph.text for paragraph in document.paragraphs
            ]

            for table in document.tables:
                for row in table.rows:
                    paragraphs.append(
                        " ".join(cell.text for cell in row.cells)
                    )

            return "\n".join(paragraphs)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not read this resume. "
                "Please try another PDF or DOCX file."
            ),
        ) from exc

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Upload a PDF or DOCX file.",
    )


def contains_term(text: str, term: str) -> bool:
    """Find a skill without matching it inside unrelated words."""
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def analyze_text(text: str, job_role: str) -> dict:
    """Analyze resume text using transparent, rule-based checks."""
    word_count = len(re.findall(r"\b[\w+#./-]+\b", text))

    email_found = bool(
        re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text,
            re.IGNORECASE,
        )
    )

    phone_found = bool(
        re.search(
            r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
            text,
        )
    )

    date_found = bool(
        re.search(
            r"\b(?:19|20)\d{2}\b|"
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]?\.?\s+\d{4}\b",
            text,
            re.IGNORECASE,
        )
    )

    quantified_achievement = bool(
        re.search(
            r"\b\d+\s*(?:%|percent|users|customers|projects|hours)\b",
            text,
            re.IGNORECASE,
        )
    )

    found_skills = [
        skill for skill in SKILLS if contains_term(text, skill)
    ]

    section_keywords = {
        "Education": [
            "education", "academic background", "qualification"
        ],
        "Skills": [
            "skills", "technical skills", "core competencies"
        ],
        "Projects": [
            "projects", "personal projects", "academic projects"
        ],
        "Experience": [
            "experience", "work experience", "internship", "employment"
        ],
        "Certifications": [
            "certifications", "certificates", "courses"
        ],
    }

    lowered_text = text.lower()

    sections_found = [
        section
        for section, keywords in section_keywords.items()
        if any(keyword in lowered_text for keyword in keywords)
    ]

    missing_sections = [
        section
        for section in section_keywords
        if section not in sections_found
    ]

    # Resume quality checklist, not a hiring prediction.
    quality_score = 0
    quality_score += len(sections_found) * 7
    quality_score += min(len(found_skills) * 2, 25)
    quality_score += 10 if email_found else 0
    quality_score += 5 if phone_found else 0
    quality_score += (
        10 if 100 <= word_count <= 1000
        else 5 if word_count > 0
        else 0
    )
    quality_score += 5 if date_found else 0
    quality_score += 10 if quantified_achievement else 0
    quality_score = min(quality_score, 100)

    # Compare detected skills against the requested role.
    normalized_role = job_role.strip().lower()
    expected_skills = ROLE_SKILLS.get(normalized_role, [])

    if expected_skills:
        matched_role_skills = [
            skill for skill in expected_skills
            if skill in found_skills
        ]

        missing_role_skills = [
            skill for skill in expected_skills
            if skill not in matched_role_skills
        ]

        skill_match_score = round(
            len(matched_role_skills) / len(expected_skills) * 100
        )
    else:
        matched_role_skills = []
        missing_role_skills = []
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

    if not quantified_achievement:
        improvements.append(
            "Where accurate, include measurable project outcomes or results."
        )

    if expected_skills and missing_role_skills:
        improvements.append(
            "For your target role, consider learning or demonstrating: "
            + ", ".join(missing_role_skills)
            + ". Only include these skills after gaining relevant experience."
        )

    if word_count < 100:
        improvements.append(
            "The extracted resume text is short. "
            "Check that the file contains all pages."
        )

    return {
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
            "These scores are rule-based guidance, not an official ATS score "
            "or a prediction of hiring success. Skill detection depends on "
            "the text extracted from your resume."
        ),
    }


@app.get("/")
def home():
    return {
        "message": "ResumeIQ API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_role: str = Form(""),
):
    filename = file.filename or ""

    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX resume.",
        )

    content = await file.read()

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
                "No readable text found. "
                "Try a text-based PDF or DOCX file."
            ),
        )

    return analyze_text(text, job_role)
