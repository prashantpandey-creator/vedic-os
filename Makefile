.PHONY: run clean docker test

run:
	./run.sh

clean:
	rm -rf venv/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -f *.log

docker:
	docker build -t vedic-sandbox .

test:
	pytest tests/
