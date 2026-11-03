"""
 Sales Analytics Without Pandas

"""
import csv
import math 
from pathlib import Path

DATA_PATH = Path("data") / "electronics_sales.csv"
OUTPUT_PATH = Path("output") / "sales_report.txt"
THRESHOLD = 50_000


def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows."""
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
    return rows


def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None."""

    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    value = value.replace(",", "")

    if value.upper().startswith("KES"):
        value = value[3:].strip()

    try:
           number = float(value)
    except ValueError:
           return None
    return number if math.isfinite(number) else None


def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return cleaned rows and skipped rows with reasons."""

    clean_rows = []
    skipped_rows = []

    for row in rows:
        quantity = parse_number(row["quantity"])
        unit_price = parse_number(row["unit_price_kes"])

        reason = None

        if quantity is None:
            reason = f"quantity not usable ({row['quantity']!r})"
        elif not quantity.is_integer():
            reason = f"quantity must be a whole number ({row['quantity']!r})"
        elif quantity <= 0:
            reason = f"quantity must be greater than zero ({row['quantity']!r})"
        elif unit_price is None:
            reason = f"unit price not usable ({row['unit_price_kes']!r})"
        elif unit_price <= 0:
            reason = f"unit price must be greater than zero ({row['unit_price_kes']!r})"

        if reason is not None:
            skipped_rows.append({**row, "reason": reason})
            continue

        cleaned_row = row.copy()
        cleaned_row["quantity"] = int(quantity)
        cleaned_row["unit_price_kes"] = unit_price
        cleaned_row["revenue"] = cleaned_row["quantity"] * unit_price

        clean_rows.append(cleaned_row)

    return clean_rows, skipped_rows


def total_revenue(rows: list[dict]) -> float:
    """Calculate total revenue from all valid sales transactions."""
    total = 0.0
    for row in rows:
        total += row["revenue"]
    return total


def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Total revenue grouped by any column (product, store, payment_method...)."""
    totals: dict[str, float] = {}
    for row in rows:
        key = row[field]
        if key in totals:
            totals[key] += row["revenue"]
        else:
            totals[key] = row["revenue"]
    return totals


def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest-revenue items, highest first.

    Ties on revenue are broken alphabetically by name.
    """

    ranked = sorted(
        totals.items(),
        key=lambda item: (-item[1], item[0])
    )

    return ranked[:n]


def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension)."""
    return [row for row in rows if row["revenue"] >= threshold]


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate the mean of an empty list.")
    total = 0.0
    for v in values:
        total += v
    return total / len(values)


def median(values: list[float]) -> float:
    """Calculate the median of a list of values."""

    if not values:
        raise ValueError("median() needs at least one value; got an empty list")

    sorted_values = sorted(values)
    n = len(sorted_values)
    middle = n // 2

    if n % 2 == 1:
        return sorted_values[middle]

    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def minimum_maximum(values: list[float]) -> tuple[float, float]:
    """Return the smallest and largest values without min() or max()."""

    if not values:
        raise ValueError("Cannot find minimum and maximum of an empty list.")

    smallest = values[0]
    largest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value

        if value > largest:
            largest = value

    return smallest, largest



def verify_with_pandas(path: Path, my_results: dict) -> list[str]:
    """Recompute the analysis with pandas and compare it with the pure-Python results.

    Cleaning rules mirror parse_number() / convert_rows(): strip whitespace and a
    leading 'KES', remove every comma, accept only finite numbers, then require a
    positive whole-number quantity and a positive unit price. Keep the two in sync.

    my_results must contain these keys:
        valid_count, skipped_count, total_revenue, mean_revenue, median_revenue,
        minimum_revenue, maximum_revenue, product_revenue, store_revenue,
        payment_method_revenue (dicts of field value -> revenue),
        top_products (list of (product, revenue) tuples).

    Returns the report lines, so the caller can print them and save them.
    """
    try:
        import pandas as pd
    except ImportError:
        return ["pandas is not installed - verification skipped"]

    # Read every value as text so pandas cannot convert 'N/A' or '38,999' itself.
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    def pandas_parse_number(value):
        value = value.strip()
        if value.upper().startswith("KES"):
            value = value[3:].strip()
        value = value.replace(",", "")
        if not value:
            return float("nan")
        try:
            number = float(value)
        except ValueError:
            return float("nan")
        return number if math.isfinite(number) else float("nan")

    df["quantity"] = df["quantity"].map(pandas_parse_number)
    df["unit_price_kes"] = df["unit_price_kes"].map(pandas_parse_number)

    valid_mask = (
        (df["quantity"] > 0)
        & (df["quantity"] % 1 == 0)
        & (df["unit_price_kes"] > 0)
    )  # comparisons with NaN are False, so unparseable rows are excluded
    clean_df = df.loc[valid_mask].copy()
    clean_df["revenue"] = clean_df["quantity"] * clean_df["unit_price_kes"]

    def close(a, b):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=0.01)

    def dicts_match(pure, theirs):
        return pure.keys() == theirs.keys() and all(close(pure[k], theirs[k]) for k in pure)

    # Each result is computed once: (label, matched, pure value, pandas value).
    results = []

    pd_total = float(clean_df["revenue"].sum())
    results.append(("Total revenue", close(my_results["total_revenue"], pd_total),
                    my_results["total_revenue"], pd_total))

    by_product = clean_df.groupby("product")["revenue"].sum().to_dict()
    results.append(("Revenue by product",
                    dicts_match(my_results["product_revenue"], by_product),
                    my_results["product_revenue"], by_product))

    pd_top = sorted(by_product.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    pure_top = my_results["top_products"]
    top_ok = len(pd_top) == len(pure_top) and all(
        a[0] == b[0] and close(a[1], b[1]) for a, b in zip(pure_top, pd_top)
    )
    results.append(("Top 3", top_ok, pure_top, pd_top))

    pd_mean = float(clean_df["revenue"].mean())
    pd_median = float(clean_df["revenue"].median())
    pure_pair = (my_results["mean_revenue"], my_results["median_revenue"])
    results.append(("Mean / median",
                    close(pure_pair[0], pd_mean) and close(pure_pair[1], pd_median),
                    pure_pair, (pd_mean, pd_median)))

    # Extra checks beyond the four required lines.
    pd_min = float(clean_df["revenue"].min())
    pd_max = float(clean_df["revenue"].max())
    results.append(("Min / max",
                    close(my_results["minimum_revenue"], pd_min)
                    and close(my_results["maximum_revenue"], pd_max),
                    (my_results["minimum_revenue"], my_results["maximum_revenue"]),
                    (pd_min, pd_max)))

    pd_valid, pd_skipped = len(clean_df), int((~valid_mask).sum())
    results.append(("Rows used / skipped",
                    pd_valid == my_results["valid_count"]
                    and pd_skipped == my_results["skipped_count"],
                    (my_results["valid_count"], my_results["skipped_count"]),
                    (pd_valid, pd_skipped)))

    for field, label in [("store", "Revenue by store"),
                         ("payment_method", "Revenue by payment")]:
        theirs = clean_df.groupby(field)["revenue"].sum().to_dict()
        pure = my_results[f"{field}_revenue"]
        results.append((label, dicts_match(pure, theirs), pure, theirs))

    lines = []
    for label, matched, pure, theirs in results:
        status = "MATCH" if matched else f"MISMATCH (pure={pure}, pandas={theirs})"
        lines.append(f"{label:<19}: {status}")
    return lines


def analyse(path: Path = DATA_PATH, threshold: float = THRESHOLD) -> dict:
    """Run the full analysis and return every result in one dict.

    The same dict is passed to verify_with_pandas() and build_report(), so the
    report and the verification always use identical numbers.
    """
    rows = read_sales(path)
    clean_rows, skipped_rows = convert_rows(rows)

    revenues = [row["revenue"] for row in clean_rows]
    minimum, maximum = minimum_maximum(revenues)

    product_revenue = revenue_by(clean_rows, "product")
    store_revenue = revenue_by(clean_rows, "store")
    payment_method_revenue = revenue_by(clean_rows, "payment_method")

    high_sales = high_value(clean_rows, threshold)
    high_sales_by_store = {
        store: len([sale for sale in high_sales if sale["store"] == store])
        for store in sorted(store_revenue)
    }

    return {
        "columns": list(rows[0].keys()) if rows else [],
        "rows_read": len(rows),
        "valid_count": len(clean_rows),
        "skipped_count": len(skipped_rows),
        "skipped_rows": skipped_rows,
        "threshold": threshold,
        "total_revenue": total_revenue(clean_rows),
        "mean_revenue": mean(revenues),
        "median_revenue": median(revenues),
        "minimum_revenue": minimum,
        "maximum_revenue": maximum,
        "product_revenue": product_revenue,
        "store_revenue": store_revenue,
        "payment_method_revenue": payment_method_revenue,
        "top_products": top_n(product_revenue, 3),
        "high_sales": high_sales,
        "high_sales_by_store": high_sales_by_store,
    }


def _breakdown_lines(title: str, totals: dict[str, float], width: int) -> list[str]:
    """Format one 'revenue by ...' table, highest first, ties alphabetical."""
    lines = [title]
    for name, amount in sorted(totals.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"  {name:<{width}}  {amount:>14,.2f}")
    return lines


def build_report(results: dict, verification_lines: list[str]) -> str:
    """Format the results as the report text (no printing, no file access)."""
    r = results
    width = max(len(name) for name in r["product_revenue"])

    skipped_details = ", ".join(
        f"{row['sale_id']}: {row['reason']}" for row in r["skipped_rows"]
    )

    lines = [
        "=== Sales report: September 2026 ===",
        f"Columns found      : {', '.join(r['columns'])}",
        f"Rows read          : {r['rows_read']}",
        f"Rows used          : {r['valid_count']}",
        f"Rows skipped       : {r['skipped_count']}"
        + (f"   ({skipped_details})" if skipped_details else ""),
        "",
        f"Total revenue (KES): {r['total_revenue']:,.2f}",
        "",
    ]
    lines += _breakdown_lines("Revenue by product (KES)", r["product_revenue"], width)
    lines.append("")
    lines += _breakdown_lines("Revenue by store (KES)", r["store_revenue"], width)
    lines.append("")
    lines += _breakdown_lines("Revenue by payment method (KES)", r["payment_method_revenue"], width)

    lines += ["", "Top 3 products"]
    for rank, (product, amount) in enumerate(r["top_products"], start=1):
        lines.append(f"  {rank}. {product} - KES {amount:,.2f}")

    lines += [
        "",
        f"High-value transactions (>= KES {r['threshold']:,.0f}): {len(r['high_sales'])}",
    ]
    for sale in r["high_sales"]:
        lines.append(
            f"  {sale['sale_id']}  {sale['sale_date']}  {sale['store']}  "
            f"{sale['product']}  KES {sale['revenue']:,.2f}"
        )

    lines += ["", "High-value sales per store"]
    for store, count in r["high_sales_by_store"].items():
        lines.append(f"  {store:<{width}}  {count:>3}")

    lines += [
        "",
        "Transaction revenue statistics",
        f"  mean   : {r['mean_revenue']:,.2f}",
        f"  median : {r['median_revenue']:,.2f}",
        f"  min    : {r['minimum_revenue']:,.2f}",
        f"  max    : {r['maximum_revenue']:,.2f}",
        "",
        "=== pandas verification ===",
    ]
    lines += verification_lines

    return "\n".join(lines) + "\n"


def write_report(report_path: Path, report: str) -> None:
    """Save the report text to a file, creating the folder if needed."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    results = analyse()
    verification_lines = verify_with_pandas(DATA_PATH, results)
    report = build_report(results, verification_lines)

    write_report(OUTPUT_PATH, report)
    print(report)
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
