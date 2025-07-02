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

        # Extract all text (no filter)
        oa_text = extract_text_from_pdf(oa_file)
        po_text = extract_text_from_pdf(spartan_po_file)

        # Build your final structured prompt
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
- Focus only on lines that contain a model number.
- Ignore serial codes, “Sold To” sections, addresses, legal sections, shipping details.
- For dates: build a table showing lines in OA with their expected date and lines in PO with their requested date.
- If the OA or PO shows multiple tags for one line or one tag for multiple lines, check that the total quantity and total price are consistent. Ignore duplicate tags that do not change the quantity.

🚫 Do NOT mention or flag payment terms, tax details, or general legal text.

📋 Format your response exactly like this:

1. **Expected vs Requested Dates Table**

| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines 10-160 | Jul 28, 2025 | Lines 10-160 | Jun 25, 2025 |
| Lines 170-360 | Aug 08, 2025 | Lines 170-360 | Jun 25, 2025 |
| ... | ... | ... | ... |

2. **Other Discrepancies**
- Model Number mismatch on Line XX if any.
- Tags inconsistent for Model XYZ.
- PO Numbers do not match.
- Any other real issues found.

✅ End with: “No other discrepancies found.” if there are no other issues.

Here is the OA:
{oa_text[:30000]}

Here is the PO:
{po_text[:30000]}
"""

        # Call Groq using the current Llama model
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
