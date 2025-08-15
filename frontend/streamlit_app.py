import streamlit as st
import requests

st.set_page_config(page_title="Medical Insurance Chat", layout="centered")
st.title("💬 Medical Insurance Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask a question about your insurance PDF")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        full_response = ""
        message_placeholder = st.empty()

        try:
            response = requests.post(
                "http://backend:8000/query",
                json={"question": user_input},
                stream=True,
                timeout=300,  
            )

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        decoded = chunk.decode("utf-8", errors="ignore")
                        full_response += decoded
                        message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                message_placeholder.markdown("Error from backend.")
        except Exception as e:
            st.error(f"Request failed: {e}")
