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

        # === FINAL STRICT FLAGGER PROMPT ===
        prompt = f"""
You are a strict FLAGGER, not a problem solver.  
Your only job is to compare two documents:  
1️⃣ The Factory Order Acknowledgement (OA)  
2️⃣ The Spartan Purchase Order (PO)  

👉 Go line-by-line, in order.  
👉 For each line, compare:  
- Model Number  
- Expected Date (OA) vs Requested Date (PO)  
- Unit Price and Total Price  
- Quantity  
- Tags or Tag Numbers (treat minor formatting differences like dashes or spaces as the same — only flag true mismatches)
- Calibration data if available (only flag if different)

✅ If a line has a tag in the OA but not in the PO (or vice versa), flag it.  
✅ Flag even tiny price differences down to $0.01.  
✅ If the PO Number at the top is different, flag it.  
✅ At the end, compare the final order total price — if it’s different, flag it (do not explain why).

⚖️ How to output:

1️⃣ Expected vs Requested Dates Table:
- Only show this table if you find any lines with date differences.
- If all dates match, do not show the table.
- Before the table, write: “The expected ship date in the OA and requested ship date in the PO are different as shown below.”

Format:
| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines X-X | <OA Date> | Lines X-X | <PO Date> |
(Only include lines where dates differ.)

2️⃣ Numbered List of Discrepancies:
- After the table (or first if no table), output a numbered list in order of the lines.
- Each discrepancy must include:
   • The line number in OA and PO  
   • The field that does not match (Model #, Price, Quantity, Tags, Calibration)  
   • Show the OA value vs PO value side-by-side  
   • Highlight the actual part that is different in **bold**

✅ Example:  
1. Line 330: Unit Price mismatch — OA=$**3499.61** vs PO=$**3499.60**  
2. Line 420: Tag present in PO but missing in OA  
3. Line 530: Quantity mismatch — OA=**2** vs PO=**5**  
4. Order total mismatch — OA=$XXX.XX vs PO=$XXX.XX

✅ Do NOT output “matches” or mention lines that match — just skip them.  
✅ Do NOT suggest reasons or solutions — just flag the facts.

✅ End your output with:  
“No other discrepancies found.” if any were flagged, or  
“No discrepancies found.” if the docs match perfectly.

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
