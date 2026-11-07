import io
import re
from typing import Iterable

import openpyxl
import pandas as pd
from openpyxl.styles import Font


PRIMARY_TAGS = {
    "Bug": "broken/not working",
    "Feature request": "entirely new feature",
    "Enhancements": "improvement to an existing feature",
    "Education": "confused/unclear about a feature",
    "Compliment": "positive feedback or appreciation",
    "others": "does not fit the above categories",
}

SECONDARY_TAGS = [
    "UI/UX",
    "Backend/logic",
    "Performance",
    "integrations",
    "billing pricing",
    "data",
    "onboarding (signup)",
    "other",
]


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def detect_feedback_column(headers: Iterable[object]) -> tuple[str, float]:
    """
    Header-only heuristic so the user can see and override the initial guess.
    """
    keywords = {
        "feedback": 1.0,
        "comment": 0.92,
        "comments": 0.92,
        "review": 0.88,
        "suggestion": 0.88,
        "suggestions": 0.88,
        "issue": 0.84,
        "description": 0.70,
        "response": 0.70,
        "user response": 0.95,
        "customer feedback": 1.0,
        "customer comment": 0.95,
        "free text": 0.86,
        "verbatim": 0.82,
    }

    best_header = str(next(iter(headers), ""))
    best_score = 0.0

    for header in headers:
        normalized = _norm(header)
        score = 0.0

        if normalized in keywords:
            score = keywords[normalized]
        else:
            for token, weight in keywords.items():
                nt = _norm(token)
                if nt and (nt in normalized or normalized in nt):
                    score = max(score, weight * 0.8)

        if score > best_score:
            best_header = str(header)
            best_score = score

    return best_header, best_score


def load_workbook_as_dataframe(
    file_bytes: bytes, sheet_name: str
) -> tuple[pd.DataFrame, list[str]]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=False)
    ws = wb[sheet_name]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return pd.DataFrame(), []

    headers = [str(value).strip() if value is not None else "" for value in rows[0]]
    # Make blank/duplicate headers usable in pandas and keep output mapping deterministic.
    seen: dict[str, int] = {}
    clean_headers: list[str] = []
    for idx, header in enumerate(headers):
        name = header or f"Column {idx + 1}"
        count = seen.get(name, 0)
        seen[name] = count + 1
        clean_headers.append(name if count == 0 else f"{name} ({count + 1})")

    data_rows = rows[1:]
    df = pd.DataFrame(data_rows, columns=clean_headers)

    # Trim trailing rows where all cells are empty/blank or null
    if not df.empty:
        has_data = df.apply(
            lambda r: any(pd.notna(v) and str(v).strip() != "" for v in r),
            axis=1,
        )
        if has_data.any():
            last_valid_idx = has_data[::-1].idxmax()
            df = df.iloc[: last_valid_idx + 1].copy()
        else:
            df = df.iloc[0:0].copy()

    return df, clean_headers


def dataframe_preview(df: pd.DataFrame) -> pd.DataFrame:
    return df.head(50).copy()


def _last_non_empty_col(ws) -> int:
    last = 0
    for row in ws.iter_rows():
        for cell in row:
            if cell.value not in (None, ""):
                last = max(last, cell.column)
    return last


def append_analysis_to_workbook(
    original_bytes: bytes,
    sheet_name: str,
    result_df: pd.DataFrame,
) -> bytes:
    """
    Preserve the source workbook and append two columns after the last non-empty
    column on the selected sheet. Existing rows/sheet formatting stay intact.
    """
    in_memory = io.BytesIO(original_bytes)
    wb = openpyxl.load_workbook(in_memory, read_only=False, data_only=False)
    ws = wb[sheet_name]

    last_col = _last_non_empty_col(ws)
    primary_col = last_col + 1
    secondary_col = last_col + 2

    ws.cell(row=1, column=primary_col, value="Primary tag")
    ws.cell(row=1, column=secondary_col, value="Secondary tag")
    ws.cell(row=1, column=primary_col).font = Font(bold=True)
    ws.cell(row=1, column=secondary_col).font = Font(bold=True)

    for df_index, row in result_df.iterrows():
        excel_row = int(df_index) + 2
        ws.cell(row=excel_row, column=primary_col, value=row["Primary tag"] or None)
        ws.cell(row=excel_row, column=secondary_col, value=row["Secondary tag"] or None)

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
