"""
toolkit/observability.py

Per-stage timing for every request, LangSmith-compatible (set
LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY to use real LangSmith
instead — no code changes needed here).
"""
import time


class Tracer:
    def __init__(self):
        self.stages = {}

    def stage(self, name: str):
        return _StageTimer(self, name)

    def as_dict(self) -> dict:
        return dict(self.stages)

    def total_seconds(self) -> float:
        return sum(self.stages.values())


class _StageTimer:
    def __init__(self, tracer: Tracer, name: str):
        self.tracer = tracer
        self.name = name

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args):
        self.tracer.stages[self.name] = round(time.time() - self._start, 4)
