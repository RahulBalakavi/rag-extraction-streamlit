import pdfplumber as pdfplumber
import streamlit as st

st.title('PDF extraction for RAG')


def extract_data(feed):
    data = []
    with pdfplumber.load(feed) as pdf:
        pages = pdf.pages
        for p in pages:
            data.append(p.extract_tables())
    return data  # build more code to return a dataframe


uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")
if uploaded_file is not None:
    data = extract_data(uploaded_file)
    st.write(data)
