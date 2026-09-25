import streamlit as st
from compound_screening_main import compound_screening

st.set_page_config(
    page_title="Compound Screening Test",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 SciAI — Compound Screening Test")

compound_screening()