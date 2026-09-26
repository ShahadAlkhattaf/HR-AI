"""Input contract for the future job-matching task."""

from pydantic import BaseModel

from ..extraction.schema import CandidateProfile


class MatchRequest(BaseModel):
    candidate: CandidateProfile
    job_description: str
