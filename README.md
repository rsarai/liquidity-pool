# Liquidity pool
This is a toy project built for Python Nordeste 2022. The goal is to implement web3 apps with web2 tools (no blockchain, no tokens, just data structures and classes)

# Running the project
Clone this project and run the following on the root dir:

```
$ docker run -p 8888:8888 -v $(pwd):/home/jovyan/work jupyter/minimal-notebook
```

# Coverage
pytest -vv --cov=. test_lp.py

# Slides
- https://docs.google.com/presentation/d/1dDXufg5D1p15-5-wbsrforzlQysw5g3_SKrpySP6kwQ/edit?usp=sharing