from rescue_rag.sec.xbrl import filing_fiscal_year, match_fact

ACCN = "0000320193-25-000079"


def _row(val, end, start=None, accn=ACCN, form="10-K", fy=2025):
    r = {"val": val, "end": end, "accn": accn, "form": form, "fy": fy, "fp": "FY"}
    if start:
        r["start"] = start
    return r


FACTS = {
    "facts": {
        "us-gaap": {
            "Revenues": {"units": {"USD": [_row(1, "2025-09-27", "2025-06-29")]}},  # quarter
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {
                    "USD": [
                        _row(416, "2025-09-27", "2024-09-29"),  # current year
                        _row(391, "2024-09-28", "2023-10-01"),  # prior year, same filing
                        _row(999, "2025-09-27", "2024-09-29", form="10-Q"),
                    ]
                }
            },
            "Assets": {"units": {"USD": [_row(359, "2025-09-27"), _row(365, "2024-09-28")]}},
        }
    }
}

REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"]


def test_flow_item_needs_annual_duration_and_falls_back():
    f = match_fact(FACTS, REV, ACCN, "2025-09-27", flow=True)
    assert f is not None
    assert f.value == 416
    assert f.concept == "RevenueFromContractWithCustomerExcludingAssessedTax"


def test_period_end_selects_the_filings_own_year():
    f = match_fact(FACTS, REV, ACCN, "2024-09-28", flow=True)
    assert f is not None and f.value == 391


def test_balance_item_is_point_in_time():
    f = match_fact(FACTS, ["Assets"], ACCN, "2025-09-27", flow=False)
    assert f is not None and f.value == 359


def test_other_filing_or_missing_concept_returns_none():
    assert match_fact(FACTS, REV, "other-accn", "2025-09-27", flow=True) is None
    assert match_fact(FACTS, ["NetIncomeLoss"], ACCN, "2025-09-27", flow=True) is None


def test_filing_fiscal_year():
    assert filing_fiscal_year(FACTS, ACCN) == 2025
    assert filing_fiscal_year(FACTS, "other-accn") is None
