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
You are a strict but smart purchase order checker.

✅ Your job is to compare these two documents:
1️⃣ The Factory Order Acknowledgement (OA)
2️⃣ The Spartan Purchase Order (PO)

👉 Check line-by-line for:
- Model Number
- Expected Date (from OA) vs Requested Date (from PO)
- Unit Price and Total Price
- Tags or Tag Numbers (treat minor formatting differences like dashes or spaces as matching)
- Calibration data if available
- The main PO Number at the top of each document (must match)

⚖️ When comparing lines:
- Focus on lines that contain a model number.
- Ignore serial codes, “Sold To” sections, headers, legal terms, or shipping details.
- For dates: build a table showing lines in OA with their expected date and lines in PO with their requested date.
- If the OA or PO shows multiple tags for one line or one tag for multiple lines, just check that the total quantity and total price are consistent.
- Ignore duplicate tags if they do not change the quantity.

📋 Format your response exactly like this:

1. **Expected vs Requested Dates Table**

| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines 10-160 | Jul 28, 2025 | Lines 10-160 | Jun 25, 2025 |
| Lines 170-360 | Aug 08, 2025 | Lines 170-360 | Jun 25, 2025 |
...(use as many rows as needed)

2. **Other Discrepancies**
- Model Number mismatch on Line XX if any.
- Tags do not match for Model XYZ.
- PO Numbers do not match.
- Any other relevant issues.

✅ End with “No other discrepancies found.” if there are no other issues.

Here is the OA:
{oa_text[:30000]}

Here is the PO:
{po_text[:30000]}
"""

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
