import streamlit as st
import os
import fitz  # PyMuPDF
from groq import Groq

# Connect to Groq
client = Groq(api_key=os.environ["GROQ_API_KEY"])

st.title("🧾 Spartan Order Checker")

# Upload UI
oa_file = st.file_uploader("Upload Factory Order Acknowledgement", type=["pdf"])
spartan_po_file = st.file_uploader("Upload Spartan Purchase Order", type=["pdf"])

# Add your helper functions here:
def extract_text_from_pdf(file):
    if file is None:
        return ""
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_relevant_lines(text):
    lines = text.split('\n')
    relevant = []
    for line in lines:
        if any(keyword in line for keyword in ["Model", "Tag", "Serial", "Qty", "Unit Price", "Price", "Calibration", "Tag#", "DATE", "Ship date", "PO#", "Item Number"]):
            relevant.append(line.strip())
    return "\n".join(relevant)

# BUTTON LOGIC
if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload both files.")
    else:
        st.info("🔄 Extracting and analyzing...")

        raw_oa_text = extract_text_from_pdf(oa_file)
        raw_po_text = extract_text_from_pdf(spartan_po_file)

        oa_text = extract_relevant_lines(raw_oa_text)
        po_text = extract_relevant_lines(raw_po_text)

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

Respond with a clear summary like this:
---
Line 10: Model Number mismatch — OA=... vs PO=...
...

Here is the OA:
{oa_text[:15000]}

Here is the PO:
{po_text[:15000]}
"""

        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        st.success("✅ Check Complete")
        st.markdown(response.choices[0].message.content)
