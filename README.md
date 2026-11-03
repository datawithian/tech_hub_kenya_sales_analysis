# Electronics Sales Analytics (Without Pandas)

## Project Overview

This project analyzes an electronics sales CSV using Python's standard
library. It reads and cleans transaction data, calculates revenue
metrics, identifies high-value transactions, summarizes product
performance, and writes a formatted report to a text file.

Pandas is used only in the final verification step to independently
check selected results from the standard-library implementation.

## Project Structure

``` text
day2-sales-analytics/
├── sales_analysis.py
├── data/
│   └── electronics_sales.csv
├── output/
│   └── sales_report.txt
├── requirements.txt
└── README.md
```

-   `sales_analysis.py` --- data-reading, cleaning, analysis, reporting,
    and verification functions.
-   `data/electronics_sales.csv` --- source sales data.
-   `output/sales_report.txt` --- generated analysis report.
-   `requirements.txt` --- dependency used for verification.
-   `README.md` --- project documentation.

## Objectives

-   Read CSV data with Python's built-in `csv` module.
-   Convert messy numeric values into usable numbers.
-   Separate valid transactions from invalid rows.
-   Calculate total revenue and revenue by product.
-   Rank the top three products by revenue.
-   Identify high-value transactions.
-   Calculate mean, median, minimum, and maximum transaction revenue.
-   Save results in a readable text report.
-   Verify selected calculations with pandas.

## Approach

| Task | Function | Notes |
|---|---|---|
| 1 | `read_sales` | `csv.DictReader`, `newline=""`, UTF-8 (BOM-safe). Prints the row count and column names to the terminal, as the brief asks; the saved report repeats them in its header. A missing CSV raises a clear `FileNotFoundError`. |
| 2 | `parse_number`, `convert_rows` | Repair simple formatting (spaces, `KES` prefix, commas); skip values that are missing or not numbers. |
| 3 | `total_revenue` | Revenue per row = quantity x unit price; summed with a loop. |
| 4 | `revenue_by` | Plain `dict` with an `in` check (no `defaultdict`/`Counter`). Used for product, store, payment method. |
| 5 | `top_n` | `sorted(..., key=...)` returning `(product, revenue)` tuples. |
| 6 | `high_value` + dict comprehension | List comprehension for `>= 50,000`; per-store counts via dict comprehension (stores with 0 are shown). |
| 7 | `mean`, `median`, `minimum_maximum` | Hand-written; `minimum_maximum` uses a loop, not `min()`/`max()`. Each raises `ValueError("<name>() needs at least one value; got an empty list")` on an empty list. |
| 8 | `verify_with_pandas` | Re-cleans the CSV in pandas with the same rules and prints MATCH/MISMATCH per headline number. |

## Cleaning rules and justification

The file has 6 irregular values in 50 rows. `parse_number` applies these rules in order:

1. Strip leading/trailing whitespace. An empty string is not usable (`None`).
2. Remove **every comma**.
3. If the text starts with `KES` (any case), drop that prefix and any space after it.
4. Convert with `float()`. If that fails, the value is not usable (`None`).
5. Reject `nan` and `inf` (`math.isfinite`), so a bad value can never turn a total into `nan`.

`convert_rows` then requires a **positive whole-number quantity** and a **positive unit price**.
Each skipped row keeps its `sale_id` and a reason that includes the offending value.

**Repaired (formatting only, meaning is unambiguous in this file):**
- `38,999` (S-3017) becomes 38999. The comma is a thousands separator.
- `KES 18999` (S-3029) becomes 18999. The column is already in KES, so the prefix adds no information.

**Skipped (no number to recover), with a reason recorded for each:**
- S-3006 quantity `two` - a word, not a number. I deliberately do not interpret words: a word-to-number table does not scale and would silently mishandle other text.
- S-3030 unit price `N/A` - no price given.
- S-3035 quantity empty - not recorded.
- S-3039 unit price empty - not recorded.

**Why every comma is removed.** This is a one-time analysis of one known export, and the only comma in the file is a thousands separator. I assume the till never uses a decimal comma, so a comma is always either a thousands separator or a typo. The risk is that a value such as `3,19` would be read as 319 instead of being flagged. That does not occur in this file, but it is the main weakness of the rule, and a stricter parser (for example, accepting commas only in groups of three) would be needed if the code were reused on other exports.

**Known limitations of the rules:** `float()` also accepts forms such as `1e3` and `1_000`, which are not specially handled. Only the `KES` prefix is recognised, not `Ksh`.

For each valid transaction:

`revenue = quantity × unit_price_kes`

Other fields, including sale ID, date, store, product, and payment
method, are retained for grouping and reporting.

## Tie-breaking

`top_n` sorts by revenue descending, then product name ascending, so equal revenues always give the same order. There are no ties in the September top 3.

## Analysis Included

### Revenue

-   Total revenue across valid transactions.
-   Revenue by product, sorted from highest to lowest.
-   Revenue by store and by payment method.
-   Top three products by revenue.

### High-value transactions

Transactions with revenue greater than or equal to **KES 50,000** are
included in the high-value section. The threshold can be changed in the
script. The number of high-value sales per store is also reported (stores
with none show 0).

### Transaction revenue statistics

-   **Mean:** average revenue per valid transaction.
-   **Median:** middle transaction revenue after sorting.
-   **Minimum:** smallest valid transaction revenue.
-   **Maximum:** largest valid transaction revenue.

These statistics are calculated from transaction revenue, not individual
unit prices.

## Tools and Python Concepts

-   Python standard library, including `csv` and `pathlib`.
-   Lists and dictionaries for storing and processing records.
-   Functions to separate tasks and make code reusable.
-   Loops and conditionals for validation and aggregation.
-   Sorting and key functions for ranking results.
-   File handling to write `output/sales_report.txt`.
-   Pandas for final verification only.

## Requirements

-   Python 3.10 or later is recommended because the code uses modern
    type-hint syntax.
-   `pandas` is required only for the verification step. If it is not
    installed, the report still runs and the verification section reads
    `pandas is not installed - verification skipped`.

Install dependencies from the project root:

``` bash
python -m pip install -r requirements.txt
```

Tasks 1--7 are designed to use the Python standard library only.

## How to Run

1.  Open a terminal in the project root---the directory containing
    `sales_analysis.py`.

2.  Install the verification dependency:

    ``` bash
    python -m pip install -r requirements.txt
    ```

3.  Run the analysis:

    ``` bash
    python sales_analysis.py
    ```

4.  Review the report printed in the terminal. The first two lines
    ("Rows read" and "Columns") are printed by `read_sales` (task 1); the
    report header repeats the same information, so it is also saved in
    the file.

5.  Open `output/sales_report.txt` to review the saved report.

The script should create the `output` directory if it does not already
exist.

If the CSV is missing, the script stops with a clear message
(`Error: Sales file not found: data/electronics_sales.csv`) instead of a
traceback. Check that the file is in `data/` and that you are running from
the project root.

## Report Contents

The generated report is intended to include:

-   Reporting period heading and the column names found.
-   Number of rows read, used, and skipped.
-   Skipped sale IDs and reasons, where applicable.
-   Total revenue.
-   Revenue by product, by store, and by payment method.
-   Top three products.
-   High-value transactions and the count per store.
-   Mean, median, minimum, and maximum transaction revenue.
-   Results of the pandas verification checks.

Report values are calculated at runtime from the CSV and should not be
entered manually.

## Verification

The verification function re-reads the CSV as text with pandas, applies the
same cleaning rules (including removing every comma and rejecting `nan`
and `inf`), and compares eight results with the standard-library ones:

-   Total revenue.
-   Revenue by product.
-   Top three products.
-   Mean and median transaction revenue.
-   Minimum and maximum transaction revenue.
-   Rows used and skipped.
-   Revenue by store.
-   Revenue by payment method.

The first four follow the layout of `expected_report.txt`; the other four
are extra checks. Floats are compared with `math.isclose`, not `==`, to
avoid false mismatches from rounding. The report and the verification both
receive the same `analyse()` results dict, so they always use identical
numbers.

If a check reports `MISMATCH`, investigate differences in parsing,
validation, grouping, sorting, or calculations. The pandas parser is a
separate re-implementation of `parse_number`, so the two must be kept in
sync if either changes. The top-three check reuses the same tie-break as
`top_n`, so ties are not independently verified (there are none in this
data).

## Assumptions and Limitations

-   Revenue is quantity multiplied by unit price. Tax, discounts,
    delivery fees, and refunds are not adjusted unless such rules are
    explicitly added.
-   Invalid or incomplete quantity and unit-price values are skipped
    rather than imputed.
-   Only positive whole-number quantities and positive unit prices are
    accepted.
-   The high-value threshold is inclusive: a transaction worth exactly
    KES 50,000 qualifies.
-   The report heading uses September 2026 to match the expected report
    template. Update it if the source data covers another period.
-   Results depend on the CSV contents and the rules implemented in the
    script.

## Learning Outcomes

This project practices reading CSV files, cleaning data, handling
invalid records, using lists and dictionaries, writing reusable
functions, calculating summary statistics, sorting results, and
generating reports without relying on pandas for the main analysis.

It also demonstrates how an independent implementation can help verify
analytical results.
