"""
Creates a couple of tiny sample resumes (1 English, 1 Arabic) plus matching
ground-truth JSON so the pipeline and evaluator can be smoke-tested before
any real resumes / human-reviewed ground truth are added.

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
sarah.alamin@example.com | +966-50-123-4567

Education
BSc Computer Science, King Saud University, 2016-2020

Work Experience
Software Engineer, Acme Analytics, 2020-2023
Built data pipelines and internal tooling in Python.

Senior Software Engineer, DataCore, 2023-Present
Leads a team building ML infrastructure.

Technical Skills
Python, SQL, Docker, Kubernetes, AWS

Soft Skills
Leadership, Communication, Problem Solving

Certifications
AWS Certified Solutions Architect, Amazon, 2022

Languages
English (Native), Arabic (Fluent)
"""

AR_RESUME_TEXT = """سارة الأمين
sarah.alamin@example.com | 966501234567+

التعليم
بكالوريوس علوم حاسب، جامعة الملك سعود، 2016-2020

الخبرة العملية
مهندسة برمجيات، شركة أكمي للتحليلات، 2020-2023
بناء خطوط بيانات وأدوات داخلية باستخدام بايثون.

مهندسة برمجيات أولى، داتاكور، 2023-حتى الآن
تقود فريقاً لبناء البنية التحتية للتعلم الآلي.

المهارات التقنية
بايثون، إس كيو إل، دوكر، كوبرنيتيس، أمازون ويب سيرفيسز

المهارات الشخصية
القيادة، التواصل، حل المشكلات

الشهادات
شهادة AWS للحلول المعمارية المعتمدة، أمازون، 2022

اللغات
العربية (اللغة الأم)، الإنجليزية (طلاقة)
"""

GROUND_TRUTH = {
    "full_name": "Sarah Al-Amin",
    "email": "sarah.alamin@example.com",
    "phone": "+966-50-123-4567",
    "education": [
        {
            "degree": "BSc",
            "field_of_study": "Computer Science",
            "institution": "King Saud University",
            "start_year": "2016",
            "end_year": "2020",
        }
    ],
    "work_experience": [
        {
            "job_title": "Software Engineer",
            "company": "Acme Analytics",
            "start_date": "2020",
            "end_date": "2023",
            "description": "Built data pipelines and internal tooling in Python.",
        },
        {
            "job_title": "Senior Software Engineer",
            "company": "DataCore",
            "start_date": "2023",
            "end_date": "Present",
            "description": "Leads a team building ML infrastructure.",
        },
    ],
    "years_of_experience": 5,
    "technical_skills": ["Python", "SQL", "Docker", "Kubernetes", "AWS"],
    "soft_skills": ["Leadership", "Communication", "Problem Solving"],
    "certifications": [
        {"name": "AWS Certified Solutions Architect", "issuer": "Amazon", "year": "2022"}
    ],
    "languages": [
        {"language": "English", "proficiency": "Native"},
        {"language": "Arabic", "proficiency": "Fluent"},
    ],
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
        json.dumps(GROUND_TRUTH, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Same ground truth content applies to the Arabic version of the same resume.
    (gt_dir / "sample_ar_001.json").write_text(
        json.dumps(GROUND_TRUTH, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("Seeded sample data:")
    print(f"  {en_dir / 'sample_en_001.docx'}")
    print(f"  {ar_dir / 'sample_ar_001.docx'}")
    print(f"  {gt_dir / 'sample_en_001.json'}")
    print(f"  {gt_dir / 'sample_ar_001.json'}")


if __name__ == "__main__":
    main()
