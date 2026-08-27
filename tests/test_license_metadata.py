from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI matrix
    import tomli as tomllib


ROOT = Path(__file__).parents[1]


def test_polyform_noncommercial_metadata_is_exact() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    assert project["license"] == "PolyForm-Noncommercial-1.0.0"
    assert project["license-files"] == ["LICENSE"]
    assert pyproject["build-system"]["requires"] == ["setuptools>=77.0.3"]

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("# PolyForm Noncommercial License 1.0.0\n")
    assert "https://polyformproject.org/licenses/noncommercial/1.0.0" in license_text
