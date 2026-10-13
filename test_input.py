import streamlit as st

st.title("Search Input Test")

query = st.text_input(
    "Ask your question",
    placeholder="Enter Tamil or English text",
    key="test_search_query",
)

st.write("Current query:", repr(query))