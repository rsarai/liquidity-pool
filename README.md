# Running the project
Clone this project and run the following on the root dir:

```
$ docker run -p 8888:8888 -v $(pwd):/home/jovyan/work jupyter/minimal-notebook
```

# Coverage
pytest -vv --cov=. test_lp.py
