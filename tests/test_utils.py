import io

import openpyxl
import pandas as pd

from utils import (
    append_analysis_to_workbook,
    dataframe_preview,
    detect_feedback_column,
    load_workbook_as_dataframe,
)


def make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Feedback"
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_feedback_column_detection():
    col, confidence = detect_feedback_column(["ID", "Status", "Customer Feedback"])
    assert col == "Customer Feedback"
    assert confidence > 0.9

    col_empty, conf_empty = detect_feedback_column([])
    assert col_empty == ""
    assert conf_empty == 0.0


def test_load_workbook_clean_headers_and_trailing_empty_rows():
    # Includes empty header (Column 2) and duplicate header (Status, Status (2))
    # and trailing completely empty rows
    data = [
        ["ID", None, "Status", "Status", "Customer Feedback"],
        [1, "Val1", "Active", "Open", "Great tool!"],
        [2, "Val2", "Closed", "Done", "Needs improvements"],
        [None, None, None, None, None],
        ["", "   ", None, None, ""],
    ]
    raw = make_xlsx(data)
    df, headers = load_workbook_as_dataframe(raw, "Feedback")

    assert headers == ["ID", "Column 2", "Status", "Status (2)", "Customer Feedback"]
    # Only 2 rows with data should be kept; trailing empty rows trimmed
    assert len(df) == 2
    assert df.iloc[0]["Customer Feedback"] == "Great tool!"


def test_load_workbook_empty_sheet():
    raw = make_xlsx([])
    df, headers = load_workbook_as_dataframe(raw, "Feedback")
    assert df.empty
    assert headers == []


def test_dataframe_preview():
    df = pd.DataFrame({"col": range(100)})
    preview = dataframe_preview(df)
    assert len(preview) == 50


def test_append_analysis():
    original = make_xlsx([
        ["ID", "Name", "Customer Feedback"],
        [1, "A", "The button does not work"],
        [2, "B", "Please add SSO"],
        [3, "C", "I love this app!"],
    ])
    df, headers = load_workbook_as_dataframe(original, "Feedback")
    df["Primary tag"] = ["Bug", "Feature request", "Compliment"]
    df["Secondary tag"] = ["UI/UX", "integrations", "other"]

    output = append_analysis_to_workbook(original, "Feedback", df)
    wb = openpyxl.load_workbook(io.BytesIO(output))
    ws = wb["Feedback"]

    assert ws["D1"].value == "Primary tag"
    assert ws["E1"].value == "Secondary tag"
    assert ws["D2"].value == "Bug"
    assert ws["D4"].value == "Compliment"
    assert ws["E4"].value == "other"
