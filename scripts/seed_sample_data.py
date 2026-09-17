"""
Creates a couple of tiny sample resumes (1 English, 1 Arabic) plus matching
ground-truth JSON so the pipeline and evaluator can be smoke-tested before
any real resumes / human-reviewed ground truth are added.

IMPORTANT: each resume's ground truth must match what is actually written in that resume's own language/script. Using
one resume's (e.g. English) ground truth for the other language's file
silently corrupts Arabic-vs-English quality comparisons, since the scorer
would be comparing the Arabic model output against English-language
expected values. Ground truth here is evaluation-only; it is never fed
into the model during inference.

Run: python scripts/seed_sample_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docx import Document  # noqa: E402


EN_RESUME_TEXT = """Sarah Al-Amin
sarah.alamin@example.com | +966-50-123-4567 | Riyadh, Saudi Arabia
linkedin.com/in/sarah-alamin | github.com/sarahalamin

Summary
Backend-leaning software engineer with 5 years of experience building data
pipelines and ML infrastructure.

Education
BSc Computer Science, King Saud University, 2016-2020, GPA 3.8

Work Experience
Software Engineer, Acme Analytics, 2020-2023
Built data pipelines and internal tooling in Python.

Senior Software Engineer, DataCore, 2023-Present
Leads a team building ML infrastructure.

Skills
Python, SQL, Docker, Kubernetes, AWS, Leadership, Communication, Problem Solving

Certifications
AWS Certified Solutions Architect, Amazon, issued 2022

Projects
Resume Parser, github.com/sarahalamin/resume-parser
Open-source bilingual resume parsing pipeline.

Languages
English (Native), Arabic (Fluent)
"""

AR_RESUME_TEXT = """سارة الأمين
sarah.alamin@example.com | 966501234567+ | الرياض، المملكة العربية السعودية

نبذة
مهندسة برمجيات لديها خمس سنوات من الخبرة في بناء خطوط البيانات والبنية
التحتية للتعلم الآلي.

التعليم
بكالوريوس علوم حاسب، جامعة الملك سعود، 2016-2020، معدل تراكمي 3.8

الخبرة العملية
مهندسة برمجيات، شركة أكمي للتحليلات، 2020-2023
بناء خطوط بيانات وأدوات داخلية باستخدام بايثون.

مهندسة برمجيات أولى، داتاكور، 2023-حتى الآن
تقود فريقاً لبناء البنية التحتية للتعلم الآلي.

المهارات
بايثون، إس كيو إل، دوكر، كوبرنيتيس، أمازون ويب سيرفيسز، القيادة، التواصل، حل المشكلات

الشهادات
شهادة AWS للحلول المعمارية المعتمدة، أمازون، صدرت 2022

المشاريع
محلل السير الذاتية، github.com/sarahalamin/resume-parser
خط أنابيب مفتوح المصدر لتحليل السير الذاتية ثنائية اللغة.

اللغات
العربية (اللغة الأم)، الإنجليزية (طلاقة)
"""

# Ground truth for the ENGLISH resume: every value here is taken verbatim
# (or trivially normalized) from EN_RESUME_TEXT above.
EN_GROUND_TRUTH = {
    "full_name": "Sarah Al-Amin",
    "email": "sarah.alamin@example.com",
    "phone": "+966-50-123-4567",
    "location": "Riyadh, Saudi Arabia",
    "summary": (
        "Backend-leaning software engineer with 5 years of experience "
        "building data pipelines and ML infrastructure."
    ),
    "github": "github.com/sarahalamin",
    "linkedin": "linkedin.com/in/sarah-alamin",
    "portfolio": None,
    "skills": [
        "Python", "SQL", "Docker", "Kubernetes", "AWS",
        "Leadership", "Communication", "Problem Solving",
    ],
    "certificates": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon",
            "issue_date": "2022",
            "expiry_date": None,
        }
    ],
    "projects": [
        {
            "name": "Resume Parser",
            "link": "github.com/sarahalamin/resume-parser",
            "description": "Open-source bilingual resume parsing pipeline.",
        }
    ],
    "education": [
        {
            "degree": "BSc Computer Science",
            "institution": "King Saud University",
            "start_year": "2016",
            "end_year": "2020",
            "gpa": "3.8",
        }
    ],
    "work_experience": [
        {
            "company": "Acme Analytics",
            "role": "Software Engineer",
            "start_date": "2020",
            "end_date": "2023",
            "description": "Built data pipelines and internal tooling in Python.",
        },
        {
            "company": "DataCore",
            "role": "Senior Software Engineer",
            "start_date": "2023",
            "end_date": "Present",
            "description": "Leads a team building ML infrastructure.",
        },
    ],
    "languages": [
        {"language": "English", "proficiency": "Native"},
        {"language": "Arabic", "proficiency": "Fluent"},
    ],
    "years_of_experience": 5,
    "detected_source_language": "en",
}

# Ground truth for the ARABIC resume: values are taken from AR_RESUME_TEXT
# in their original Arabic script (per the parsing pipeline's rule of
# preserving names/terms in their original language), not translated back
# to English. Only language-agnostic tokens (emails, URLs, numbers) match
# the English resume's ground truth by coincidence, since this is the same
# underlying person's data restated in Arabic, not a shared ground-truth
# object.
AR_GROUND_TRUTH = {
    "full_name": "سارة الأمين",
    "email": "sarah.alamin@example.com",
    "phone": "+966501234567",
    "location": "الرياض، المملكة العربية السعودية",
    "summary": (
        "مهندسة برمجيات لديها خمس سنوات من الخبرة في بناء خطوط البيانات "
        "والبنية التحتية للتعلم الآلي."
    ),
    "github": "github.com/sarahalamin",
    "linkedin": None,
    "portfolio": None,
    "skills": [
        "بايثون", "إس كيو إل", "دوكر", "كوبرنيتيس", "أمازون ويب سيرفيسز",
        "القيادة", "التواصل", "حل المشكلات",
    ],
    "certificates": [
        {
            "name": "شهادة AWS للحلول المعمارية المعتمدة",
            "issuer": "أمازون",
            "issue_date": "2022",
            "expiry_date": None,
        }
    ],
    "projects": [
        {
            "name": "محلل السير الذاتية",
            "link": "github.com/sarahalamin/resume-parser",
            "description": "خط أنابيب مفتوح المصدر لتحليل السير الذاتية ثنائية اللغة.",
        }
    ],
    "education": [
        {
            "degree": "بكالوريوس علوم حاسب",
            "institution": "جامعة الملك سعود",
            "start_year": "2016",
            "end_year": "2020",
            "gpa": "3.8",
        }
    ],
    "work_experience": [
        {
            "company": "شركة أكمي للتحليلات",
            "role": "مهندسة برمجيات",
            "start_date": "2020",
            "end_date": "2023",
            "description": "بناء خطوط بيانات وأدوات داخلية باستخدام بايثون.",
        },
        {
            "company": "داتاكور",
            "role": "مهندسة برمجيات أولى",
            "start_date": "2023",
            "end_date": "حتى الآن",
            "description": "تقود فريقاً لبناء البنية التحتية للتعلم الآلي.",
        },
    ],
    "languages": [
        {"language": "العربية", "proficiency": "اللغة الأم"},
        {"language": "الإنجليزية", "proficiency": "طلاقة"},
    ],
    "years_of_experience": 5,
    "detected_source_language": "ar",
}


def write_docx(text: str, path: Path) -> None:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(str(path))


def main():
    en_dir = ROOT / "data" / "resumes" / "english"
    ar_dir = ROOT / "data" / "resumes" / "arabic"
    gt_dir = ROOT / "data" / "ground_truth"
    for d in (en_dir, ar_dir, gt_dir):
        d.mkdir(parents=True, exist_ok=True)

    write_docx(EN_RESUME_TEXT, en_dir / "sample_en_001.docx")
    write_docx(AR_RESUME_TEXT, ar_dir / "sample_ar_001.docx")

    (gt_dir / "sample_en_001.json").write_text(
        json.dumps(EN_GROUND_TRUTH, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Separate, language-matched ground truth for the Arabic sample (fixes
    # the previous bug where both files shared the English ground truth).
    (gt_dir / "sample_ar_001.json").write_text(
        json.dumps(AR_GROUND_TRUTH, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("Seeded sample data:")
    print(f"  {en_dir / 'sample_en_001.docx'}")
    print(f"  {ar_dir / 'sample_ar_001.docx'}")
    print(f"  {gt_dir / 'sample_en_001.json'}")
    print(f"  {gt_dir / 'sample_ar_001.json'}")


if __name__ == "__main__":
    main()
