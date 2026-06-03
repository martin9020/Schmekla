from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_python_and_pytest_baseline_docs_match_current_evidence():
    readme = read_doc("README.md")
    onboarding = read_doc("docs/company/onboarding.md")
    risk_register = read_doc("docs/company/risk-register.md")

    assert "Python support target: 3.11+ project metadata; 3.12+ launcher path pending SUP-2" in readme
    assert "Python support target is not yet a production baseline" in onboarding
    assert "pytest` currently runs under Python 3.13.11 with 30 passing tests" in onboarding
    assert "pytest --cov=src` currently runs under Python 3.13.11 with 30 passing tests" in onboarding
    assert "py -m pytest` still launches Python 3.14 without pytest installed" in onboarding
    assert "not on PATH" not in onboarding
    assert "command not found" not in onboarding
    assert "Python/test baseline still needs a supported-version decision" in risk_register
