import streamlit as st
import requests

# ── Config ────────────────────────────────────────────
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI SQL Assistant",
    page_icon="🤖",
    layout="wide"
)

# ── Title ─────────────────────────────────────────────
st.title("🤖 AI SQL Assistant")
st.markdown("Upload a CSV dataset, select a table, then ask questions in plain English.")
st.divider()


# ── Helper: fetch tables ──────────────────────────────
def fetch_tables():
    try:
        res = requests.get(f"{BACKEND_URL}/tables", timeout=5)
        return res.json().get("tables", [])
    except Exception:
        return []


# ════════════════════════════════════════════════════
# SECTION 1 — Upload CSV
# ════════════════════════════════════════════════════
st.header("📂 Step 1 — Upload CSV Dataset")

col1, col2 = st.columns([3, 2])
with col1:
    csv_file = st.file_uploader("Choose a CSV file", type="csv")
with col2:
    table_name_input = st.text_input(
        "Unique Table Name",
        placeholder="e.g. sales_2024",
        help="Only letters, numbers, underscores. Must be unique."
    )

if st.button("⬆️ Upload CSV", use_container_width=True):
    if not csv_file:
        st.warning("⚠️ Please select a CSV file.")
    elif not table_name_input:
        st.warning("⚠️ Please enter a table name.")
    else:
        with st.spinner("Uploading..."):
            try:
                files = {"file": (csv_file.name, csv_file, "text/csv")}
                data  = {"table_name": table_name_input}
                res   = requests.post(f"{BACKEND_URL}/upload", files=files, data=data, timeout=30)
                body  = res.json()
                if res.status_code == 200:
                    st.success(f"✅ {body['message']}")
                    st.rerun()
                else:
                    st.error(f"❌ {body.get('error', 'Upload failed.')}")
            except Exception as e:
                st.error(f"❌ Could not connect to backend: {e}")

st.divider()


# ════════════════════════════════════════════════════
# SECTION 2 — Manage Tables
# ════════════════════════════════════════════════════
st.header("🗂️ Step 2 — Manage Uploaded Tables")

tables = fetch_tables()

if not tables:
    st.info("No tables uploaded yet. Upload a CSV above to get started.")
else:
    st.caption(f"{len(tables)} table(s) available:")
    for t in tables:
        col_a, col_b, col_c = st.columns([4, 1, 1])
        with col_a:
            st.markdown(f"📋 `{t}`")
        with col_b:
            # Preview schema
            if st.button("🔍 Schema", key=f"schema_{t}"):
                try:
                    res = requests.get(f"{BACKEND_URL}/schema/{t}", timeout=5)
                    st.code(res.json().get("schema", ""), language="sql")
                except Exception as e:
                    st.error(str(e))
        with col_c:
            if st.button("🗑️ Delete", key=f"delete_{t}"):
                try:
                    res = requests.delete(f"{BACKEND_URL}/table/{t}", timeout=5)
                    body = res.json()
                    if res.status_code == 200:
                        st.success(f"✅ Table `{t}` deleted.")
                        st.rerun()
                    else:
                        st.error(f"❌ {body.get('error')}")
                except Exception as e:
                    st.error(str(e))

st.divider()



# ════════════════════════════════════════════════════
# SECTION 3 — Generate Dataset Insights
# ════════════════════════════════════════════════════
st.header("📈 Step 3 — Generate Dataset Insights")

if not tables:
    st.warning("⚠️ Upload a CSV first to generate insights.")
else:
    insight_table = st.selectbox(
        "Select a table to profile",
        options=tables,
        key="insight_table",
        help="Choose the dataset you want to analyze."
    )

    if st.button("✨ Generate Insights Report", use_container_width=True):
        with st.spinner("Analyzing dataset... This may take 15-30 seconds ⏳"):
            try:
                res = requests.get(
                    f"{BACKEND_URL}/profile/{insight_table}",
                    timeout=120
                )
                if res.status_code == 200:
                    html_bytes = res.content
                    st.success("✅ Report generated! Click below to download.")
                    st.download_button(
                        label="📥 Download Full Insights Report (HTML)",
                        data=html_bytes,
                        file_name=f"{insight_table}_insights_report.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    st.info("💡 Open the downloaded HTML file in your browser to explore the full interactive report.")
                else:
                    error = res.json().get("error", "Unknown error")
                    st.error(f"❌ {error}")
            except requests.exceptions.Timeout:
                st.error("❌ Report generation timed out. Try with a smaller dataset.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    with st.expander("ℹ️ What's included in the report?"):
        st.markdown("""
        The HTML report includes:
        - **📊 Overview** — row count, column count, missing values, duplicates
        - **📋 Column Statistics** — min, max, mean, median, std deviation for each column
        - **📉 Distributions** — histogram and value counts per column
        - **🔗 Correlations** — Pearson & Spearman correlation heatmaps
        - **❓ Missing Values** — bar chart and matrix of missing data
        - **👥 Duplicate Rows** — list of duplicate entries if any
        """)

st.divider()


# ════════════════════════════════════════════════════
# SECTION 4 — Ask a Question
# ════════════════════════════════════════════════════
st.header("💬 Step 4 — Ask a Question")

if not tables:
    st.warning("⚠️ Upload a CSV first before asking questions.")
else:
    selected_table = st.selectbox(
        "Select a table to query",
        options=tables,
        help="Choose the dataset you want to ask about."
    )

    question = st.text_input(
        "Your question in plain English",
        placeholder="e.g. What is the total amount spent?"
    )

    if st.button("🔍 Ask", use_container_width=True):
        if not question:
            st.warning("⚠️ Please enter a question.")
        else:
            with st.spinner("Generating SQL and fetching answer..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/ask",
                        json={"question": question, "table_name": selected_table},
                        timeout=60
                    )
                    data = res.json()

                    if data.get("error"):
                        st.error(f"❌ Error: {data['error']}")
                    else:
                        # ── 1. Generated SQL ──────────────────────
                        st.subheader("🧠 Generated SQL Query")
                        sql = data.get("sql_query", "")
                        if sql:
                            st.code(sql, language="sql")
                        else:
                            st.warning("No SQL query returned.")

                        st.divider()

                        # ── 2. Raw Results ────────────────────────
                        st.subheader("📊 Query Results")
                        raw = data.get("raw_result", [])
                        if raw:
                            # Build pure HTML table — zero pyarrow dependency
                            headers = list(raw[0].keys())
                            header_html = "".join(f"<th style='padding:8px 12px; background:#1e3a5f; color:white; text-align:left;'>{h}</th>" for h in headers)
                            rows_html = ""
                            for i, row in enumerate(raw):
                                bg = "#f0f4f8" if i % 2 == 0 else "#ffffff"
                                cells = "".join(f"<td style='padding:8px 14px; border-bottom:1px solid #ddd; color:#111111; font-size:14px;'>{row.get(h, '')}</td>" for h in headers)
                                rows_html += f"<tr style='background:{bg};'>{cells}</tr>"

                            table_html = f"""
                            <div style='overflow-x:auto; border-radius:8px; border:1px solid #ddd; margin-top:8px;'>
                            <table style='width:100%; border-collapse:collapse; font-size:14px; font-family:sans-serif; background:#ffffff;'>
                                <thead><tr>{header_html}</tr></thead>
                                <tbody>{rows_html}</tbody>
                            </table>
                            </div>
                            """
                            st.markdown(table_html, unsafe_allow_html=True)
                            st.caption(f"🔢 {len(raw)} row(s) returned")
                        else:
                            st.info("No rows returned for this query.")

                        st.divider()

                        # ── 3. Natural Language Answer ─────────────
                        st.subheader("💡 Answer")
                        answer = data.get("answer", "")
                        if answer:
                            st.success(answer)
                        else:
                            st.warning("No answer returned.")

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The backend may be slow — try again.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")