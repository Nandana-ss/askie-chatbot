# app.py
import streamlit as st
from utils import create_agent, chat_with_agent

st.set_page_config(page_title="Askie bot", layout="centered")
def clear_input():
    st.session_state.chat_input = ""
st.markdown("""
    <style>

    .main .block-container {
        max-width: 650px;
    margin: 5rem auto;
    padding: 2rem;
    background-color: #ffffff;  /* light background for contrast */
    border-radius: 12px;
    box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.08); /* soft shadow */
    border: 1px solid #eee; /* subtle border */
    }
            
   h1{
        text-align: center;
            color:grey;
    }
   h2, h3{
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
        padding-bottom: 0.3rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #eaeaea;
            }      
    /* Chat bubbles */
    .message-box {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        max-width: 90%;
        line-height: 1.4;
    }

    .user-msg {
    background-color: #dceeff;
    color: #334;
    margin-left: auto;
    text-align: right;
    padding: 14px 18px;
    border-radius: 12px;
    max-width: 90%;
    font-family: 'Segoe UI', sans-serif;
    font-size: 16px;
    font-weight: 500;
    margin-top: 12px;
    margin-bottom: 8px;
}


    .bot-msg {
    background: linear-gradient(145deg, #f7f7f7, #e6e6e6);
    color: #1a1a1a;
    border-left: 5px solid #6C63FF;
    padding: 14px 18px;
    margin-right: auto;
    margin-top: 12px;
    margin-bottom: 8px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    font-size: 17px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
    max-width: 90%;
}

input[type="text"] {
    border: 2px solid #ccc !important;
    border-radius: 8px !important;
    padding: 8px 12px;
    font-size: 16px;
}
    </style>
""", unsafe_allow_html=True)

st.title("Askie bot")

# Session State Init
if "email" not in st.session_state:
    st.session_state.email = ""
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Section 1: Context
st.markdown("### Provide Training Context")
file_upload = st.file_uploader("Upload a .txt file with your context:", type="txt")
text_context = st.text_area("Or paste your training content below:", height=150)

if st.button("Save Context"):
    if file_upload is not None:
        content = file_upload.read().decode("utf-8")
    elif text_context.strip():
        content = text_context
    else:
        content = None

    if content:
        result = create_agent(content)
        st.session_state.assistant_id = result["assistant_id"]
        st.session_state.thread_id = result["thread_id"]
        st.success("Context uploaded and assistant initialized.")
    else:
        st.warning("Please upload a file or paste some context.")

# Section 2: Email
st.markdown("### Enter Your Email")
email_input = st.text_input("Your Email")
if st.button("Save Email"):
    if email_input and "@" in email_input:
        st.session_state.email = email_input
        st.success("Email saved.")
    else:
        st.error("Enter a valid email address.")

# Section 3: Chat
st.markdown("### Chat with the Bot")
if st.session_state.assistant_id and st.session_state.thread_id:
    user_msg = st.text_input(
    "💡 Ask something based on your content",
    key="chat_input"
)
    if user_msg:
     st.markdown(f"<div class='message-box user-msg'>🧑‍💻 <strong>You:</strong> {user_msg}</div>", unsafe_allow_html=True)
     reply = chat_with_agent(
        thread_id=st.session_state.thread_id,
        message=user_msg,
        user_email=st.session_state.email,
        assistant_id=st.session_state.assistant_id
    )
     st.markdown(f"<div class='message-box bot-msg'>🤖 <strong>Bot:</strong> {reply}</div>", unsafe_allow_html=True)

    # Clear input on next rerun
     st.experimental_rerun()
else:
    st.info("Please upload or paste context and save your email before chatting.")
