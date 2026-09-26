"""Task-specific prompt for job matching, separate from resume extraction."""

from .schema import MatchRequest


def build_matching_prompt(request: MatchRequest) -> str:
    return (
        "Compare the candidate profile with the job description.\n\n"
        f"CANDIDATE PROFILE:\n{request.candidate.model_dump_json()}\n\n"
        f"JOB DESCRIPTION:\n{request.job_description}"
    )
