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

        # === STRICT FLAGGER PROMPT — SMART VERSION ===
        prompt = f"""
You are a strict FLAGGER, not a problem solver.

Compare:
1️⃣ The Factory Order Acknowledgement (OA)
2️⃣ The Spartan Purchase Order (PO)

📋 What To Check:

Go line-by-line, in order, but only check lines that contain real item details:
- Model Number
- Quantity
- Unit Price and Total Price
- Expected Date (OA) vs Requested Date (PO)
- Tags (flag real mismatches or presence/absence)
- Calibration data if available (only flag if different)

✅ Ignore:
- General headers, legal disclaimers, supplier details, shipping info.
- Do not flag a field as “missing” if that line naturally doesn’t include it.
- Ignore carrier, shipping terms, and other irrelevant fields.

✅ PO Number Rule:
- Compare only the Customer PO Number (e.g., "2022.892-0929").
- Ignore Factory Order Number prefixes like "8303..." — they do not count as a mismatch.

✅ Always flag:
- Tiny price differences down to $0.01
- If the OA has a tariff charge but the PO does not, flag that
- If a tag is present in one but not the other, flag that
- If the PO Number is different, flag it
- Final order total difference — flag it but do not explain why

⚖️ How to output:

1️⃣ Expected vs Requested Dates Table:
- Show this table only if you find actual date differences.
- If all dates match, do not output the table.
- Before the table, write: “The expected ship date in the OA and requested ship date in the PO are different as shown below.”

Format:
| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines X-X | <OA Date> | Lines X-X | <PO Date> |
(Only include lines where dates differ.)

2️⃣ Numbered List of Discrepancies:
- After the table (or first if no table), output a numbered list in order of the lines.
- Each discrepancy must include:
  • OA and PO line numbers
  • The exact field (Model #, Qty, Price, Tags, Calibration)
  • OA value vs PO value side-by-side
  • Highlight the exact digits or text that differ in **bold**

✅ Example:
1. Line 330: Unit Price mismatch — OA=$**3499.61** vs PO=$**3499.60**
2. Line 530: Quantity mismatch — OA=**2** vs PO=**5**
3. Line 420: Tag present in PO but missing in OA
4. Order total mismatch — OA=$XXX.XX vs PO=$XXX.XX

✅ Do NOT output “matches” for lines that match.
✅ Do NOT suggest reasons — just flag the difference.

✅ End with:
“No other discrepancies found.” if anything was flagged,
or “No discrepancies found.” if all matches.

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
