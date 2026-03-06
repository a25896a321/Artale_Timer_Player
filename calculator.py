# -*- coding: utf-8 -*-
"""
Artale Timer Player - Calculation Engine  v1.0.1
Author: oo_jump

Terminology:
  base time  – the unknown current timer value (0:10 ~ 11:50, step 10 min)
  MAX_TIME   – 12:00 = 720 min (exclusive upper bound; reaching it is BAD)
  IDEAL_TIME – 11:50 = 710 min (best possible result)
  sequence   – ordered tuple of button operations to apply in succession
"""

from itertools import permutations, combinations
from collections import Counter

# ── Constants ───────────────────────────────────────────────────────────────

MAX_TIME   = 720   # 12:00 exclusive limit
IDEAL_TIME = 710   # 11:50 ideal target
TIME_STEP  = 10    # base-time granularity (minutes)

# Button definitions – value in minutes, or None for ×2
BUTTON_DEFS: dict = {
    '10分': 10,
    '30分': 30,
    '50分': 50,
    '1hr':  60,
    '2hr':  120,
    '4hr':  240,
    '9hr':  540,
    'x2':   None,
}
BUTTON_NAMES = list(BUTTON_DEFS.keys())

# Fixed 5 zones for "best5zones" display mode
# Each tuple: (zone_min_min, zone_max_min, label_zh, label_en)
BEST5_ZONES = [
    (480, 710, "8:00~11:50", "8:00~11:50"),
    (360, 470, "6:00~7:50",  "6:00~7:50"),
    (240, 350, "4:00~5:50",  "4:00~5:50"),
    (120, 230, "2:00~3:50",  "2:00~3:50"),
    (10,  110, "0:10~1:50",  "0:10~1:50"),
]

# ── Core arithmetic ─────────────────────────────────────────────────────────

def apply_op(time_min: int, op: str) -> int:
    """Apply one button operation to a time value (minutes)."""
    return time_min * 2 if op == 'x2' else time_min + BUTTON_DEFS[op]


def simulate_sequence(base_time: int, sequence: tuple) -> tuple:
    """
    Apply a sequence of operations in order.
    Returns (final_time, is_valid).
    is_valid = True iff the time never reached or exceeded MAX_TIME.
    """
    t = base_time
    for op in sequence:
        t = apply_op(t, op)
        if t >= MAX_TIME:
            return t, False
    return t, True


def canonical_seq(seq: tuple) -> tuple:
    """
    Normalise a sequence for deduplication / grouping.
    Additions commute, so sort them alphabetically.
    x2 breaks commutativity, so sequences containing it are kept as-is.
    """
    return seq if 'x2' in seq else tuple(sorted(seq))


# ── Optimal-sequence finder ──────────────────────────────────────────────────

def find_best_sequence(base_time: int, buttons: list) -> tuple:
    """
    Try every non-empty subset / permutation of `buttons` and return
    (best_result, canonical_best_sequence).

    best_result == base_time and sequence == () means "no improvement possible".
    """
    best_result = base_time
    best_seq: tuple = ()

    n = len(buttons)
    for r in range(1, n + 1):
        for idx_combo in combinations(range(n), r):
            subset = tuple(buttons[i] for i in idx_combo)
            for perm in set(permutations(subset)):        # set() removes duplicates
                final_t, valid = simulate_sequence(base_time, perm)
                if valid and final_t > best_result:
                    best_result = final_t
                    best_seq    = canonical_seq(perm)

    return best_result, best_seq


# ── Full result generation ───────────────────────────────────────────────────

def generate_all_results(buttons: list) -> list:
    """
    For every base time 0:10 … 11:50 find the optimal sequence.
    Returns [(base_time, result_time, canonical_sequence), …] sorted ascending.
    """
    return [
        (base, *find_best_sequence(base, buttons))
        for base in range(TIME_STEP, MAX_TIME, TIME_STEP)
    ]


# ── Grouping ─────────────────────────────────────────────────────────────────

def group_results(results: list) -> list:
    """
    Merge consecutive base times that share the same optimal sequence.

    Returns list of (base_start, base_end, min_result, max_result, sequence),
    ordered by base_start ascending.
    """
    if not results:
        return []

    groups = []
    cur_start, cur_result, cur_seq = results[0]
    cur_end   = cur_start
    cur_min   = cur_result
    cur_max   = cur_result

    for base, result, seq in results[1:]:
        if seq == cur_seq:
            cur_end  = base
            cur_min  = min(cur_min, result)
            cur_max  = max(cur_max, result)
        else:
            groups.append((cur_start, cur_end, cur_min, cur_max, cur_seq))
            cur_start = base
            cur_end   = base
            cur_min   = result
            cur_max   = result
            cur_seq   = seq

    groups.append((cur_start, cur_end, cur_min, cur_max, cur_seq))
    return groups


# ── Merge adjacent groups (for simplified display) ───────────────────────────

def merge_adjacent_groups(groups: list) -> list:
    """
    Simplify display: merge adjacent groups whose sequences are prefix-related
    AND where the shorter sequence remains valid across the merged range.
    """
    if len(groups) <= 1:
        return groups

    merged = list(groups)
    changed = True
    while changed:
        changed = False
        new_merged = []
        i = 0
        while i < len(merged):
            if i + 1 < len(merged):
                g1 = merged[i]
                g2 = merged[i + 1]
                s1, s2 = g1[4], g2[4]
                shorter = longer = None
                if len(s1) < len(s2) and s2[:len(s1)] == s1:
                    shorter = s1
                elif len(s2) < len(s1) and s1[:len(s2)] == s2:
                    shorter = s2

                if shorter is not None:
                    all_bases = list(range(
                        min(g1[0], g2[0]),
                        max(g1[1], g2[1]) + TIME_STEP,
                        TIME_STEP,
                    ))
                    can_merge = all(
                        simulate_sequence(b, shorter)[1] for b in all_bases
                    )
                    if can_merge:
                        results = [simulate_sequence(b, shorter)[0] for b in all_bases]
                        new_merged.append((
                            min(g1[0], g2[0]), max(g1[1], g2[1]),
                            min(results), max(results), shorter,
                        ))
                        i += 2
                        changed = True
                        continue

            new_merged.append(merged[i])
            i += 1
        merged = new_merged

    return merged


# ── Sorting ───────────────────────────────────────────────────────────────────

def sort_groups(groups: list, sort_order: str) -> list:
    """
    Sort and optionally trim groups.

    sort_order values:
      'base_desc'   – highest base end first
      'base_asc'    – lowest base start first
      'result_desc' – highest max_result first (推估值大→小)
      'result_asc'  – lowest max_result first  (推估值小→大)
      'best5zones'  – handled separately in compute_best5zones()
    """
    if sort_order == 'base_desc':
        return sorted(groups, key=lambda g: g[1], reverse=True)
    elif sort_order == 'base_asc':
        return sorted(groups, key=lambda g: g[0])
    elif sort_order == 'result_desc':
        return sorted(groups, key=lambda g: g[3], reverse=True)   # g[3] = max_result
    elif sort_order == 'result_asc':
        return sorted(groups, key=lambda g: g[3])
    return groups


# ── Formatting helpers ────────────────────────────────────────────────────────

def minutes_to_str(minutes: int) -> str:
    """Convert minutes to H:MM display string."""
    return f"{minutes // 60}:{minutes % 60:02d}"


def format_sequence(seq: tuple, lang: str = 'zh',
                    show_any_hint: bool = True,
                    show_seq_hint: bool = True) -> str:
    """
    Convert an action sequence tuple to a readable string.

    show_any_hint – append （任意）/(any) for commutative sequences
    show_seq_hint – append （依序）/(in order) for ordered sequences
    """
    if not seq:
        return '無需操作' if lang == 'zh' else 'No action'

    if len(seq) == 1:
        return seq[0]

    has_x2 = 'x2' in seq
    if lang == 'zh':
        if not has_x2:
            return '、'.join(seq) + ('（任意）' if show_any_hint else '')
        return ' → '.join(seq) + ('（依序）' if show_seq_hint else '')
    else:
        if not has_x2:
            return ', '.join(seq) + (' (any)' if show_any_hint else '')
        return ' → '.join(seq) + (' (in order)' if show_seq_hint else '')


def _result_range_str(min_r: int, max_r: int) -> str:
    if min_r == max_r:
        return minutes_to_str(min_r)
    return f"{minutes_to_str(min_r)}~{minutes_to_str(max_r)}"


def format_header(lang: str = 'zh',
                  show_number: bool = True,
                  show_estimate: bool = True) -> str:
    """
    Return the column header line + separator.
    Columns are separated by \\t so the Text widget can align them via tab stops.
    Tab order: [編號\\t] 基礎時間\\t 建議操作\\t [推估值]
    """
    parts = []
    if show_number:
        parts.append('編號' if lang == 'zh' else '#')
        parts.append('\t')
    parts.append('基礎時間範圍' if lang == 'zh' else 'Base Time Range')
    parts.append('\t')
    parts.append('建議操作' if lang == 'zh' else 'Suggested Action')
    if show_estimate:
        parts.append('\t')
        parts.append('推估值' if lang == 'zh' else 'Est. Result')
    header = ''.join(parts)
    sep = '─' * 120
    return header + '\n' + sep


def format_group_tagged(group: tuple, index: int,
                        lang: str = 'zh',
                        show_number: bool = True,
                        show_estimate: bool = True,
                        show_any_hint: bool = True,
                        show_seq_hint: bool = True) -> list:
    """
    Return a list of (text_fragment, tag_name) tuples for one result row.
    Tags: 'col_num', 'col_range', 'col_action', 'col_estimate', 'newline'
    """
    base_start, base_end, min_result, max_result, seq = group

    # 編號
    case_str = f"第{index + 1}種" if lang == 'zh' else f"Case {index + 1}"

    # 基礎時間範圍
    if base_start == base_end:
        range_str = minutes_to_str(base_start)
    else:
        range_str = f"{minutes_to_str(base_start)}~{minutes_to_str(base_end)}"

    # 建議操作
    action_str = format_sequence(seq, lang, show_any_hint, show_seq_hint)

    # 推估值
    result_str = _result_range_str(min_result, max_result)

    # Columns separated by \t; the Text widget uses configured tab stops
    # for pixel-accurate alignment regardless of CJK / ASCII mix.
    parts = []
    if show_number:
        parts.append((case_str + '\t', 'col_num'))
    parts.append((range_str + '\t', 'col_range'))
    parts.append((action_str + '\t', 'col_action'))
    if show_estimate:
        parts.append((result_str, 'col_estimate'))
    parts.append(('\n', 'newline'))
    return parts


def format_group_plain(group: tuple, index: int,
                       lang: str = 'zh',
                       show_number: bool = True,
                       show_estimate: bool = True,
                       show_any_hint: bool = True,
                       show_seq_hint: bool = True) -> str:
    """Plain-text version of format_group_tagged (for float window etc.)."""
    return "".join(t for t, _ in format_group_tagged(
        group, index, lang, show_number, show_estimate,
        show_any_hint, show_seq_hint))


# ── 5-zone mode ───────────────────────────────────────────────────────────────

def compute_best5zones(buttons: list,
                       lang: str = 'zh',
                       show_number: bool = True,
                       show_estimate: bool = True,
                       show_any_hint: bool = True,
                       show_seq_hint: bool = True) -> list:
    """
    For each of the 5 fixed base-time zones, find the most commonly recommended
    sequence and compute the result range when that sequence is applied.

    Returns list of tagged-part lists (same format as format_group_tagged),
    prefixed by header tagged-parts.
    """
    header_text = format_header(lang, show_number, show_estimate)
    header_parts = [(line + '\n', 'header') for line in header_text.splitlines()]

    zone_rows: list[list] = []
    for i, (z_min, z_max, lbl_zh, lbl_en) in enumerate(BEST5_ZONES):
        base_times = list(range(z_min, z_max + TIME_STEP, TIME_STEP))
        zone_label = lbl_zh if lang == 'zh' else lbl_en

        # Count optimal sequences across the zone
        seq_freq: Counter = Counter()
        seq_best: dict = {}
        for base in base_times:
            result, seq = find_best_sequence(base, buttons)
            seq_freq[seq] += 1
            seq_best[seq] = max(seq_best.get(seq, 0), result)

        # Most-frequent, tie-break by highest result
        best_seq = max(seq_freq, key=lambda s: (seq_freq[s], seq_best.get(s, 0)))

        # Result range for best_seq across zone
        valid_res = []
        for base in base_times:
            if not best_seq:
                valid_res.append(base)
            else:
                t, ok = simulate_sequence(base, best_seq)
                if ok:
                    valid_res.append(t)

        if valid_res:
            res_str = _result_range_str(min(valid_res), max(valid_res))
        else:
            res_str = "—"

        action_str = format_sequence(best_seq, lang, show_any_hint, show_seq_hint)
        case_str   = f"第{i + 1}種" if lang == 'zh' else f"Case {i + 1}"

        row_parts = []
        if show_number:
            row_parts.append((case_str + '\t', 'col_num'))
        row_parts.append((zone_label + '\t', 'col_range'))
        row_parts.append((action_str + '\t', 'col_action'))
        if show_estimate:
            row_parts.append((res_str, 'col_estimate'))
        row_parts.append(('\n', 'newline'))
        zone_rows.append(row_parts)

    return header_parts + zone_rows


# ── Main pipeline ─────────────────────────────────────────────────────────────

def compute_tagged_results(buttons: list,
                           sort_order: str,
                           lang: str = 'zh',
                           show_number: bool = True,
                           show_estimate: bool = True,
                           show_any_hint: bool = True,
                           show_seq_hint: bool = True) -> list:
    """
    Full pipeline for the main results Text widget.
    Returns list of (text_fragment, tag_name) tuples.
    Accepts any number of buttons (1–4).
    """
    if not buttons:
        from translations import TRANSLATIONS
        msg = TRANSLATIONS.get(lang, TRANSLATIONS['zh'])['results_empty']
        return [(msg, 'muted')]

    if sort_order == 'best5zones':
        return compute_best5zones(buttons, lang, show_number, show_estimate,
                                   show_any_hint, show_seq_hint)

    raw     = generate_all_results(buttons)
    groups  = group_results(raw)
    sorted_ = sort_groups(groups, sort_order)

    header_text  = format_header(lang, show_number, show_estimate)
    header_parts = [(line + '\n', 'header') for line in header_text.splitlines()]

    row_parts = []
    for i, g in enumerate(sorted_):
        row_parts.extend(format_group_tagged(g, i, lang, show_number, show_estimate,
                                              show_any_hint, show_seq_hint))

    return header_parts + row_parts


def compute_plain_results(buttons: list,
                          sort_order: str,
                          lang: str = 'zh',
                          show_number: bool = True,
                          show_estimate: bool = True,
                          show_any_hint: bool = True,
                          show_seq_hint: bool = True) -> str:
    """Plain-text version for float window / copy-paste."""
    tagged = compute_tagged_results(buttons, sort_order, lang, show_number,
                                    show_estimate, show_any_hint, show_seq_hint)
    return "".join(t for t, _ in tagged)
