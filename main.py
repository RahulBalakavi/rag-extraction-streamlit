import streamlit as st
import fitz

st.title('PDF extraction for RAG')

def extract_data(file_name):
    doc = fitz.open(file_name)  # open a document
    pdf_data = []
    for page in doc:  # iterate the document pages
        text = page.get_text().encode("utf8")  # get plain text (is in UTF-8)
        pdf_data.append(text)
        pdf_data.append("------------------------------")
    return pdf_data


uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")
if uploaded_file is not None:
    data = extract_data(uploaded_file)
    st.write(data)
