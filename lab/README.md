# lab/

The research lab: explore the whole corpus and set up new tests without touching the study
(`docs/lab/README.md` is the start page).

- `registry.py`: one row per catalogued work with the facts a test filters on; rule sets
- `passages.py`: fast meaning search over the study's passage index
- `door.py`: the one door to the corpus: `works`, `read`, `find`, `phrase`
- `paths.py`: the only folders lab code may write to
