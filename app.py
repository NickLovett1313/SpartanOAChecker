import streamlit as st
import os
import fitz  # PyMuPDF
from groq import Groq

# Connect to Groq with your secret key from Streamlit Cloud
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Page settings
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

# Button: run check
if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload both the OA and the PO.")
    else:
        st.info("🔄 Extracting and analyzing...")

        # Extract all text with no filter
        oa_text = extract_text_from_pdf(oa_file)
        po_text = extract_text_from_pdf(spartan_po_file)

        # Build strict prompt
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
Line 10: Model Number mismatch — OA=702DX32D1I6WA3WN1B4 vs PO=702DX32D1I6WA3WN1B5
Line 20: Tag SR1-01-XT-9025B missing in OA
Line 30: Prices match.
Line 40: Quantities match.
No other discrepancies found.
---

Here is the OA:
{oa_text[:30000]}

Here is the PO:
{po_text[:30000]}
"""

        # Call Groq using the new Llama 3.3 70B model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Show result
        st.success("✅ Check Complete")
        st.markdown(response.choices[0].message.content)
