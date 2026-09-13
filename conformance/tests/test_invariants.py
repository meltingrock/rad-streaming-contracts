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


def _hard(seq, offset, duration=100):
    return {"seq": seq, "duration_ms": duration, "timing_rule": "hard", "start_offset_ms": offset}


def _plan(items):
    return {"total_duration_ms": sum(i["duration_ms"] for i in items), "items": items}


def test_i4a_rejects_hard_anchors_at_the_same_instant():
    """The live defect: five leaflet lines anchored at the identical offset.

    I1-I3 are all satisfied by this plan, which is why it aired.
    """
    plan = _plan([_hard(i, 900_000) for i in range(5)])
    errors = check_invariants(plan)
    assert any("I4a" in e for e in errors)
    assert not any(e.startswith(("I1", "I2", "I3")) for e in errors), errors


def test_i4a_rejects_a_partial_overlap():
    plan = _plan([_hard(0, 0, 30_000), _hard(1, 20_000, 30_000)])
    errors = check_invariants(plan)
    assert any("I4a" in e for e in errors)


def test_i4a_allows_anchors_that_merely_touch():
    """One ending exactly as the next begins is playable, so it is not an error."""
    plan = _plan([_hard(0, 0, 30_000), _hard(1, 30_000, 30_000)])
    assert check_invariants(plan) == []


def test_i4a_allows_the_phased_placement_that_fixed_the_defect():
    # 09:15, 09:45, 10:15, 10:45, 11:15 as ms-from-hour-start would be in
    # different hours; within one hour, two adverts at :15 and :45.
    plan = _plan([_hard(0, 900_000, 30_000), _hard(1, 2_700_000, 30_000)])
    assert check_invariants(plan) == []


def test_i4a_ignores_soft_items():
    """Music has no offset and cannot overlap an anchor by this measure."""
    plan = {
        "total_duration_ms": 300,
        "items": [
            {"seq": 0, "duration_ms": 100, "timing_rule": "soft", "start_offset_ms": None},
            {"seq": 1, "duration_ms": 200, "timing_rule": "soft", "start_offset_ms": None},
        ],
    }
    assert check_invariants(plan) == []


def test_i4a_is_reported_even_when_i2_is_violated():
    """Offset order, not item order: an I2 breach must not hide an overlap."""
    plan = _plan([_hard(0, 60_000, 30_000), _hard(1, 50_000, 30_000)])
    errors = check_invariants(plan)
    assert any("I2" in e for e in errors)
    assert any("I4a" in e for e in errors)


def test_i4b_is_a_warning_and_never_an_error():
    """An overfull hour still plays in order, so it must not take a store off air."""
    from hourplan_conformance.invariants import check_warnings

    # 121 anchors of 30s, laid end to end: 3,630,000ms, past the hour.
    items = [_hard(i, i * 30_000, 30_000) for i in range(121)]
    plan = _plan(items)
    assert check_invariants(plan) == []          # playable, so no error
    assert any("I4b" in w for w in check_warnings(plan))


def test_i4b_is_quiet_for_an_ordinary_hour():
    from hourplan_conformance.invariants import check_warnings

    assert check_warnings(_plan([_hard(0, 0, 30_000), _hard(1, 60_000, 30_000)])) == []
