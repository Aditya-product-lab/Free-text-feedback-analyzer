import io
import os
from collections import Counter
from pathlib import Path

import openpyxl
import streamlit as st
from dotenv import load_dotenv

from analyzer import analyze_feedback, build_summary
from utils import (
    PRIMARY_TAGS,
    SECONDARY_TAGS,
    append_analysis_to_workbook,
    dataframe_preview,
    detect_feedback_column,
    load_workbook_as_dataframe,
)

# -------------------------------------------------------------------
# Load environment configuration
# -------------------------------------------------------------------

load_dotenv()

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

BATCH_SIZE = int(
    os.getenv(
        "BATCH_SIZE",
        "25",
    )
)

MAX_ROWS = int(
    os.getenv(
        "MAX_ROWS",
        "1000",
    )
)


# -------------------------------------------------------------------
# Streamlit page configuration
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Feedback Analyzer",
    page_icon="💬",
    layout="wide",
)


# -------------------------------------------------------------------
# App header
# -------------------------------------------------------------------

st.title("💬 Feedback Analyzer")

st.caption(
    "Upload your feedback file, confirm the feedback column, "
    "and let the tool analyze it."
)


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "summary" not in st.session_state:
    st.session_state.summary = ""


# -------------------------------------------------------------------
# File upload
# -------------------------------------------------------------------

uploaded = st.file_uploader(
    "Upload an Excel file",
    type=["xlsx", "xlsm"],
    help=(
        "The first row is treated as the header row. "
        "This tool supports .xlsx and .xlsm files."
    ),
)


if uploaded is None:
    st.info(
        "Start by uploading an Excel file."
    )
    st.stop()


# -------------------------------------------------------------------
# Read uploaded workbook
# -------------------------------------------------------------------

file_bytes = uploaded.getvalue()

try:
    workbook = openpyxl.load_workbook(
        io.BytesIO(file_bytes),
        read_only=False,
        data_only=False,
    )

    sheet_names = workbook.sheetnames

except Exception as exc:
    st.error(
        f"Could not open the workbook: {exc}"
    )
    st.stop()


# -------------------------------------------------------------------
# Worksheet selection
# -------------------------------------------------------------------

selected_sheet = st.selectbox(
    "Worksheet",
    sheet_names,
)


# -------------------------------------------------------------------
# Load worksheet into dataframe
# -------------------------------------------------------------------

df, headers = load_workbook_as_dataframe(
    file_bytes,
    selected_sheet,
)


if df.empty or not headers:
    st.error(
        "No tabular data was found on the selected worksheet."
    )
    st.stop()


# -------------------------------------------------------------------
# Detect likely feedback column
# -------------------------------------------------------------------

detected_column, _ = detect_feedback_column(
    headers
)

options = list(headers)

default_index = (
    options.index(detected_column)
    if detected_column in options
    else 0
)


# -------------------------------------------------------------------
# Confirm feedback column
# -------------------------------------------------------------------

st.subheader(
    "1. Confirm the feedback column"
)

feedback_column = st.selectbox(
    "Column to analyze",
    options,
    index=default_index,
    help=(
        "The tool has suggested a column based on its header. "
        "Change it if the suggestion is incorrect."
    ),
)

st.caption(
    f"Suggested column: **{detected_column}**"
)


# -------------------------------------------------------------------
# Source data preview
# -------------------------------------------------------------------

st.subheader(
    "2. Preview of source data"
)

st.dataframe(
    dataframe_preview(df),
    use_container_width=True,
    height=300,
)


# -------------------------------------------------------------------
# Count usable feedback rows
# -------------------------------------------------------------------

feedback_series = (
    df[feedback_column]
    .fillna("")
    .astype(str)
)

non_empty = (
    feedback_series
    .str
    .strip()
    .ne("")
)

feedback_count = int(
    non_empty.sum()
)

st.write(
    f"Rows with feedback: **{feedback_count:,}**"
)


# -------------------------------------------------------------------
# Maximum row validation
# -------------------------------------------------------------------

if feedback_count > MAX_ROWS:

    st.warning(
        f"This file contains **{feedback_count:,} feedback responses**, "
        f"which is more than the maximum of **{MAX_ROWS:,}** allowed for one analysis."
    )

    st.info(
        "Please reduce the number of feedback rows in the file "
        "before starting the analysis."
    )

    st.stop()


# -------------------------------------------------------------------
# Analyze button
# -------------------------------------------------------------------

analyze_clicked = st.button(
    "Analyze feedback",
    type="primary",
    use_container_width=True,
)


if analyze_clicked:

    # ---------------------------------------------------------------
    # Validate API key
    # ---------------------------------------------------------------

    if not os.getenv("GEMINI_API_KEY"):

        st.error(
            "Gemini API key is not configured. "
            "Please add GEMINI_API_KEY to your .env file "
            "and restart the application."
        )

        st.stop()


    # ---------------------------------------------------------------
    # Validate feedback
    # ---------------------------------------------------------------

    if feedback_count == 0:

        st.error(
            "The selected column does not contain any "
            "non-empty feedback."
        )

        st.stop()


    # ---------------------------------------------------------------
    # Prepare feedback rows
    # ---------------------------------------------------------------

    feedback_rows = [
        {
            "row_index": int(i),
            "text": feedback_series.iloc[i],
        }
        for i in range(len(feedback_series))
        if feedback_series.iloc[i].strip()
    ]


    # ---------------------------------------------------------------
    # Final safety check
    # ---------------------------------------------------------------

    if len(feedback_rows) > MAX_ROWS:

        st.error(
            f"Analysis stopped because {len(feedback_rows):,} "
            f"feedback responses exceed the configured maximum."
        )

        st.stop()


    # ---------------------------------------------------------------
    # Progress indicator
    # ---------------------------------------------------------------

    progress = st.progress(0)

    status = st.empty()


    # ---------------------------------------------------------------
    # Analyze feedback using Gemini
    # ---------------------------------------------------------------

    try:

        def update_progress(
            completed,
            total,
        ):
            progress.progress(
                min(
                    completed / max(total, 1),
                    1.0,
                )
            )

            status.write(
                f"Analyzed {completed:,} "
                f"of {total:,} responses…"
            )


        result_rows = analyze_feedback(
            feedback_rows,
            model=MODEL,
            batch_size=BATCH_SIZE,
            progress_callback=update_progress,
        )


        progress.progress(1.0)

        status.write(
            "Analysis complete."
        )


        # -----------------------------------------------------------
        # Create enriched dataframe
        # -----------------------------------------------------------

        enriched_df = df.copy()

        enriched_df["Primary tag"] = ""
        enriched_df["Secondary tag"] = ""


        for item in result_rows:

            idx = item["row_index"]

            enriched_df.at[
                idx,
                "Primary tag",
            ] = item["primary_tag"]

            enriched_df.at[
                idx,
                "Secondary tag",
            ] = item["secondary_tag"]


        # -----------------------------------------------------------
        # Store analysis results
        # -----------------------------------------------------------

        st.session_state.analysis_result = {
            "df": enriched_df,
            "sheet_name": selected_sheet,
            "feedback_column": feedback_column,
            "original_bytes": file_bytes,
            "source_filename": uploaded.name,
        }


        # -----------------------------------------------------------
        # Generate summary
        # -----------------------------------------------------------

        st.session_state.summary = build_summary(
            feedback_rows=feedback_rows,
            result_rows=result_rows,
            model=MODEL,
        )


    except Exception as exc:

        st.error(
            f"Analysis failed: {exc}"
        )

        st.stop()


# -------------------------------------------------------------------
# Display analysis results
# -------------------------------------------------------------------

result = st.session_state.analysis_result


if result:

    st.subheader(
        "3. Results"
    )

    result_df = result["df"]


    # ---------------------------------------------------------------
    # Results table
    # ---------------------------------------------------------------

    st.dataframe(
        result_df,
        use_container_width=True,
        height=420,
    )


    # ---------------------------------------------------------------
    # Tag distributions
    # ---------------------------------------------------------------

    counts_primary = Counter(
        result_df["Primary tag"]
    )

    counts_secondary = Counter(
        result_df["Secondary tag"]
    )


    c1, c2 = st.columns(2)


    with c1:

        st.markdown(
            "**Primary tag distribution**"
        )

        st.write(
            " · ".join(
                f"{tag}: "
                f"{counts_primary.get(tag, 0)}"
                for tag in PRIMARY_TAGS
            )
        )


    with c2:

        st.markdown(
            "**Secondary tag distribution**"
        )

        st.write(
            " · ".join(
                f"{tag}: "
                f"{counts_secondary.get(tag, 0)}"
                for tag in SECONDARY_TAGS
            )
        )


    # ---------------------------------------------------------------
    # Feedback summary
    # ---------------------------------------------------------------

    st.subheader(
        "4. Feedback summary"
    )

    st.text_area(
        "Generated summary",
        value=st.session_state.summary,
        height=280,
        label_visibility="collapsed",
    )


    # ---------------------------------------------------------------
    # Copy summary to clipboard
    # ---------------------------------------------------------------

    import streamlit.components.v1 as components


    safe_summary = (
        st.session_state.summary
        .replace(
            "\\",
            "\\\\",
        )
        .replace(
            "`",
            "\\`",
        )
        .replace(
            "${",
            "\\${",
        )
    )


    components.html(
        f"""
        <div
            style="
                font-family: sans-serif;
                margin-top: 4px;
            "
        >

            <button
                id="copyBtn"
                style="
                    padding: 8px 14px;
                    border-radius: 6px;
                    border: 1px solid #bbb;
                    background: #fff;
                    cursor: pointer;
                "
            >
                Copy summary to clipboard
            </button>

            <span
                id="copyStatus"
                style="
                    margin-left: 8px;
                    color: #666;
                "
            ></span>

        </div>

        <script>

            const text = `{safe_summary}`;

            const btn =
                document.getElementById("copyBtn");

            const status =
                document.getElementById("copyStatus");

            btn.onclick = async () => {{

                try {{

                    await navigator.clipboard.writeText(
                        text
                    );

                    status.textContent = "Copied!";

                }} catch (e) {{

                    const area =
                        document.createElement("textarea");

                    area.value = text;

                    document.body.appendChild(area);

                    area.select();

                    document.execCommand("copy");

                    area.remove();

                    status.textContent = "Copied!";

                }}

            }};

        </script>
        """,
        height=45,
    )


    # ---------------------------------------------------------------
    # Create downloadable workbook
    # ---------------------------------------------------------------

    output = append_analysis_to_workbook(
        original_bytes=result["original_bytes"],
        sheet_name=result["sheet_name"],
        result_df=result_df,
    )


    base = Path(
        result["source_filename"]
    ).stem


    output_name = (
        f"{base}_analyzed.xlsx"
    )


    # ---------------------------------------------------------------
    # Download button
    # ---------------------------------------------------------------

    st.download_button(
        "Download analyzed Excel",
        data=output,
        file_name=output_name,
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
        use_container_width=True,
    )
