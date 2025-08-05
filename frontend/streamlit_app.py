import streamlit as st
import requests

st.set_page_config(page_title="Medical Insurance Chat", layout="centered")
st.title("Medical Insurance Assistant")

# chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_input = st.chat_input("Ask a question about your insurance!")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            
            response = requests.post(
                "http://backend:8000/query",
                json={"question": user_input},
                stream=True,
                timeout=60
            )

            if response.status_code == 200:
                
                def stream_chunks_and_store():
                    collected_text = ""
                    for chunk in response.iter_content(chunk_size=1):
                        if chunk:
                            decoded = chunk.decode("utf-8")
                            collected_text += decoded
                            yield collected_text
                    st.session_state.generated_response = collected_text

                message_placeholder.write_stream(stream_chunks_and_store())
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": st.session_state.generated_response
                })
                del st.session_state.generated_response 

            else:
                message_placeholder.markdown("Backend error.")
        except Exception as e:
            st.error(f"Request failed: {e}")
