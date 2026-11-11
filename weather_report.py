"""Build a self-contained comparison report for offline viewing and printing."""

from html import escape

SERIES = (("Selected", "#087c68"), ("Reference", "#3b5ba9"))


def daily_chart(selected, reference, key, label, *, rainfall=False):
    periods = (selected["daily_weather"], reference["daily_weather"])
    values = [row[key] for period in periods for row in period if row[key] is not None]
    if not values:
        return f"<h2>{label}</h2><p>No daily readings available.</p>"

    days = max(map(len, periods))
    low, high = (0, max(values)) if rainfall else (min(values), max(values))
    if high <= low:
        high = low + 1
    step = 610 / days
    marks = []
    for tick in range(3):
        y = 32 + tick * 58
        value = high - (high - low) * tick / 2
        marks.append(f'<path d="M54 {y} H664" stroke="#d4dce1"/>')
        marks.append(f'<text x="48" y="{y + 4}" text-anchor="end">{value:.1f}</text>')
    for index, ((_, color), period) in enumerate(zip(SERIES, periods)):
        previous = None
        for row in period:
            value = row[key]
            if value is None:
                previous = None
                continue
            x = 54 + step * (row["day"] - 0.5)
            y = 148 - 116 * (value - low) / (high - low)
            if rainfall:
                bar_x = x + (index - 1) * step * 0.34
                marks.append(f'<rect x="{bar_x:.2f}" y="{y:.2f}" width="{step * .34:.2f}" height="{148 - y:.2f}" fill="{color}"/>')
            else:
                if previous is not None:
                    px, py = previous
                    marks.append(f'<path d="M{px:.2f} {py:.2f} L{x:.2f} {y:.2f}" stroke="{color}" stroke-width="2"/>')
                marks.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.7" fill="{color}"/>')
                previous = x, y
    ticks = '<text x="54" y="168">Day 1</text>'
    if days > 1:
        ticks += f'<text x="664" y="168" text-anchor="end">Day {days}</text>'
    return (
        f'<h2>{label}</h2><svg viewBox="0 0 680 175" role="img" aria-label="{label} by day">'
        f'{"".join(marks)}{ticks}</svg>'
    )


def comparison_report(selected, reference, rows):
    headers = ("Metric", "Reference", "Selected", "Selected minus reference")
    headings = "".join(f"<th scope='col'>{heading}</th>" for heading in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(row[heading]))}</td>" for heading in headers) + "</tr>"
        for row in rows
    )
    dates = "".join(
        f"<li><strong>{name}</strong> {escape(period['start_date'])} to {escape(period['end_date'])}</li>"
        for (name, _), period in zip(SERIES, (selected, reference))
    )
    legend = " &nbsp; ".join(f'<span style="color:{color}">● {name}</span>' for name, color in SERIES)
    duration_note = ""
    if (selected["start_date"], selected["end_date"]) == (reference["start_date"], reference["end_date"]):
        duration_note = "<p>Both periods use the same dates.</p>"
    elif selected["expected_days"] != reference["expected_days"]:
        duration_note = "<p>Rainfall totals cover different numbers of days.</p>"
    temperature = daily_chart(selected, reference, "T2M", "Daily temperature (°C)")
    rainfall = daily_chart(selected, reference, "rainfall_mm", "Daily rainfall (mm)", rainfall=True)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Field Shift | Wheat season comparison</title>
<style>
body {{ max-width: 740px; margin: 28px auto; padding: 0 18px; color: #17282e; font: 15px/1.4 system-ui, sans-serif; }}
h1 {{ margin: 0; }} h2 {{ font-size: 16px; margin: 14px 0 0; }}
table {{ width: 100%; border-collapse: collapse; }} th,td {{ border-bottom: 1px solid #d4dce1; padding: 7px; text-align: left; }}
svg {{ display: block; width: 100%; font: 12px system-ui, sans-serif; }}
footer {{ color: #3c5059; font-size: 13px; }}
@media print {{ body {{ margin: 0 auto; }} section, table {{ break-inside: avoid; }} }}
</style></head><body>
<header><p>FIELD SHIFT</p><h1>Wheat season comparison</h1>
<p>Requested coordinates {selected['requested_latitude']:.6f}°, {selected['requested_longitude']:.6f}°</p>
<ul>{dates}</ul></header>
<table><thead><tr>{headings}</tr></thead><tbody>{body}</tbody></table>
{duration_note}<p>{legend} · Day 1 is the start of each period.</p>
<section>{temperature}</section><section>{rainfall}</section>
<footer>Source: NASA POWER daily grid estimates (UTC). Dates are inclusive. Humidity differences are in percentage points (pp).
Grid estimates describe the area around the coordinates. Crop rankings use separate regional inputs.</footer>
</body></html>"""
