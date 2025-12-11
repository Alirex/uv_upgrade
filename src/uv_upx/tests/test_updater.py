import pytest


@pytest.fixture
def lock_file_contents() -> str:
    return """[[package]]
name = "bla"
version = "0.2.1"

[[package]]
name = "foo"
version = "1.21.0"
"""


@pytest.fixture
def pyproject_toml_contents() -> str:
    return """[project]
name = "uv-upx"
version = "0.2.4"

requires-python = ">=3.14"
dependencies = [
    # Better classes and data validation
    "pydantic>=2.12.5",
    # TOML parser and writer with preserved formatting
    "tomlkit>=0.13.3",
    # CLI app framework
    "typer>=0.20.0",
]
"""


# TODO: Add tests.
