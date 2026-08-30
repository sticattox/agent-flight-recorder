"""Agent Flight Recorder — structured traces from observable agent sessions."""

from .models import FlightTrace, PatternRecord, PatternLibrary
from .pipeline import ingest_transcript, merge_into_library

__version__ = "0.2.0"
__all__ = [
    "FlightTrace",
    "PatternRecord",
    "PatternLibrary",
    "ingest_transcript",
    "merge_into_library",
    "__version__",
]
