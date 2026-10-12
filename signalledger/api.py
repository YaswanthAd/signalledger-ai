import json
import os
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from .models import Investigation
from .engine import investigate
from .store import Store, Conflict
from .security import Boundary

HERE = Path(__file__).parent


def create_app(db_path=None):
    app = FastAPI(title='SignalLedger', version='0.1.0', docs_url=None, redoc_url=None)
    store = Store(db_path or os.getenv('DB_PATH', 'data/signalledger.db'))
    app.add_middleware(Boundary)

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'service': 'signalledger'}

    @app.get('/api/scenarios')
    def scenarios():
        return [{'id': p.stem, 'title': json.loads(p.read_text())['title']} for p in sorted((HERE / 'fixtures').glob('*.json'))]

    @app.get('/api/scenarios/{scenario_id}')
    def scenario(scenario_id: str):
        path = next((p for p in (HERE / 'fixtures').glob('*.json') if p.stem == scenario_id), None)
        if not path:
            raise HTTPException(404, 'Scenario not found')
        return json.loads(path.read_text())

    @app.post('/api/investigations')
    def create(request: Investigation, idempotency_key: str | None = Header(default=None, max_length=128)):
        key = idempotency_key or str(uuid4())
        body = request.model_dump(mode='json')
        try:
            cached = store.cached(key, body)
            return cached or store.save(key, body, investigate(request))
        except Conflict as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get('/api/investigations')
    def recent():
        return store.recent()

    @app.get('/api/investigations/{report_id}')
    def report(report_id: str):
        result = store.get(report_id)
        if result is None:
            raise HTTPException(404, 'Investigation not found')
        return result

    app.mount('/', StaticFiles(directory=HERE / 'web', html=True), name='web')
    return app


app = create_app()
