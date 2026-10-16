
import re
import streamlit as st
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from xml.sax.saxutils import escape
from pypdf import PdfReader

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f4f7fb;
    }

    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(120deg, #172554, #2563eb);
        color: white;
        padding: 30px;
        border-radius: 18px;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: white;
        font-size: 34px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #dbeafe;
        font-size: 16px;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 18px;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stFileUploader"] {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dbeafe;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 22px;
        font-weight: 600;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }

    h2, h3 {
        color: #172554;
    }

    .footer {
        text-align: center;
        color: #64748b;
        padding: 25px 0 5px 0;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# Common technical skills
SKILLS = [
    "python", "java", "javascript", "html", "css",
    "sql", "mysql", "postgresql", "django", "flask",
    "streamlit", "react", "node.js", "machine learning",
    "deep learning", "artificial intelligence", "data analysis",
    "data analytics", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "nlp", "excel", "power bi",
    "tableau", "git", "github", "rest api", "aws",
    "azure", "docker", "communication", "problem solving",
    "data structures", "algorithms", "c++", "c"
]

# Read text from an uploaded PDF
def extract_resume_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


# Match whole words or phrases, not partial words
def contains_term(text, term):
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None


# Analyze the resume
def analyze_resume(resume_text, job_description):
    text = resume_text.lower()
    job_text = job_description.lower()

    sections = {
        "Contact information": [
            "email", "phone", "mobile", "linkedin", "github"
        ],
        "Education": [
            "education", "degree", "bachelor", "university",
            "college", "b.tech", "b.e."
        ],
        "Skills": ["skills", "technical skills", "technologies"],
        "Projects": ["projects", "project"],
        "Experience": [
            "experience", "internship", "work experience"
        ],
        "Certifications": ["certifications", "certificates"]
    }

    section_results = {}

    for section, keywords in sections.items():
        section_results[section] = any(
            contains_term(text, word) for word in keywords
        )

    # Identify skills in the resume
    resume_skills = [
        skill for skill in SKILLS
        if contains_term(text, skill)
    ]

    # Extract skills mentioned in the job description
    required_skills = [
        skill for skill in SKILLS
        if contains_term(job_text, skill)
    ]

    matched_skills = [
        skill for skill in required_skills
        if skill in resume_skills
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill not in resume_skills
    ]

    # Find important job-description keywords
    stop_words = {
        "the", "and", "for", "with", "you", "your", "are",
        "our", "will", "this", "that", "from", "have",
        "has", "who", "all", "can", "job", "role", "work",
        "using", "ability", "required", "preferred", "good",
        "strong", "years", "year", "into", "their", "they"
    }

    job_words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]*\b", job_text)

    important_words = {
        word.lower() for word in job_words
        if len(word) >= 3 and word.lower() not in stop_words
    }

    matched_keywords = [
        word for word in sorted(important_words)
        if contains_term(text, word)
    ]

    missing_keywords = [
        word for word in sorted(important_words)
        if not contains_term(text, word)
    ]

    # Score calculation: total 100 points
    section_score = (
        sum(section_results.values()) / len(section_results) * 25
    )

    if required_skills:
        skill_score = len(matched_skills) / len(required_skills) * 40
    else:
        skill_score = (
            40 if resume_skills else 0
        )

    if important_words:
        keyword_score = (
            len(matched_keywords) / len(important_words) * 25
        )
    else:
        keyword_score = 0

    length_score = 10 if len(text.split()) >= 100 else (
        5 if len(text.split()) >= 40 else 0
    )

    total_score = round(
        section_score + skill_score + keyword_score + length_score
    )

    return {
        "score": min(total_score, 100),
        "sections": section_results,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "word_count": len(text.split())
    }


def create_pdf_report(results, suggestions):
    """Create a downloadable PDF report from resume analysis results."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1D4ED8"),
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=12,
        spaceAfter=7
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=5,
        wordWrap="LTR"
    ))

    story = []

    # Report title
    story.append(Paragraph("AI RESUME ANALYZER", styles["ReportTitle"]))
    story.append(Paragraph(
        "ATS-Style Resume Analysis Report",
        styles["Heading2"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This report provides an estimated resume score based on "
        "section checks, supported skills, job-description keywords, "
        "and resume length. It is not an official ATS result.",
        styles["ReportBody"]
    ))

    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#CBD5E1"),
        spaceBefore=5,
        spaceAfter=12
    ))

    # Score summary
    story.append(Paragraph("1. Score Summary", styles["SectionHeading"]))

    score = results["score"]

    score_data = [
        ["Metric", "Result"],
        ["ATS-style score", f"{score}/100"],
        ["Resume word count", str(results["word_count"])],
        [
            "Required skills matched",
            f"{len(results['matched_skills'])}/"
            f"{len(results['required_skills'])}"
        ]
    ]

    score_table = Table(
        score_data,
        colWidths=[8 * cm, 8 * cm],
        repeatRows=1
    )

    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    story.append(score_table)

    # Resume section checklist
    story.append(Paragraph(
        "2. Resume Section Checklist",
        styles["SectionHeading"]
    ))

    section_data = [["Section", "Status"]]

    for section, present in results["sections"].items():
        section_data.append([
            section,
            "Detected" if present else "Review"
        ])

    section_table = Table(
        section_data,
        colWidths=[8 * cm, 8 * cm],
        repeatRows=1
    )

    section_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(section_table)

    # Skills section
    def add_list_section(title, items, empty_message):
        story.append(Paragraph(title, styles["SectionHeading"]))

        if items:
            for item in items:
                story.append(Paragraph(
                    "&#8226; " + escape(str(item)),
                    styles["ReportBody"]
                ))
        else:
            story.append(Paragraph(
                escape(empty_message),
                styles["ReportBody"]
            ))

    add_list_section(
        "3. Skills Found in Resume",
        results["resume_skills"],
        "No supported skills detected."
    )

    add_list_section(
        "4. Matched Skills",
        results["matched_skills"],
        "No matching skills detected."
    )

    add_list_section(
        "5. Missing Skills to Review",
        results["missing_skills"],
        "No missing supported skills detected."
    )

    add_list_section(
        "6. Matched Job Keywords",
        results["matched_keywords"],
        "No matching keywords detected."
    )

    add_list_section(
        "7. Missing Job Keywords",
        results["missing_keywords"][:40],
        "No missing keywords detected."
    )

    # Suggestions
    story.append(Paragraph(
        "8. Improvement Suggestions",
        styles["SectionHeading"]
    ))

    for suggestion in suggestions:
        story.append(Paragraph(
            "&#8226; " + escape(str(suggestion)),
            styles["ReportBody"]
        ))

    story.append(Spacer(1, 14))

    story.append(HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor("#CBD5E1")
    ))

    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "Generated by AI Resume Analyzer | For guidance only. "
        "Verify all recommendations and include only skills you possess.",
        styles["ReportBody"]
    ))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()

# User interface

st.markdown("""
<div class="hero">
    <h1>AI Resume Analyzer</h1>
    <p>
        Analyze your resume, identify skill gaps, and improve
        your alignment with your target job description.
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("Resume Analysis Workspace")
st.caption(
    "Upload your PDF resume and enter the job description "
    "to generate your personalized report."
)


st.info(
    "This is an educational resume analysis tool. "
    "Its score is an estimate, not a real employer ATS result."
)


upload_col, description_col = st.columns([1, 1.4])

with upload_col:
    st.markdown("### 1. Upload Resume")

    uploaded_file = st.file_uploader(
        "Choose your PDF resume",
        type=["pdf"],
        help="Use a readable, text-based PDF."
    )

    if uploaded_file is not None:
        st.success("Resume uploaded successfully.")

with description_col:
    st.markdown("### 2. Target Job")

    job_description = st.text_area(
        "Paste the complete job description",
        height=180,
        placeholder=(
            "Python, SQL, Django, Git, REST APIs, "
            "communication and problem-solving..."
        )
    )


if st.button("Analyze My Resume", type="primary"):
    if uploaded_file is None:
        st.error("Please upload your resume PDF.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            resume_text = extract_resume_text(uploaded_file)

            if len(resume_text.strip()) < 20:
                st.error(
                    "No readable text was found. "
                    "Try a text-based PDF instead of a scanned image."
                )
            else:
                results = analyze_resume(
                    resume_text, job_description
                )

                st.divider()
                st.header("Analysis Results")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "ATS-style score",
                        f"{results['score']}/100"
                    )

                with col2:
                    st.metric(
                        "Resume word count",
                        results["word_count"]
                    )

                with col3:
                    st.metric(
                        "Matched required skills",
                        f"{len(results['matched_skills'])}/"
                        f"{len(results['required_skills'])}"
                    )

                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=results["score"],
                        title={"text": "ATS-Style Score"},
                        number={"suffix": "/100"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#2563eb"},
                            "steps": [
                                {"range": [0, 40], "color": "#fee2e2"},
                                {"range": [40, 70], "color": "#fef3c7"},
                                {"range": [70, 100], "color": "#dcfce7"},
                            ],
                        },
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                if results["score"] >= 80:
                    st.success("Strong estimated match.")
                elif results["score"] >= 60:
                    st.warning(
                        "Moderate estimated match. "
                        "Review the suggestions below."
                    )
                else:
                    st.error(
                        "Your resume may need improvement "
                        "for this particular job description."
                    )

                st.subheader("Resume Section Checklist")

                for section, present in results["sections"].items():
                    if present:
                        st.write(f"✅ {section}")
                    else:
                        st.write(f"⚠️ Review: {section}")

                st.subheader("Skills Found in Your Resume")

                if results["resume_skills"]:
                    st.write(", ".join(results["resume_skills"]))
                else:
                    st.write("No listed skills were detected.")

                st.subheader("Matched Skills")

                if results["matched_skills"]:
                    st.success(
                        ", ".join(results["matched_skills"])
                    )
                else:
                    st.write("No matching listed skills detected.")

                st.subheader("Missing Skills")

                if results["missing_skills"]:
                    st.warning(
                        ", ".join(results["missing_skills"])
                    )
                else:
                    st.write(
                        "No missing skills from the supported "
                        "skill list were detected."
                    )

                st.subheader("Job Description Keywords")

                col4, col5 = st.columns(2)

                with col4:
                    st.write("**Matched keywords**")
                    st.write(
                        ", ".join(results["matched_keywords"])
                        if results["matched_keywords"]
                        else "No matched keywords detected."
                    )

                with col5:
                    st.write("**Missing keywords**")
                    st.write(
                        ", ".join(results["missing_keywords"][:40])
                        if results["missing_keywords"]
                        else "No missing keywords detected."
                    )

                st.subheader("Improvement Suggestions")

                suggestions = []

                for section, present in results["sections"].items():
                    if not present:
                        suggestions.append(
                            f"Review whether to add a clear "
                            f"{section} section."
                        )

                if results["missing_skills"]:
                    suggestions.append(
                        "Review the missing skills and add any "
                        "you genuinely possess."
                    )

                if results["missing_keywords"]:
                    suggestions.append(
                        "Use relevant job-description terms "
                        "naturally where they accurately describe "
                        "your experience."
                    )

                if results["word_count"] < 100:
                    suggestions.append(
                        "Check whether your resume has enough "
                        "detail about projects, education and skills."
                    )

                if not suggestions:
                    suggestions.append(
                        "Review formatting, dates, accuracy and "
                        "the relevance of your project descriptions."
                    )

                for suggestion in suggestions:
                    st.write(f"• {suggestion}")

                report = (
                    "AI RESUME ANALYZER REPORT\n"
                    f"ATS-style score: {results['score']}/100\n"
                    f"Word count: {results['word_count']}\n"
                    f"Resume skills: "
                    f"{', '.join(results['resume_skills'])}\n"
                    f"Matched skills: "
                    f"{', '.join(results['matched_skills'])}\n"
                    f"Missing skills: "
                    f"{', '.join(results['missing_skills'])}\n"
                    f"Matched keywords: "
                    f"{', '.join(results['matched_keywords'])}\n"
                    f"Missing keywords: "
                    f"{', '.join(results['missing_keywords'])}\n"
                    "\nSUGGESTIONS\n"
                    + "\n".join(suggestions)
                )

                st.download_button(
                    "Download Analysis Report",
                    data=report,
                    file_name="resume_analysis_report.txt",
                    mime="text/plain"
                )

                # Generate professional PDF report
                pdf_bytes = create_pdf_report(results, suggestions)

                st.download_button(
                    label="Download Professional PDF Report",
                    data=pdf_bytes,
                    file_name="AI_Resume_Analysis_Report.pdf",
                    mime="application/pdf",
                    key="download_pdf_report"
                )


        except Exception as error:
            st.error(
                "Unable to analyze this PDF. "
                "Check that the file is valid and readable."
            )
            st.caption(f"Technical details: {error}")

st.markdown("""
<div class="footer">
    AI Resume Analyzer | Python · Streamlit · NLP
    <br>
    Scores are estimates and should not be treated as
    official employer ATS results.
</div>
""", unsafe_allow_html=True)
