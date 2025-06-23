import streamlit as st

st.set_page_config(page_title="Spartan Order Checker", page_icon="🧾")

st.title("🧾 Spartan Order Checker")
st.markdown("Upload your documents below and let AI check for discrepancies.")

# File uploads
oa_file = st.file_uploader("📎 Upload Factory Order Acknowledgement", type=["pdf"])
spartan_po_file = st.file_uploader("📎 Upload Spartan Purchase Order", type=["pdf", "xlsx"])
customer_po_file = st.file_uploader("📎 (Optional) Upload Customer Purchase Order", type=["pdf", "xlsx"])
datasheet_file = st.file_uploader("📎 (Optional) Upload Datasheet", type=["pdf"])

# Placeholder for button
if st.button("🔍 Check for Discrepancies"):
    if not oa_file or not spartan_po_file:
        st.error("Please upload at least the OA and Spartan PO.")
    else:
        st.info("🔄 Running AI comparison... (This will work in Step 2!)")
        st.success("✅ Tags match\n⚠️ Price mismatch on Line 4\n✅ Calibration matches")
