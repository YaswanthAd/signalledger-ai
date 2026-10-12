"""Pure investigation logic. Ranking is a heuristic, never a causal proof."""
import math
import re
from datetime import datetime
from collections import Counter
from statistics import median
from .models import Investigation, AIExplanation
from . import llm


def ancestors(node, assets):
    seen, todo = set(), [node]
    while todo:
        current = todo.pop()
        if current not in seen:
            seen.add(current)
            todo.extend(assets[current].parents)
    return seen


def descendants(node, assets):
    return {key for key in assets if node in ancestors(key, assets) and key != node}


def anomaly(signal):
    center = median(signal.baseline)
    mad = median(abs(v - center) for v in signal.baseline)
    floor = {'null_fraction': .005, 'errors': 1, 'row_count': 1}.get(signal.metric, .5)
    scale = max(1.4826 * mad, abs(center) * .05, floor)
    direction = -1 if signal.metric == 'row_count' else 1
    score = max(0, direction * (signal.observed - center) / scale)
    return {**signal.model_dump(mode='json'), 'baseline_median': center,
            'robust_z': round(score, 3), 'anomalous': score >= 3,
            'direction': 'lower_is_worse' if direction == -1 else 'higher_is_worse'}


def retrieve(query, notes, limit=3):
    """Small BM25 index over runbooks; intentionally no vector service needed."""
    def tokens(text):
        return re.findall(r'[a-z0-9]+', text.lower().replace('_', ' '))
    documents = [(n, tokens(n.text)) for n in notes if n.kind == 'runbook']
    if not documents:
        return []
    avg = sum(len(t) for _, t in documents) / len(documents) or 1
    q = set(tokens(query))
    ranked = []
    for note, words in documents:
        count = Counter(words)
        score = 0
        for token in q:
            df = sum(token in doc for _, doc in documents)
            idf = math.log(1 + (len(documents) - df + .5) / (df + .5))
            tf = count[token]
            score += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * len(words) / avg))
        if score > 0:
            ranked.append({**note.model_dump(mode='json'), 'retrieval_score': round(score, 3)})
    return sorted(ranked, key=lambda x: (-x['retrieval_score'], x['id']))[:limit]


def investigate(request: Investigation):
    assets = {a.id: a for a in request.assets}
    relevant = ancestors(request.target, assets)
    scored = [anomaly(s) for s in request.signals]
    anomalies = [s for s in scored if s['anomalous'] and s['asset_id'] in relevant]
    anomalous_nodes = {s['asset_id'] for s in anomalies}
    candidates = []
    for node in sorted(anomalous_nodes):
        local = [s for s in anomalies if s['asset_id'] == node]
        impacted = sorted(descendants(node, assets))
        corroboration = len(set(impacted) & anomalous_nodes)
        recent_changes = [n for n in request.notes if n.kind == 'change' and n.asset_id == node
                          and any(0 <= (s.timestamp - n.timestamp).total_seconds() <= 3600
                                  for s in request.signals if s.asset_id == node)]
        score = min(max(s['robust_z'] for s in local), 10) + .75 * corroboration + .5 * bool(recent_changes)
        candidates.append({'asset_id': node, 'label': assets[node].label, 'score': round(score, 3),
            'evidence_ids': [s['id'] for s in local] + [n.id for n in recent_changes],
            'downstream': impacted,
            'reason': f"Direct anomaly; {corroboration} anomalous descendants; {len(recent_changes)} recent changes."})
    candidates.sort(key=lambda c: (-c['score'], c['asset_id']))
    runbooks = retrieve(request.question + ' ' + ' '.join(s['detail'] + ' ' + s['metric'] for s in anomalies),
                        [n for n in request.notes if n.asset_id in relevant])
    allowed = {s['id'] for s in scored if s['asset_id'] in relevant} | {r['id'] for r in runbooks}
    allowed |= {n.id for n in request.notes if n.asset_id in relevant and n.kind != 'runbook'}
    controls = [s for s in scored if not s['anomalous'] or s['asset_id'] not in relevant]
    root = candidates[0] if candidates else None
    result = {
        'title': request.title, 'target': request.target, 'status': 'hypothesis' if root else 'insufficient_evidence',
        'analyst': 'evidence_engine', 'ai_status': 'not_requested', 'ai_error': None,
        'summary': (f"Investigate {root['label']} first. It has direct anomalous evidence and can propagate to {assets[request.target].label}."
                    if root else 'No anomalous evidence was found on the target lineage. Collect more telemetry before assigning a cause.'),
        'caveat': 'Ranking is a heuristic, not a probability or proof of causation. Validate the leading hypothesis.',
        'checks': ['Compare the first anomalous timestamp with upstream logs.',
                   'Verify source completeness before considering any replay or backfill.'] if root else ['Check monitoring coverage and collect a longer baseline.'],
        'evidence_ids': root['evidence_ids'] if root else [], 'hypothesis_asset': root['asset_id'] if root else None,
        'candidates': candidates, 'signals': scored, 'controls': controls, 'runbooks': runbooks,
        'notes': [n.model_dump(mode='json') for n in request.notes],
        'assets': [a.model_dump() for a in request.assets],
        'blast_radius': root['downstream'] if root else [],
        'timeline': sorted([{'id': x.id, 'asset_id': x.asset_id, 'timestamp': x.timestamp.isoformat(),
                             'type': 'signal' if hasattr(x, 'metric') else x.kind}
                            for x in [*request.signals, *request.notes] if not hasattr(x, 'kind') or x.kind != 'runbook'],
                           key=lambda e: datetime.fromisoformat(e['timestamp'])),
    }
    if request.analyst == 'ollama' and root:
        try:
            context = {'question': request.question, 'candidates': candidates[:5],
                       'signals': [s for s in scored if s['id'] in allowed],
                       'notes': [n.model_dump(mode='json') for n in request.notes if n.id in allowed],
                       'allowed_evidence_ids': sorted(allowed)}
            raw = llm.generate('You assist data engineers. Explain one supplied candidate with evidence IDs. '
                               'Do not claim certainty. Recommend read-only verification steps. Do not invent observations.',
                               context, AIExplanation.model_json_schema())
            ai = AIExplanation.model_validate(raw)
            candidate = next((c for c in candidates[:5] if c['asset_id'] == ai.hypothesis_asset), None)
            if candidate is None or not set(ai.evidence_ids) <= allowed or not set(ai.evidence_ids) & set(candidate['evidence_ids']):
                raise ValueError('AI explanation failed evidence validation')
            result.update(ai.model_dump())
            result.update(analyst='ollama', ai_status='validated', blast_radius=candidate['downstream'])
        except (llm.ProviderError, ValueError) as exc:
            result.update(ai_status='rejected_or_unavailable', ai_error=str(exc)[:180])
    elif request.analyst == 'ollama':
        result['ai_status'] = 'skipped_insufficient_evidence'
    return result
