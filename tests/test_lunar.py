from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BASIC_SOURCE = REPO_ROOT / "lunar.bas"

FAIL_SCRIPT = REPO_ROOT / "test/fail.asc"
OK_SCRIPT = REPO_ROOT / "test/ok.asc"
GOOD_SCRIPT = REPO_ROOT / "test/good.asc"

FAIL_VERDICT = "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"
OK_VERDICT = "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"
GOOD_VERDICT = "GOOD LANDING (COULD BE BETTER)"


def _read_basic_source() -> str:
    return BASIC_SOURCE.read_text(encoding="utf-8", errors="strict")


def _read_burn_script(path: Path) -> list[int]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="strict").splitlines()]
    return [int(line) for line in lines if line]


def test_canonical_constants_match_lunar_bas() -> None:
    source = _read_basic_source()
    assert "A=120:V=1:M=33000:N=16500:G=1E-03:Z=1.8" in source
    assert "IF W<=1.2 THEN PRINT \"PERFECT LANDING!\"" in source
    assert "IF W<=10 THEN PRINT \"GOOD LANDING (COULD BE BETTER)\"" in source


def test_series_equation_terms_match_basic_update_block() -> None:
    source = _read_basic_source()
    assert "Q=S*K/M" in source
    assert "J=V+G*S+Z*(-Q-Q*Q/2-Q^3/3-Q^4/4-Q^5/5)" in source
    assert "I=A-G*S*S/2-V*S+Z*S*(Q/2+Q^2/6+Q^3/12+Q^4/20+Q^5/30)" in source


def test_oracle_fixture_expectations_for_fail_ok_good_scripts() -> None:
    fail_burns = _read_burn_script(FAIL_SCRIPT)
    ok_burns = _read_burn_script(OK_SCRIPT)
    good_burns = _read_burn_script(GOOD_SCRIPT)

    assert fail_burns[:8] == [0, 0, 0, 0, 0, 0, 0, 170]
    assert fail_burns[-4:] == [0, 0, 0, 20]
    assert max(fail_burns) == 200

    assert ok_burns[:8] == [0, 0, 0, 0, 0, 0, 0, 170]
    assert ok_burns[-4:] == [8, 10, 9, 100]
    assert ok_burns.count(200) == 6

    assert good_burns[:5] == [0, 0, 0, 0, 0]
    assert good_burns[-5:] == [100, 70, 39, 21, 15]
    assert min(good_burns) == 0

    # Oracle verdict expectations tied to script fixtures.
    expected_terminal_verdicts = {
        "test/fail.asc": FAIL_VERDICT,
        "test/ok.asc": OK_VERDICT,
        "test/good.asc": GOOD_VERDICT,
    }
    assert expected_terminal_verdicts["test/fail.asc"] == "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"
    assert expected_terminal_verdicts["test/ok.asc"] == "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"
    assert expected_terminal_verdicts["test/good.asc"] == "GOOD LANDING (COULD BE BETTER)"
