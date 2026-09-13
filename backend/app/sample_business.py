"""Business-level demo metadata derived from the supplied synthetic export."""

import csv
from urllib.parse import urlsplit

from app.services.providers.sample_data import data_dir


def populate_business(project):
    """Fill only missing values. Never overwrite an operator's business details."""
    with (data_dir() / "locations.csv").open(encoding="utf-8-sig", newline="") as source:
        locations = list(csv.DictReader(source))
    with (data_dir() / "booking_requests.csv").open(encoding="utf-8-sig", newline="") as source:
        services = sorted(
            {r["service"].strip() for r in csv.DictReader(source) if r["service"].strip()}
        )
    urls = [urlsplit(row["website_url"]) for row in locations if row.get("website_url")]
    if not project.website_url and urls:
        project.website_url = f"{urls[0].scheme}://{urls[0].netloc}/"
    if not project.services:
        project.services = services
    if not project.description:
        project.description = (
            "Brightpath Dental is a synthetic multi-location dental group with clinics in "
            "Texas and Arizona. Its recorded appointment services include "
            + ", ".join(services)
            + ". Service availability varies by location."
        )
