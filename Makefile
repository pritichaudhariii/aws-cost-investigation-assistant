.PHONY: install test eval demo up

install:
	pip install -e ".[api,qdrant,dev]"

test:
	pytest -q

eval:
	python -m evaluation.run_eval
	python -m evaluation.run_eval --retrieval-mode question --out evaluation/results_baseline

demo:
	costassist investigate --scenario S07 --role engineer

up:
	docker compose up --build
