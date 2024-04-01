import base64
from tempfile import NamedTemporaryFile

import pandas as pd
import streamlit as st
import fitz

from pdf_extracted_data import PDFExtractedDataPage, PDFExtractedData
from pymupdf_utilities import extract_images


############################# Extraction Methods #############################

def extract_data(file_path, file_bytes):
    if pdf_extraction_option == "PyMuPDF":
        return extract_data_pymupdf(file_bytes)
    elif pdf_extraction_option == "llmsherpa":
        return extract_data_llmsherpa(file_path)
    else:
        return extract_data_pymupdf(file_bytes)


def extract_images_from_pymupdf_page(doc):
    return extract_images.extract_images(doc)


def extract_data_pymupdf(file_bytes) -> PDFExtractedData:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pdf_data = PDFExtractedData()
    for page in doc:  # iterate the document pages
        pdf_page = PDFExtractedDataPage()
        page_str = ""
        pdf_page.text = str(page.get_text().encode("utf8"))  # get plain text (is in UTF-8)
        # Tables.
        tabs = page.find_tables()
        for tab in tabs:
            pdf_page.tables.append(tab.to_pandas())
        pdf_data.pages.append(pdf_page)
        # Images.
    if len(pdf_data.pages) > 0:
        pdf_data.pages[0].images = extract_images_from_pymupdf_page(doc)
    return pdf_data


def extract_data_llmsherpa(file_path) -> PDFExtractedData:
    from llmsherpa.readers import LayoutPDFReader

    llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
    pdf_reader = LayoutPDFReader(llmsherpa_api_url)
    doc = pdf_reader.read_pdf(file_path)
    pdf_data = PDFExtractedData()
    # llmsherpa doesn't return data per page, but does it as an aggregate. So creating just a single page.
    pdf_page = PDFExtractedDataPage()
    pdf_page.text = doc.to_text()
    pdf_page.sections = doc.sections()
    for tbl in doc.tables():
        pd_table = pd.read_html(tbl.to_html())
        if len(pd_table) > 0:
            pdf_page.tables.append(pd_table[0])
    pdf_data.pages.append(pdf_page)
    return pdf_data


#############################################################################

############################# Chunking Methods ##############################


LLAMA_INDEX_CHUNKING_OPTS = {
    "chunk_size": 256,
    "chunk_overlap": 20
}

FIXED_SIZE_CHUNKING_OPTS = {
    "chunk_size": 256,
    "chunk_overlap": 20
}


def extract_chunks_fixed_size(text):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=FIXED_SIZE_CHUNKING_OPTS["chunk_size"],
        chunk_overlap=FIXED_SIZE_CHUNKING_OPTS["chunk_overlap"]
    )

    docs = text_splitter.create_documents([text])
    doc_chunks = [doc.page_content for doc in docs]
    return doc_chunks


def combine_text_from_pages(pdf_extracted_data: PDFExtractedData):
    text = ""
    for page in pdf_extracted_data:
        text += page.text
    return text


def extract_chunks(pdf_extracted_data: PDFExtractedData):
    if text_chunking_option == "Fixed size":
        return extract_chunks_fixed_size(combine_text_from_pages(pdf_extracted_data))
    else:
        return ""


#############################################################################


def extract():
    if uploaded_file_bytes is not None:
        # Show PDF in one tab.
        base64_pdf = base64.b64encode(uploaded_file_bytes).decode('utf-8')
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        pdf_iframe.markdown(pdf_display, unsafe_allow_html=True)
        # Write pdf extracted data in another tab.
        with NamedTemporaryFile(dir='.', suffix='.csv') as f:
            f.write(uploaded_file_bytes)
            data = extract_data(f.name, uploaded_file_bytes)
            text = []
            for page in data:
                text.append(page.text)
            extracted_text.write(text)
            # Images.
            images = []
            for page in data:
                for image in page.images:
                    images.append(image)
            extracted_images.image(images)
            # Tables.
            for page in data:
                for table in page.tables:
                    extracted_tables.table(table)
                    extracted_tables.divider()
            # Sections.
            for page in data:
                for section in page.sections:
                    extracted_sections.write(section.to_text())
                    extracted_sections.divider()

        # Write extracted chunks in another tab.
        chunks = extract_chunks(data)
        extracted_chunks.write(chunks)


st.title('PDF extraction for RAG')

pdf_extraction_option = st.selectbox(
    "Which PDF extraction method would you like to use?",
    ("PyMuPDF", "llmsherpa"),
    index=0,
    placeholder="Select PDF extraction method...",
)

st.write('PDF Extraction Method:', pdf_extraction_option)

text_chunking_option = st.selectbox(
    "Which text chunking method would you like to use?",
    ("Fixed size", "semantic chunking (TBD)", "HYDE (TBD)"),
    index=0,
    placeholder="Select text chunking method...",
)

st.write('Text Chunking Method:', text_chunking_option)

if text_chunking_option == "llamaindex":
    LLAMA_INDEX_CHUNKING_OPTS["chunk_size"] = st.slider('chunk size', 100, 500, 256, on_change=extract)
    LLAMA_INDEX_CHUNKING_OPTS["chunk_overlap"] = st.slider('chunk overlap', 0, 200, 20, on_change=extract)
elif text_chunking_option == "Fixed size":
    FIXED_SIZE_CHUNKING_OPTS["chunk_size"] = st.slider('chunk size', 100, 500, 256, on_change=extract)
    FIXED_SIZE_CHUNKING_OPTS["chunk_overlap"] = st.slider('chunk overlap', 0, 200, 20, on_change=extract)

uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")
uploaded_file_bytes = None
if uploaded_file is not None:
    uploaded_file_bytes = uploaded_file.read()

pdf_iframe, \
    extracted_text, \
    extracted_images, \
    extracted_tables, \
    extracted_sections, \
    extracted_chunks = \
    st.tabs(["PDF",
             "Extracted lines",
             "Extracted Images",
             "Extracted Tables",
             "Extracted Sections",
             "Extracted Chunks"
             ])

extract()
