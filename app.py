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
- Tags or Tag Numbers (treat minor formatting differences like dashes or spaces as the same — only flag real tag mismatches)
- Calibration data if available (only flag if different)
- The main PO Number at the top of each document (must match)

⚖️ When comparing:
- Focus only on lines that contain a model number.
- Ignore serial codes, “Sold To” sections, addresses, generic headers, payment terms, taxes except for tariffs.
- For ship dates:
   - Only show a table if there are any date differences.
   - List only the lines that have different OA Expected Date and PO Requested Date.
   - If all dates match, do not output a table.

- For the final order total:
   - Compare the total prices in the OA and PO.
   - If the total prices match, do not mention them.
   - If they are different, check if there is a “Tariff” or “Duty” listed in either document that explains the difference.
   - If the difference is due to tariff/duty, say: “Order total difference is due to tariff charge.”
   - If no tariff/duty is found, list both totals and say: “Order totals differ with no clear tariff explanation.”

🚫 Do NOT mention tag formatting differences.
🚫 Do NOT output “Calibration matches” — only flag if there is a real mismatch.

📋 Format your response exactly like this:

If any date differences exist:
The expected ship date in the OA and requested ship date in the PO are compared below.

1. **Expected vs Requested Dates Table**

| OA Lines | OA Expected Date | PO Lines | PO Requested Date |
|----------|------------------|----------|--------------------|
| Lines X-X | <OA Date> | Lines X-X | <PO Date> |
| (Only include lines where dates differ.) |

2. **Other Discrepancies**
- Model Number mismatch on Line XX if any.
- Tags differ for Model XYZ if truly different.
- PO Numbers do not match.
- Calibration data mismatch if any.
- Final order total difference if any (with tariff check).

✅ End with: “No other discrepancies found.” or “No discrepancies found.” if clean.

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
