from hourplan_conformance.invariants import check_invariants


def _base():
    return {
        "total_duration_ms": 300,
        "items": [
            {"seq": 0, "duration_ms": 100, "timing_rule": "hard", "start_offset_ms": 0},
            {"seq": 1, "duration_ms": 200, "timing_rule": "soft", "start_offset_ms": None},
        ],
    }


def test_valid_plan_has_no_invariant_errors():
    assert check_invariants(_base()) == []


def test_i1_seq_must_be_contiguous():
    p = _base()
    p["items"][1]["seq"] = 5
    errors = check_invariants(p)
    assert any("I1" in e for e in errors)


def test_i2_hard_offsets_must_be_non_decreasing():
    p = _base()
    p["items"] = [
        {"seq": 0, "duration_ms": 100, "timing_rule": "hard", "start_offset_ms": 900000},
        {"seq": 1, "duration_ms": 200, "timing_rule": "hard", "start_offset_ms": 100000},
    ]
    p["total_duration_ms"] = 300
    errors = check_invariants(p)
    assert any("I2" in e for e in errors)


def test_i3_total_duration_must_equal_sum():
    p = _base()
    p["total_duration_ms"] = 999
    errors = check_invariants(p)
    assert any("I3" in e for e in errors)
