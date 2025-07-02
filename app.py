import streamlit as st
import os
import fitz  # PyMuPDF
from groq import Groq

# Get your Groq API key from Streamlit secrets
client = Groq(api_key=os.environ["GROQ_API_KEY"])

st.set_page_config(page_title="Spartan Order Checker", page_icon="🧾")
st.title("🧾 Spartan Order Checker")
st.markdown("Upload your documents below and let AI check for discrepancies.")

# Uploads
oa_file = st.file_uploader("📎 Upload Factory Order Acknowledgement", type=["pdf"])
spartan_po_file = st.file_uploader("📎 Upload Spartan Purchase Order", type=["pdf"])

# Extract PDF text
def extract_text_from_pdf(file):
    if file is None:
        return ""
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload at least the OA and Spartan PO.")
    else:
        st.info("🔄 Extracting and analyzing...")

        # Extract text
        oa_text = extract_text_from_pdf(oa_file)
        po_text = extract_text_from_pdf(spartan_po_file)

        # Build prompt for Mixtral
        prompt = f"""
You are a strict order checker.
Compare these two documents for any discrepancies in:
- Model Numbers
- Tags
- Dates
- Prices
- Calibration data

Be line-by-line. Flag ANY mismatch. Be explicit.

OA:
{oa_text[:12000]}

PO:
{po_text[:12000]}
"""

        # Call Groq Mixtral
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        st.success("✅ Check Complete")
        st.markdown(response.choices[0].message.content)
