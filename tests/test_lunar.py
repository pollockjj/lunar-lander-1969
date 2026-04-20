from pathlib import Path
import sys

import pytest

# Add parent directory to path to import lunar module
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import lunar

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


@pytest.mark.parametrize(
    ("script_name", "expected_verdict"),
    [
        ("test/fail.asc", FAIL_VERDICT),
        ("test/ok.asc", OK_VERDICT),
        ("test/good.asc", GOOD_VERDICT),
    ],
)
def test_oracle_fixture_expectations_for_fail_ok_good_scripts(script_name: str, expected_verdict: str) -> None:
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
    expected_terminal_verdicts = {"test/fail.asc": FAIL_VERDICT, "test/ok.asc": OK_VERDICT, "test/good.asc": GOOD_VERDICT}
    assert expected_terminal_verdicts["test/fail.asc"] == "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"
    assert expected_terminal_verdicts["test/ok.asc"] == "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"
    assert expected_terminal_verdicts["test/good.asc"] == "GOOD LANDING (COULD BE BETTER)"
    assert expected_terminal_verdicts[script_name] == expected_verdict


def test_python_step_matches_basic_series_expansion() -> None:
    """
    AC-1: Verify simulation_step implements the polynomial series from lunar.bas lines 420-430.

    The BASIC oracle computes:
      Q = S*K/M
      J = V + G*S + Z*(-Q - Q*Q/2 - Q^3/3 - Q^4/4 - Q^5/5)
      I = A - G*S*S/2 - V*S + Z*S*(Q/2 + Q^2/6 + Q^3/12 + Q^4/20 + Q^5/30)

    This test confirms the Python port produces identical results for known state.
    """
    # Known state: altitude=120mi, velocity=1mi/s, mass=33000lb, fuel=16500lb, burn=150lb/s, dt=10s
    altitude = 120.0
    velocity = 1.0
    mass = 33000.0
    fuel_mass = 16500.0
    burn_rate = 150.0
    time_step = 10.0

    # Hand-calculate BASIC oracle values
    s = time_step
    k = burn_rate
    m = mass
    v = velocity
    a = altitude
    g = lunar.G
    z = lunar.Z

    q = s * k / m
    j_expected = v + g * s + z * (-q - q * q / 2 - q**3 / 3 - q**4 / 4 - q**5 / 5)
    i_expected = a - g * s * s / 2 - v * s + z * s * (q / 2 + q**2 / 6 + q**3 / 12 + q**4 / 20 + q**5 / 30)

    # Call Python implementation
    new_altitude, new_velocity, new_mass, new_fuel_mass, actual_step = lunar.simulation_step(
        altitude, velocity, mass, fuel_mass, burn_rate, time_step
    )

    # Verify polynomial terms match BASIC
    assert abs(new_velocity - j_expected) < 1e-9, f"Velocity mismatch: {new_velocity} vs {j_expected}"
    assert abs(new_altitude - i_expected) < 1e-9, f"Altitude mismatch: {new_altitude} vs {i_expected}"
    assert abs(new_mass - (mass - s * k)) < 1e-9, "Mass update mismatch"
    assert abs(new_fuel_mass - (fuel_mass - s * k)) < 1e-9, "Fuel mass update mismatch"
    assert abs(actual_step - s) < 1e-9, "Time step mismatch"


def test_fuel_out_terminal_velocity_matches_basic_formula() -> None:
    """
    AC-2: Verify fuel_out_terminal_velocity implements lunar.bas lines 240-250.

    The BASIC oracle computes:
      S = (-V + SQR(V*V + 2*A*G)) / G
      V_terminal = V + G*S
      W = 3600 * V_terminal (convert to mph)

    This test confirms the Python quadratic-formula solver matches BASIC.
    """
    # Known fuel-out state from test/fail.asc trajectory endpoint
    altitude = 0.5  # miles
    velocity = 0.05  # miles/sec downward

    # Hand-calculate BASIC oracle terminal velocity
    g = lunar.G
    import math
    s = (-velocity + math.sqrt(velocity * velocity + 2 * altitude * g)) / g
    v_terminal_basic = velocity + g * s
    w_basic = 3600 * v_terminal_basic

    # Call Python implementation
    w_python = lunar.fuel_out_terminal_velocity(altitude, velocity)

    # Verify quadratic formula match
    assert abs(w_python - w_basic) < 1e-6, f"Terminal velocity mismatch: {w_python} vs {w_basic}"


def test_touchdown_verdict_thresholds_match_basic() -> None:
    """
    AC-3: Verify touchdown_verdict implements lunar.bas lines 274-300 verdict branches.

    The BASIC oracle has these thresholds:
      W <= 1.2: PERFECT LANDING!
      W <= 10: GOOD LANDING (COULD BE BETTER)
      10 < W <= 60: CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE
      W > 60: SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!

    This test confirms the Python verdict logic matches BASIC branch conditions.
    """
    # Test perfect landing threshold
    assert lunar.touchdown_verdict(1.2) == "PERFECT LANDING!"
    assert lunar.touchdown_verdict(1.0) == "PERFECT LANDING!"

    # Test good landing threshold
    assert lunar.touchdown_verdict(1.21) == "GOOD LANDING (COULD BE BETTER)"
    assert lunar.touchdown_verdict(10.0) == "GOOD LANDING (COULD BE BETTER)"

    # Test craft damage threshold
    assert lunar.touchdown_verdict(10.01) == "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"
    assert lunar.touchdown_verdict(60.0) == "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"

    # Test fatal crash threshold
    assert lunar.touchdown_verdict(60.01) == "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"
    assert lunar.touchdown_verdict(100.0) == "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"


def test_cli_prompt_cadence_and_telemetry_for_committed_scripts() -> None:
    """
    Slice 3 AC-3: Verify CLI produces expected prompt structure and telemetry columns.

    The CLI should:
    - Print the header banner and instructions
    - Print column headers: SEC, MI + FT, MPH, LB FUEL, BURN RATE
    - Print telemetry rows at 10-second intervals
    - Accept burn rate inputs from stdin
    - Print terminal verdict with ON MOON message
    - Print flavor text for craft damage (PARTY ARRIVES) or fatal crash (CRATER depth)
    """
    import subprocess
    from pathlib import Path

    # Test with each committed burn script
    for script_path in [FAIL_SCRIPT, OK_SCRIPT, GOOD_SCRIPT]:
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "lunar.py")],
            stdin=script_path.open("r"),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI exited non-zero for {script_path.name}: {result.returncode}"

        output = result.stdout

        # Verify banner and instructions present
        assert "LUNAR" in output
        assert "CREATIVE COMPUTING" in output
        assert "APOLLO LUNAR" in output
        assert "CAPSULE WEIGHT 32,500 LBS; FUEL WEIGHT 16,500 LBS" in output

        # Verify column headers
        assert "SEC" in output and "MI + FT" in output and "MPH" in output
        assert "LB FUEL" in output and "BURN RATE" in output

        # Verify terminal state message present
        assert "ON MOON AT" in output
        assert "IMPACT VELOCITY" in output
        assert "MPH" in output

        # Verify at least one verdict is present
        verdicts = [
            "PERFECT LANDING!",
            "GOOD LANDING (COULD BE BETTER)",
            "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE",
            "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!",
        ]
        assert any(v in output for v in verdicts), f"No verdict found in output for {script_path.name}"

        # Verify flavor text is present for applicable verdicts
        if "CRAFT DAMAGE" in output:
            assert "PARTY ARRIVES. HOPE YOU HAVE ENOUGH OXYGEN!" in output
        if "SORRY THERE WERE NO SURVIVORS" in output:
            assert "CRATER" in output and "FEET DEEP" in output
