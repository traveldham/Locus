from app.services.recommendations.context import Context, day
from app.services.recommendations.policy import graded

URGENT = ("phone_primary", "website_uri", "has_voice_of_merchant")


def evaluate_profile(c: Context):
    loc = c.location
    href = f"/locations/{loc['id']}"
    fields = [f for f in ("phone_primary", "website_uri", "description") if not loc.get(f)]
    if not c.rows("hours"):
        fields.append("hours")
    if loc.get("has_voice_of_merchant") is False:
        fields.append("has_voice_of_merchant")
    if loc.get("open_status") == "closed_permanently":
        c.assess("profile", "suppressed", "Permanently closed: no profile growth actions.")
    elif fields:
        urgent = [f for f in fields if f in URGENT]
        # Severity rises with how many customer-facing fields are unusable, and starts
        # higher when a customer cannot call, click through or trust the listing.
        spread = (len(fields) - 1) / 4
        score = graded(80, spread, 14, 94) if urgent else graded(48, spread, 12, 60)
        c.assess("profile", "triggered", f"{len(fields)} essential fields need confirmation.", 1)
        c.emit(
            "profile",
            "Confirm and complete customer-facing information",
            "Check the missing fields with the location manager, then update only confirmed "
            "information: " + ", ".join(fields) + ".",
            f"{len(fields)} essential profile fields need confirmation"
            + (f", including {', '.join(urgent)}." if urgent else "."),
            score,
            [
                c.evidence(
                    "locations",
                    [loc],
                    [f for f in fields if f != "hours"],
                    "Missing or unverified fields in current profile",
                    missing_fields=fields,
                    urgent_fields=urgent,
                )
            ],
            href,
            "This is current stored profile state; no historical reconstruction. "
            "No claim that completing fields improves rank.",
            "high",
        )
    else:
        c.assess("profile", "clear", "Essential profile fields are populated.")

    catalog = [
        r
        for r in c.snapshot.get("catalog", [])
        if r.get("applies_to_category", "").casefold()
        == (loc.get("primary_category_display") or "").casefold()
    ]
    assigned = {
        r["attribute_id"].removeprefix("attributes/")
        for r in c.rows("attributes")
        if r.get("values") and any(value is not None for value in r["values"])
    }
    missing = [r for r in catalog if r["attribute_name"] not in assigned]
    if not catalog:
        c.assess("attributes", "insufficient_data", "No matching category catalog.")
    elif loc.get("open_status") != "open":
        c.assess("attributes", "suppressed", "Only evaluate active locations.")
    elif missing:
        share = len(missing) / len(catalog)
        c.assess(
            "attributes",
            "triggered",
            f"{len(missing)} of {len(catalog)} category attributes are unset.",
            1,
        )
        c.emit(
            "attributes",
            "Confirm unset attributes with the location manager",
            "Review these available attributes; record true or false only after confirmation: "
            + ", ".join(r["attribute_name"] for r in missing)
            + ".",
            f"{len(missing)} of {len(catalog)} category attributes are unset ({share:.0%}).",
            graded(25, share, 20, 45),
            [
                c.evidence(
                    "catalog",
                    catalog,
                    ["attribute_name", "applies_to_category"],
                    "Catalog minus assigned attribute names",
                    available=len(catalog),
                    unset=len(missing),
                    unset_share=round(share, 4),
                    missing=[r["attribute_name"] for r in missing],
                ),
                c.evidence(
                    "attributes",
                    c.rows("attributes"),
                    ["attribute_id", "values"],
                    "Explicit FALSE counts as configured",
                    assigned=len(assigned),
                ),
            ],
            href,
            "Availability does not mean applicability. Never enable unsupported services.",
        )
    else:
        c.assess("attributes", "clear", "All catalog attributes are configured.")

    media = c.rows("media")
    if not media:
        c.assess("media", "insufficient_data", "No photo summary; absence is not zero photos.")
    elif loc.get("open_status") != "open":
        c.assess("media", "suppressed", "Only evaluate active locations.")
    else:
        row = media[0]
        missing_photos = [
            k for k in ("has_profile_photo", "has_cover_photo") if row.get(k) is False
        ]
        if missing_photos:
            c.assess(
                "media",
                "triggered",
                f"{len(missing_photos)} profile images are explicitly marked missing.",
                1,
            )
            c.emit(
                "media",
                "Add missing profile imagery",
                "Ask the manager for accurate, current imagery for: "
                + ", ".join(missing_photos)
                + ". Review before uploading.",
                "The photo summary explicitly marks these images as missing: "
                + ", ".join(missing_photos)
                + ".",
                graded(40, len(missing_photos) - 1, 8, 48),
                [
                    c.evidence(
                        "media",
                        media,
                        missing_photos,
                        "Explicit false image flags",
                        missing=missing_photos,
                    )
                ],
                "/insights/photos",
                "Counts cannot establish photo quality; no ranking uplift is inferred.",
                "high",
            )
        elif any(row.get(k) is None for k in ("has_profile_photo", "has_cover_photo")):
            c.assess("media", "insufficient_data", "Profile or cover image state is unknown.")
        else:
            c.assess("media", "clear", "No explicitly missing profile or cover image.")

    posts = [
        r
        for r in c.rows("posts")
        if day(r.get("published_on")) and day(r["published_on"]) <= c.as_of
    ]
    if loc.get("open_status") != "open":
        c.assess("posts", "suppressed", "Only evaluate active locations.")
    elif not posts:
        c.assess(
            "posts", "insufficient_data", "No dated posts; cannot establish feed completeness."
        )
    else:
        latest = max(posts, key=lambda r: r["published_on"])
        gap = (c.as_of - day(latest["published_on"])).days
        if gap >= c.config.post_gap_days:
            over = (gap - c.config.post_gap_days) / c.config.post_gap_days
            c.assess("posts", "triggered", f"Last recorded post was {gap} days ago.", 1)
            c.emit(
                "posts",
                "Check whether a useful customer update is overdue",
                "Confirm the post history is current; publish an accurate update only if "
                "there is useful news, a real event or an available offer.",
                f"The last recorded post was {gap} days before the analysis date, "
                f"past the {c.config.post_gap_days}-day policy window.",
                graded(25, over, 20, 45),
                [
                    c.evidence(
                        "posts",
                        [latest],
                        ["published_on", "post_type", "cta_type"],
                        "as_of minus latest published_on",
                        gap_days=gap,
                        threshold_days=c.config.post_gap_days,
                    )
                ],
                "/posts",
                "An incomplete export can explain the gap. Posting cadence is not a rank factor "
                "established by this dataset.",
            )
        else:
            c.assess("posts", "clear", "A post falls within the configured recency window.")
