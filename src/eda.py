"""Explore labeled Falcon 9 landing records and save charts."""

import csv
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {
    "Date",
    "Booster Version",
    "Launch Site",
    "Landing Outcome",
    "landing_success",
}
BOOSTER_FAMILY_PATTERN = re.compile(r"^(F9\s+(?:v\d+(?:\.\d+)?|FT|B\d+))")
FIGURE_NAMES = (
    "landing_outcomes.png",
    "landing_success_by_year.png",
    "landing_success_by_site.png",
    "landing_success_by_booster_family.png",
)

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "figure.facecolor": "white",
    }
)

Launch = Dict[str, str]
CategorySummary = Dict[str, Dict[str, float]]


def load_data(data_path: Path) -> List[Launch]:
    """Load labeled CSV records and validate dates and landing labels."""
    with data_path.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                f"Dataset is missing required columns: "
                f"{sorted(REQUIRED_COLUMNS.difference(reader.fieldnames or []))}"
            )

        launches = list(reader)
        if not launches:
            raise ValueError("The labeled dataset contains no records.")

        for line_number, launch in enumerate(launches, start=2):
            if launch["landing_success"] not in {"0", "1"}:
                raise ValueError(
                    f"Invalid landing label on CSV line {line_number}: "
                    f"{launch['landing_success']!r}"
                )
            try:
                datetime.strptime(launch["Date"], "%d-%m-%Y")
            except ValueError:
                pass

    return launches


def _year(launch: Launch) -> Optional[int]:
    try:
        return datetime.strptime(launch["Date"], "%d-%m-%Y").year
    except ValueError:
        return None


def booster_family(version: str) -> str:
    """Group serial-numbered booster versions by their family prefix."""
    normalized = " ".join(version.split())
    match = BOOSTER_FAMILY_PATTERN.match(normalized)
    if match is None:
        raise ValueError(f"Unrecognized Falcon 9 booster version: {version!r}")
    return match.group(1)


def _category_summaries(
    launches: List[Launch], category: str
) -> CategorySummary:
    counts: Counter[str] = Counter()
    successes: Counter[str] = Counter()
    for launch in launches:
        group = (
            booster_family(launch[category])
            if category == "Booster Version"
            else launch[category]
        )
        counts[group] += 1
        successes[group] += int(launch["landing_success"])

    summaries: CategorySummary = {}
    for group, count in counts.items():
        successful = successes[group]
        summaries[group] = {
            "launches": count,
            "successful_landings": successful,
            "unsuccessful_landings": count - successful,
            "success_rate": successful / count,
        }
    return dict(
        sorted(
            summaries.items(),
            key=lambda item: item[1]["success_rate"],
            reverse=True,
        )
    )


def build_summaries(launches: List[Launch]) -> Dict[str, object]:
    """Create outcome, yearly, launch-site, and booster-family summaries."""
    outcome_counts = Counter(
        "Successful" if launch["landing_success"] == "1" else "Unsuccessful"
        for launch in launches
    )

    year_counts: Dict[int, int] = defaultdict(int)
    year_successes: Dict[int, int] = defaultdict(int)
    invalid_date_count = 0
    for launch in launches:
        year = _year(launch)
        if year is None:
            invalid_date_count += 1
            continue
        year_counts[year] += 1
        year_successes[year] += int(launch["landing_success"])

    yearly = {
        year: {
            "launches": count,
            "successful_landings": year_successes[year],
            "unsuccessful_landings": count - year_successes[year],
            "success_rate": year_successes[year] / count,
        }
        for year, count in sorted(year_counts.items())
    }
    return {
        "outcomes": dict(outcome_counts),
        "by_year": yearly,
        "invalid_date_count": invalid_date_count,
        "by_site": _category_summaries(launches, "Launch Site"),
        "by_booster_family": _category_summaries(launches, "Booster Version"),
    }


def create_visualizations(
    launches: List[Launch], output_dir: Path
) -> List[Tuple[str, plt.Figure]]:
    """Create and save four figures from the supplied launch records."""
    existing = [name for name in FIGURE_NAMES if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(
            f"Refusing to overwrite existing figure(s): {', '.join(existing)}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = build_summaries(launches)
    figures: List[Tuple[str, plt.Figure]] = []
    outcome_counts = summaries["outcomes"]
    outcome_names = ["Unsuccessful", "Successful"]
    outcome_values = [outcome_counts.get(name, 0) for name in outcome_names]
    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar(
        outcome_names,
        outcome_values,
        color=["#d95f59", "#268a78"],
        width=0.62,
    )
    axis.bar_label(bars, padding=4, fontsize=11)
    axis.set(title="Falcon 9 First-Stage Landing Outcomes", ylabel="Launches")
    axis.set_ylim(0, max(outcome_values) * 1.15)
    figures.append(("landing_outcomes.png", figure))

    yearly = summaries["by_year"]
    years = list(yearly)
    year_rates = [yearly[year]["success_rate"] * 100 for year in years]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(years, year_rates, marker="o", linewidth=2.5, color="#236b8e")
    for year in years:
        axis.annotate(
            f"n={int(yearly[year]['launches'])}",
            (year, yearly[year]["success_rate"] * 100),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    axis.set(
        title="Landing Success Rate by Launch Year",
        xlabel="Launch year",
        ylabel="Successful landings (%)",
        ylim=(0, 108),
        xticks=years,
    )
    axis.tick_params(axis="x", rotation=45)
    figures.append(("landing_success_by_year.png", figure))

    figures.append(
        _category_figure(
            summaries["by_site"],
            "Landing Success Rate by Launch Site",
            "landing_success_by_site.png",
        )
    )
    figures.append(
        _category_figure(
            summaries["by_booster_family"],
            "Landing Success Rate by Booster Family",
            "landing_success_by_booster_family.png",
        )
    )

    for filename, figure in figures:
        figure.tight_layout()
        figure.savefig(output_dir / filename, dpi=180, bbox_inches="tight")

    return figures


def _category_figure(
    summaries: CategorySummary, title: str, filename: str
) -> Tuple[str, plt.Figure]:
    """Draw category success rates and include each group's sample size."""
    categories = sorted(
        summaries, key=lambda group: summaries[group]["success_rate"]
    )
    labels = [
        f"{category} (n={int(summaries[category]['launches'])})"
        for category in categories
    ]
    rates = [summaries[category]["success_rate"] * 100 for category in categories]
    figure, axis = plt.subplots(figsize=(10, max(4.5, len(categories) * 0.65)))
    bars = axis.barh(labels, rates, color="#268a78")
    colors = plt.get_cmap("viridis")(
        [index / max(len(categories) - 1, 1) for index in range(len(categories))]
    )
    for bar, color, rate in zip(bars, colors, rates):
        bar.set_facecolor(color)
        axis.annotate(
            f"{rate:.0f}%",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
        )
    axis.set(
        title=title,
        xlabel="Successful landings (%)",
        xlim=(0, 112),
    )
    axis.set_axisbelow(True)
    return filename, figure
