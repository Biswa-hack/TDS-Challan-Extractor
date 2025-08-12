import streamlit as st
import re
import pandas as pd
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
import io

# -----------------------------
# Function to extract PDF info
# -----------------------------
def extract_info_from_pdf(file):
    try:
        reader = PdfReader(file)
        num_pages = len(reader.pages)
        text = ''
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text
    except PdfReadError:
        st.error(f"Error reading file: EOF marker not found or file is corrupted.")
        return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

    # Regex patterns for the fields
    patterns = {
        "Nature of Payment": r'Nature of Payment\s*:\s*(.*)',
        "Amount (in Rs.)": r'Amount \(in Rs\.\)\s*:\s*(.*)',
        "CIN": r'CIN\s*:\s*(.*)',
        "Bank Reference Number": r'Bank Reference Number\s*:\s*(.*)',
        "Date of Deposit": r'Date of Deposit\s*:\s*(.*)',
        "BSR code": r'BSR code\s*:\s*(.*)',
        "Challan No": r'Challan No\s*:\s*(.*)',
        "Tender Date": r'Tender Date\s*:\s*(.*)',
        "Major Head": r'Major Head\s*:\s*(.*)',
        "Assessment Year": r'Assessment Year\s*:\s*(.*)',
        "Financial Year": r'Financial Year\s*:\s*(.*)',
        "TAN": r'TAN\s*:\s*(.*)',
        "Name": r'Name\s*:\s*(.*)',
    }

    extracted_info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        extracted_info[key] = match.group(1).strip() if match else None

    # Updated monetary value patterns for "Tax Breakup Details"
    monetary_patterns = {
        "Tax": r'Tax\s*₹\s*([\d,]+)',
        "Surcharge": r'Surcharge\s*₹\s*([\d,]+)',
        "Cess": r'Cess\s*₹\s*([\d,]+)',
        "Interest": r'Interest\s*₹\s*([\d,]+)',
        "Penalty": r'Penalty\s*₹\s*([\d,]+)',
        "Fee under section 234E": r'Fee under section 234E\s*₹\s*([\d,]+)'
    }

    for key, pattern in monetary_patterns.items():
        match = re.search(pattern, text)
        if match:
            try:
                extracted_info[key] = float(re.sub(r'[₹,]', '', match.group(1)))
            except:
                extracted_info[key] = None
        else:
            extracted_info[key] = None

    # Convert "Amount (in Rs.)"
    amt_str = extracted_info.get("Amount (in Rs.)")
    if amt_str:
        try:
            extracted_info["Amount (in Rs.)"] = float(re.sub(r'[₹,]', '', amt_str))
        except:
            extracted_info["Amount (in Rs.)"] = None

    return extracted_info


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="PDF Data Extractor", layout="wide")

st.title("📄 PDF Data Extractor")
st.write("Upload one or more PDF files to extract payment, challan, and tax breakup details.")

uploaded_files = st.file_uploader(
    "Choose PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        info = extract_info_from_pdf(uploaded_file)
        if info:
            info["File Name"] = uploaded_file.name
            all_data.append(info)

    if all_data:
        df = pd.DataFrame(all_data)
        st.success(f"✅ Extracted data from {len(all_data)} file(s).")
        st.dataframe(df)

        # Download Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Extracted Data")
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name="extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠ No valid data extracted from the uploaded files.")
