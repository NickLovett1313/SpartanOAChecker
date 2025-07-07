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

# Extract all text from PDF
def extract_text_from_pdf(file):
    if file is None:
        return ""
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Filter: keep only relevant lines to stay under token limits
def extract_relevant_lines(text):
    lines = text.split('\n')
    relevant = []
    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in [
            "cust line", "order line", "description",
            "qty", "quantity", "unit price", "total amount",
            "expected ship date", "requested ship date",
            "tag", "configuration", "surcharge", "tariff", "total usd", "po#"
        ]):
            relevant.append(line.strip())
    return "\n".join(relevant)

# Button: run check
if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload both the OA and the PO.")
    else:
        st.info("🔄 Extracting and analyzing...")

        # Extract + filter text
        raw_oa_text = extract_text_from_pdf(oa_file)
        raw_po_text = extract_text_from_pdf(spartan_po_file)

        oa_text = extract_relevant_lines(raw_oa_text)
        po_text = extract_relevant_lines(raw_po_text)

        # === FINAL SMART PROMPT ===
        prompt = f"""
You are a strict but smart purchase order checker.

✅ Your job is to compare these two documents:
1️⃣ The Factory Order Acknowledgement (OA)
2️⃣ The Spartan Purchase Order (PO)

👉 Check line-by-line for:
• Model Number
• Expected Date (from OA) vs Requested Date (from PO)
• Unit Price and Total Price, and order total price at the bottom
• Tags or Tag Numbers (treat minor formatting differences like dashes or spaces as the same — only flag real mismatches)
• Calibration data if available (only flag if different)
• The main PO Number at the top of each document (must match, ignore prefix numbers like '830355663/' if the rest matches)
• Make sure all lines match up — e.g., Line 10 in OA should have the same info as Line 10 in PO

⚖️ When comparing:
• Focus only on lines that contain a model number.
• Ignore serial codes, “Sold To” sections, addresses, generic headers, payment terms, and tax details except for tariffs/duties.
• For ship dates:
  o Only show a table if there are any date differences.
  o List only the lines that have different OA Expected Date and PO Requested Date.
  o If all dates match, do not output a table.
  o Before the table, write: “The expected ship date in the OA and requested ship date in the PO are different as shown below.”

• For the final order total:
  o Compare the total prices in the OA and PO.
  o If the total prices match, do not mention them.
  o If they are different, check if there is a “Tariff” or “Duty” line that explains the difference.
  o If the difference is due to a tariff/duty, say: “Order total difference is due to tariff charge.”
  o If no tariff/duty is found, list both totals and say: “Order totals differ with no clear tariff explanation.”

🚫 Do NOT mention tag formatting differences.
🚫 Do NOT output “Calibration matches” — only flag if there is a real mismatch.
🚫 Do NOT list lines that fully match — skip them.

📋 Format your response exactly like this:

If any date differences exist:
The expected ship date in the OA and requested ship date in the PO are different as shown below.

1. Expected vs Requested Dates Table

| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines X-X | <OA Date> | Lines X-X | <PO Date> |
(Only include lines where dates differ.)

2. Other Discrepancies
• Only list lines where there is a real mismatch.
• For each mismatch, show exactly what is different. Use **bold** to highlight the specific part that is different so it is clear at a glance.
  Example: Line 90: IC**0063**-NC (OA) vs IC**0100**-NC (PO)
• Always show the exact line numbers for context.
• PO Number mismatch if any.
• Tags mismatch if truly different.
• Calibration data mismatch if any.
• Final order total difference with tariff explanation or not.

✅ End with: “No other discrepancies found.” or “No discrepancies found.” if clean.

Here is the OA:
{oa_text[:8000]}

Here is the PO:
{po_text[:8000]}
"""

        # Call Groq using the Llama model
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
