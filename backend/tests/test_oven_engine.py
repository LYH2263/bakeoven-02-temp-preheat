from app.services.oven_engine import (
    Interval,
    Occupancy,
    RecipeDurations,
    build_occupancies,
    find_conflicts,
    latest_tier_before,
    next_free_window,
    plan_preheat,
)


def test_half_open_no_touch_conflict():
    a = Occupancy(1, Interval(0, 30), "bake", 1)
    b = Occupancy(1, Interval(30, 60), "bake", 2)
    assert find_conflicts([a], [b]) == []


def test_overlap_detected():
    recipe = RecipeDurations(20, 30)
    cand = build_occupancies(1, 9, 10, recipe)
    existing = [Occupancy(1, Interval(25, 40), "bake", 1)]
    assert find_conflicts(existing, cand)


def test_next_free_window_after_busy():
    existing = [
        Occupancy(1, Interval(0, 40), "ferment", 1),
        Occupancy(1, Interval(40, 70), "bake", 1),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(70, 100)


def test_next_free_in_gap():
    existing = [
        Occupancy(1, Interval(0, 20), "bake", 1),
        Occupancy(1, Interval(80, 100), "bake", 2),
    ]
    w = next_free_window(existing, 1, duration=30, search_from=0)
    assert w == Interval(20, 50)


def test_plan_preheat_on_tier_switch():
    assert plan_preheat("高温", "中温", 15, 630) == Interval(615, 630)


def test_plan_preheat_skipped_when_same_tier_or_no_previous():
    assert plan_preheat("中温", "中温", 15, 630) is None
    assert plan_preheat(None, "中温", 15, 630) is None
    assert plan_preheat("高温", "中温", 0, 630) is None


def test_build_occupancies_with_preheat():
    occ = build_occupancies(1, 9, 100, RecipeDurations(20, 30), preheat_min=10)
    assert [(o.phase, o.interval) for o in occ] == [
        ("preheat", Interval(90, 100)),
        ("ferment", Interval(100, 120)),
        ("bake", Interval(120, 150)),
    ]


def test_build_occupancies_without_preheat_by_default():
    occ = build_occupancies(1, 9, 100, RecipeDurations(20, 30))
    assert [o.phase for o in occ] == ["ferment", "bake"]


def test_preheat_segment_occupies_oven():
    # 上一批 9:00-10:00 占炉，新批 10:30 开工需 15 分钟预热 → 不重叠
    existing = [Occupancy(1, Interval(540, 600), "bake", 1)]
    preheat = plan_preheat("高温", "中温", 15, 630)
    cand = [Occupancy(1, preheat, "preheat", 2)]
    assert find_conflicts(existing, cand) == []


def test_preheat_conflict_with_existing_occupancy():
    # 上一批 9:00-10:10 占炉，新批 10:20 开工需 15 分钟预热 → 预热段 10:05-10:20 与之重叠
    existing = [Occupancy(1, Interval(540, 610), "bake", 1)]
    preheat = plan_preheat("高温", "中温", 15, 620)
    cand = [Occupancy(1, preheat, "preheat", 2)]
    hits = find_conflicts(existing, cand)
    assert hits and hits[0][1].phase == "preheat"


def test_preheat_touching_half_open_no_conflict():
    # 半开区间：预热段起点恰好等于上一批终点不算重叠
    existing = [Occupancy(1, Interval(540, 600), "bake", 1)]
    cand = [Occupancy(1, Interval(600, 615), "preheat", 2)]
    assert find_conflicts(existing, cand) == []


def test_latest_tier_before_picks_immediately_previous():
    ends = [(600, "高温"), (675, "中温"), (800, "低温")]
    assert latest_tier_before(ends, 690) == "中温"
    assert latest_tier_before(ends, 600) == "高温"  # 紧贴上一批终点也算上一档
    assert latest_tier_before(ends, 500) is None    # 前面没有批次则不预热


def _schedule(existing, oven_id, start_min, recipe, new_tier, oven_preheat, prev_ends):
    """与 create_batch 相同的判定流程：先查发酵/烘烤重叠，再按需插预热。"""
    cand = build_occupancies(oven_id, -1, start_min, recipe)
    if find_conflicts(existing, cand):
        return None, "overlap"
    preheat = plan_preheat(latest_tier_before(prev_ends, start_min), new_tier, oven_preheat, start_min)
    if preheat is not None:
        if find_conflicts(existing, [Occupancy(oven_id, preheat, "preheat", -1)]):
            return None, "preheat_conflict"
        return build_occupancies(oven_id, -1, start_min, recipe, oven_preheat), "ok"
    return cand, "ok"


def test_scenario_tier_switch_inserts_preheat_once():
    # 炉上已有 高温批 9:00-10:15；10:30 排入 中温批 → 预热 10:15-10:30
    occ_a = build_occupancies(1, 1, 540, RecipeDurations(40, 35))
    new, status = _schedule(occ_a, 1, 630, RecipeDurations(25, 20), "中温", 15, [(615, "高温")])
    assert status == "ok"
    assert [(o.phase, o.interval) for o in new] == [
        ("preheat", Interval(615, 630)),
        ("ferment", Interval(630, 655)),
        ("bake", Interval(655, 675)),
    ]
    # 同档紧跟其后 11:15 再排 中温批 → 不得多出预热条
    existing = occ_a + new
    new2, status = _schedule(existing, 1, 675, RecipeDurations(25, 20), "中温", 15, [(615, "高温"), (675, "中温")])
    assert status == "ok"
    assert [o.phase for o in new2] == ["ferment", "bake"]


def test_scenario_preheat_blocked_by_previous_batch():
    # 高温批 9:00-10:20 占炉；中温批 10:30 开工需 15 分钟预热 → 预热段 10:15-10:30 与烘烤重叠
    occ_a = build_occupancies(1, 1, 540, RecipeDurations(40, 40))
    new, status = _schedule(occ_a, 1, 630, RecipeDurations(25, 20), "中温", 15, [(620, "高温")])
    assert new is None and status == "preheat_conflict"
