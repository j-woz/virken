#!/bin/zsh

P="pypi-AgENdGVzdC5weXBpLm9yZwIkOThmNDk0M2EtODBkNC00MmFjLWI2M2ItYTI2NjMzMjgzNjExAAIqWzMsIjk5NzQ1Mzg2LTUwMmQtNDg1Yi1iZWQ4LTFjNGY3NmM4YjUzZSJdAAAGIIKcvQlFpXFoDTbRKcSrlzLNW3jMRt-jtLAFrhJm8N1j"

job twine upload \
      -u __token__ \
      -p $P \
      --repository testpypi  \
      dist/verctrl-0.0.1.tar.gz dist/verctrl-0.0.1-py3-none-any.whl
