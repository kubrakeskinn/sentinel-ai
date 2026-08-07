import streamlit as st

st.set_page_config(page_title="Sentinel AI", page_icon="🛡️")
st.title("Sentinel AI")

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
else:
    st.info("Upload a video to begin.")
