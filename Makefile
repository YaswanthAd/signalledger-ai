install:
	python -m pip install -e '.[dev]'
test:
	python -m pytest -q
demo:
	python -m uvicorn signalledger.api:app --host 127.0.0.1 --port 8011
evaluate:
	python scripts/evaluate.py
