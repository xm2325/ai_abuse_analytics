.PHONY: test demo clean

test:
	pytest -q

demo:
	python run_all.py --n-accounts 180 --seed 17

clean:
	rm -f data/*.csv artifacts/*.csv artifacts/*.json artifacts/*.md
	rm -rf artifacts/cases
