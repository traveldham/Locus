"""Match a model's suggestion back to the finding it answers.

Models sometimes put the field name where the rule id belongs, or drop the subject.
The exact (rule, subject) key is tried first; then the field plus subject; then the
field alone when only one finding wants that field. Anything still ambiguous is dropped.
"""


def resolve_target(by_key: dict[tuple[str, str], dict], raw: dict, suggests: dict[str, str]):
    rule = str(raw.get("rule") or "")
    subject = str(raw.get("subject") or "")
    field = str(raw.get("field") or "")
    exact = by_key.get((rule, subject))
    if exact is not None:
        return exact
    wanted = field or (rule if rule in set(suggests.values()) else "")
    if not wanted:
        return None
    candidates = [
        item
        for (item_rule, item_subject), item in by_key.items()
        if suggests.get(item_rule) == wanted and (not subject or item_subject == subject)
    ]
    if len(candidates) == 1:
        return candidates[0]
    if subject:
        # Several findings want this field for the same subject: prefer the rule named.
        named = [c for c in candidates if c["rule"] == rule]
        return named[0] if len(named) == 1 else None
    return None
