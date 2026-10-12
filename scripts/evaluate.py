"""Reproduce the three synthetic scenarios. No model or network is required."""
import json
from pathlib import Path
from signalledger.models import Investigation
from signalledger.engine import investigate
ROOT=Path(__file__).resolve().parents[1]
expected={'01-source-delay': 'partner_api', '02-schema-drift': 'raw_events', '03-healthy': None}
out=[]
for scenario,expect in expected.items():
    request=Investigation.model_validate_json((ROOT/'examples'/f'{scenario}.json').read_text())
    result=investigate(request)
    observed=result['hypothesis_asset']
    assert observed==expect,(scenario,observed,expect)
    out.append({'scenario':scenario,'expected':expect,'observed':observed,'passed':True})
report={'scope':'Three designed synthetic fixtures; evidence engine only; no LLM quality or load benchmark.','results':out}
(ROOT/'docs/evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
