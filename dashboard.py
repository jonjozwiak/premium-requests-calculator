import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import tempfile
import matplotlib.pyplot as plt

# --- Helper functions ---

def load_csv(name):
    try:
        return pd.read_csv(name)
    except Exception:
        return pd.DataFrame()

def df_to_image(df, title=None):
    # Render DataFrame as an image using matplotlib for better alignment
    fig, ax = plt.subplots(figsize=(min(20, max(6, len(df.columns)*2)), min(1+len(df)*0.5, 20)))
    ax.axis('off')
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.2)
    if title:
        plt.title(title, fontsize=14, pad=20)
    # Save to a temporary file and open as PIL image
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        plt.savefig(tmp_img.name, bbox_inches='tight', dpi=200)
        plt.close(fig)
        img = Image.open(tmp_img.name).convert("RGB")
    os.remove(tmp_img.name)
    return img

def export_pdf(figs, tables, filename="dashboard_export.pdf", max_rows_per_page=25):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Add figures
    for fig in figs:
        img_bytes = fig.to_image(format="png")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            tmp_img.write(img_bytes)
            tmp_img.flush()
            img_path = tmp_img.name
        pdf.add_page()
        pdf.image(img_path, x=10, y=20, w=180)
        os.remove(img_path)
    # Add tables as images, paginated
    for title, df in tables:
        if not df.empty:
            num_pages = (len(df) - 1) // max_rows_per_page + 1
            for i in range(num_pages):
                chunk = df.iloc[i*max_rows_per_page:(i+1)*max_rows_per_page]
                page_title = f"{title} (Page {i+1})" if num_pages > 1 else title
                img = df_to_image(chunk, page_title)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    img.save(tmp_img, format="PNG")
                    tmp_img.flush()
                    img_path = tmp_img.name
                pdf.add_page()
                pdf.image(img_path, x=10, y=5, w=180)  # Changed y=20 to y=10
                os.remove(img_path)
    pdf.output(filename)
    return filename

# --- Load data ---
st.title("Premium Requests Dashboard")

# File paths
base = "."
csv_files = {
    "Requests per Model": os.path.join(base, "requests_per_model.csv"),
    "Requests per User per Model": os.path.join(base, "requests_per_user_per_model.csv"),
    "Total Requests per User": os.path.join(base, "requests_per_user.csv"),
    "Estimated Monthly Premium Requests per User": os.path.join(base, "estimated_requests_per_user.csv"),
}

# Load all CSVs
dfs = {k: load_csv(v) for k, v in csv_files.items()}

# Load original input for time series
input_csv = None

if len(sys.argv) < 2:
    print('Usage: streamlit run dashboard.py <input_csv_file>')
    sys.exit(1)
input_csv = sys.argv[1]

# Load the CSV file
df_raw = pd.read_csv(input_csv)

# Standardize column names to lowercase for easier access
df_raw.columns = [col.lower() for col in df_raw.columns]

# Ensure timestamp column is datetime
df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])

# Filter out rows where the last column is "Unlimited"
last_col = df_raw.columns[-1]
df_raw = df_raw[
    (df_raw[last_col] != "Unlimited") &
    (df_raw[last_col] != 2147483647) &
    (df_raw[last_col] != "2147483647")
]

# --- Visualizations ---

# 1. Line chart: total requests over time
st.header("Requests Over Time")
if not df_raw.empty and 'timestamp' in df_raw.columns:
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
    df_time = df_raw.groupby(df_raw['timestamp'].dt.date).size().reset_index(name='total_requests')
    fig_line = px.line(
        df_time,
        x='timestamp',
        y='total_requests',
        title="Requests Over Time",
        color_discrete_sequence=["#1f77b4"]  # Set a blue color for the line
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Raw data with 'timestamp' column not found.")

# 2. Pie chart: requests per model
st.header("Requests per Model")
df_model = dfs["Requests per Model"]
if not df_model.empty:
    fig_pie = px.pie(
        df_model,
        names='model',
        values='requests_used',
        title="Requests per Model",
        color_discrete_sequence=px.colors.qualitative.Set3  # Use a colorful palette
    )
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("Model summary data not found.")

# 3. Users near or above quota
st.header("Users Near or Above Quota")
percent_threshold = st.slider("Show users at or above this percent of quota", min_value=0, max_value=100, value=90, step=1)
df_user = dfs["Total Requests per User"]
if not df_user.empty and 'total_monthly_quota' in df_user.columns:
    df_user['percent_of_quota'] = df_user['requests_used'] / df_user['total_monthly_quota']
    near_quota = df_user[df_user['percent_of_quota'] >= percent_threshold / 100]
    st.dataframe(near_quota[['user', 'requests_used', 'total_monthly_quota', 'percent_of_quota']])
else:
    st.info("User quota data not found.")

# 4. Copilot Enterprise Upgrade Savings
st.header("Copilot Enterprise Upgrade Savings (>= 800 Requests)")
if not df_user.empty and 'total_monthly_quota' in df_user.columns:
    copilot_upgrade = df_user[(df_user['total_monthly_quota'] == 300) & (df_user['requests_used'] >= 800)]
    st.dataframe(copilot_upgrade[['user', 'requests_used', 'total_monthly_quota']])
else:
    st.info("User quota data not found.")

# 5. If not a full month, show estimated charts
st.header("Estimated Data (if not a full month)")
df_est = dfs["Estimated Monthly Premium Requests per User"]
if not df_est.empty and 'estimated_requests_used' in df_est.columns:
    st.subheader("Users Near or Above Quota (Estimated)")
    if 'total_monthly_quota' in df_est.columns:
        percent_threshold_est = st.slider(
            "Show estimated users at or above this percent of quota",
            min_value=0, max_value=100, value=90, step=1, key="est_percent_threshold"
        )
        df_est['percent_of_quota'] = df_est['estimated_requests_used'] / df_est['total_monthly_quota']
        near_quota_est = df_est[df_est['percent_of_quota'] >= percent_threshold_est / 100]
        st.dataframe(near_quota_est[['user', 'estimated_requests_used', 'total_monthly_quota', 'percent_of_quota']])
    st.subheader("Copilot Enterprise Upgrade Savings (Estimated)")
    if 'total_monthly_quota' in df_est.columns:
        copilot_upgrade_est = df_est[(df_est['total_monthly_quota'] == 300) & (df_est['estimated_requests_used'] >= 800)]
        st.dataframe(copilot_upgrade_est[['user', 'estimated_requests_used', 'total_monthly_quota']])
else:
    st.info("Estimated monthly data not found.")

# 6. Data explorer
st.header("Explore CSV Outputs")
csv_choice = st.selectbox("Select CSV to view", list(csv_files.keys()))
df_selected = dfs[csv_choice]
if not df_selected.empty:
    st.dataframe(df_selected)
    csv = df_selected.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, f"{csv_choice.replace(' ', '_').lower()}.csv", "text/csv")
else:
    st.info("No data available for selected CSV.")

# 7. Export to PDF
st.header("Export Dashboard to PDF")
if st.button("Export to PDF"):
    figs = []
    if 'fig_line' in locals():
        figs.append(fig_line)
    if 'fig_pie' in locals():
        figs.append(fig_pie)
    tables = [
        ("Users Near or Above Quota", near_quota if 'near_quota' in locals() else pd.DataFrame()),
        ("Copilot Enterprise Upgrade Savings", copilot_upgrade if 'copilot_upgrade' in locals() else pd.DataFrame()),
        ("Users Near or Above Quota (Estimated)", near_quota_est if 'near_quota_est' in locals() else pd.DataFrame()),
        ("Copilot Enterprise Upgrade Savings (Estimated)", copilot_upgrade_est if 'copilot_upgrade_est' in locals() else pd.DataFrame()),
    ]
    pdf_file = export_pdf(figs, tables, max_rows_per_page=30)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, pdf_file, "application/pdf", key="pdf-download")
