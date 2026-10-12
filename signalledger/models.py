from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Asset(Strict):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,60}$')
    label: str = Field(min_length=1, max_length=120)
    kind: Literal['source', 'pipeline', 'table', 'dashboard']
    parents: list[str] = Field(default_factory=list, max_length=30)


class Signal(Strict):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,60}$')
    asset_id: str
    metric: Literal['freshness_minutes', 'row_count', 'null_fraction', 'duration_seconds', 'errors']
    observed: float = Field(ge=0, le=1e15)
    baseline: list[Annotated[float, Field(ge=0, le=1e15)]] = Field(min_length=5, max_length=168)
    timestamp: datetime
    detail: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def limits(self):
        if self.timestamp.utcoffset() is None:
            raise ValueError('Signal timestamps require a timezone')
        if any(x < 0 for x in self.baseline):
            raise ValueError('Baseline values must be nonnegative')
        if self.metric == 'null_fraction' and any(x > 1 for x in [self.observed, *self.baseline]):
            raise ValueError('Null fractions must be between zero and one')
        return self


class Note(Strict):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,60}$')
    asset_id: str
    kind: Literal['change', 'log', 'runbook']
    text: str = Field(min_length=1, max_length=3000)
    timestamp: datetime

    @model_validator(mode='after')
    def zoned(self):
        if self.timestamp.utcoffset() is None:
            raise ValueError('Note timestamps require a timezone')
        return self


class Investigation(Strict):
    title: str = Field(min_length=1, max_length=150)
    target: str
    question: str = Field(default='What should the on-call engineer investigate first?', max_length=600)
    assets: list[Asset] = Field(min_length=1, max_length=60)
    signals: list[Signal] = Field(min_length=1, max_length=200)
    notes: list[Note] = Field(default_factory=list, max_length=100)
    analyst: Literal['rules', 'ollama'] = 'rules'

    @model_validator(mode='after')
    def graph_valid(self):
        assets = {a.id: a for a in self.assets}
        if len(assets) != len(self.assets) or self.target not in assets:
            raise ValueError('Asset IDs must be unique and the target must exist')
        evidence_ids = [x.id for x in [*self.signals, *self.notes]]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError('Evidence IDs must be unique')
        for asset in self.assets:
            if any(p not in assets for p in asset.parents) or len(set(asset.parents)) != len(asset.parents):
                raise ValueError('Parents must exist and be unique')
        if any(x.asset_id not in assets for x in [*self.signals, *self.notes]):
            raise ValueError('Evidence must reference an existing asset')
        visiting, done = set(), set()
        def visit(node):
            if node in visiting:
                raise ValueError('Lineage must be acyclic')
            if node in done:
                return
            visiting.add(node)
            for parent in assets[node].parents:
                visit(parent)
            visiting.remove(node)
            done.add(node)
        for node in assets:
            visit(node)
        return self


class AIExplanation(Strict):
    hypothesis_asset: str
    summary: str = Field(min_length=15, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1, max_length=20)
    checks: list[str] = Field(min_length=1, max_length=5)
    caveat: str = Field(min_length=1, max_length=500)
