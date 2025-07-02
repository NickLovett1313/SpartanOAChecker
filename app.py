import streamlit as st
import os
import fitz  # PyMuPDF
from groq import Groq

# Connect to Groq with your secret key from Streamlit Cloud
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# App title
st.set_page_config(page_title="Spartan Order Checker", page_icon="🧾")
st.title("🧾 Spartan Order Checker")
st.markdown("Upload your documents below and let AI check for discrepancies.")

# Upload boxes
oa_file = st.file_uploader("📎 Upload Factory Order Acknowledgement", type=["pdf"])
spartan_po_file = st.file_uploader("📎 Upload Spartan Purchase Order", type=["pdf"])

# Function to extract all text from a PDF
def extract_text_from_pdf(file):
    if file is None:
        return ""
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Function to keep only relevant lines
def extract_relevant_lines(text):
    lines = text.split('\n')
    relevant = []
    for line in lines:
        if any(keyword in line for keyword in [
            "Model", "Tag", "Serial", "Qty", "Unit Price", "Price",
            "Calibration", "Tag#", "DATE", "Ship date", "PO#", "Item Number"
        ]):
            relevant.append(line.strip())
    return "\n".join(relevant)

# BUTTON — This does everything when clicked
if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload both the OA and the PO.")
    else:
        st.info("🔄 Extracting and analyzing...")

        # Step 1: Extract text from PDFs
        raw_oa_text = extract_text_from_pdf(oa_file)
        raw_po_text = extract_text_from_pdf(spartan_po_file)

        # Step 2: Keep only relevant lines to stay under Groq's token limit
        oa_text = extract_relevant_lines(raw_oa_text)
        po_text = extract_relevant_lines(raw_po_text)

        # Step 3: Build the strict prompt
        prompt = f"""
You are a strict purchase order checker.

Your job is to compare these two documents:
1️⃣ The Factory Order Acknowledgement (OA)
2️⃣ The Spartan Purchase Order (PO)

Check them line-by-line for:
- ✅ Model Numbers
- ✅ Tags or Tag Numbers
- ✅ Quantities
- ✅ Unit Prices
- ✅ Dates
- ✅ Calibration data

Your goal is to:
- Find ANY mismatches, even small differences.
- Ignore unimportant differences like addresses or generic T&Cs.
- Always be precise: If something does NOT match, clearly say what line, what field, and what the values are.

Respond with a clear summary, like this:

Example:
---
Line 10: Model Number mismatch — OA=702DX32D1I6WA3WN1B4 vs PO=702DX32D1I6WA3WN1B5
Line 20: Tag SR1-01-XT-9025B missing in OA
Line 30: Prices match.
Line 40: Quantities match.
No other discrepancies found.
---

Here is the OA:
{oa_text[:15000]}

Here is the PO:
{po_text[:15000]}
"""

        # Step 4: Call Groq
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Step 5: Show results
        st.success("✅ Check Complete")
        st.markdown(response.choices[0].message.content)
