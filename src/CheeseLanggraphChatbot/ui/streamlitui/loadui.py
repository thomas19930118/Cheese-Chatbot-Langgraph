import streamlit as st
import os
from datetime import date
from dotenv import load_dotenv
from langchain_core.messages import AIMessage,HumanMessage
from src.CheeseLanggraphChatbot.ui.uiconfigfile import Config

load_dotenv()

REASONING_TOGGLE_KEY = "reasoning_toggle_state"
LANGSMITH_DASHBOARD_URL = os.getenv('LANGSMITH_DASHBOARD_URL')

class LoadStreamlitUI:
    def __init__(self):
        self.config =  Config() # config
        self.user_controls = {}

    def initialize_session(self):
        return {
        "current_step": "requirements",
        "requirements": "",
        "user_stories": "",
        "po_feedback": "",
        "generated_code": "",
        "review_feedback": "",
        "decision": None
    }
  
    def _start_new_chat(self):
        """Callback function to reset chat-related session state."""
        st.session_state.chat_history = []
        if 'current_feedback_state' in st.session_state:
            st.session_state.current_feedback_state = False
        # Reset any input fields that might carry over
        if 'timeframe' in st.session_state: # Assuming timeframe is the chat input variable
            st.session_state.timeframe = ''
        if 'IsFetchButtonClicked' in st.session_state:
             st.session_state.IsFetchButtonClicked = False
        # If there are other chat-specific states, reset them here.
        # For example, if the main 'state' for the graph should be reset:
        # st.session_state.state = self.initialize_session() 
        # However, this might be too broad, let's start with chat history and feedback.
        st.rerun() # Force a rerun to reflect the cleared chat immediately


    def load_streamlit_ui(self):
        st.set_page_config(page_title= "🤖 " + self.config.get_page_title(), layout="wide")
        st.header("🤖 " + self.config.get_page_title())
        st.session_state.timeframe = ''
        st.session_state.IsFetchButtonClicked = False
        st.session_state.IsSDLC = False

        if REASONING_TOGGLE_KEY not in st.session_state:
            st.session_state[REASONING_TOGGLE_KEY] = True # Default: Show reasoning

        with st.sidebar:

            st.link_button("LangSmith Dashboard", LANGSMITH_DASHBOARD_URL, help="Opens the LangSmith project dashboard in a new tab.")
            st.button("Start New Chat", on_click=self._start_new_chat, help="Clears the current conversation and starts a new one.")
            
            st.divider()

            # Get options from config
            model_options = self.config.get_model_options()
            selected_model = st.selectbox("Select Model", model_options)

            # Initialize chat history and previous model if not present
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            if "prev_model" not in st.session_state:
                st.session_state.prev_model = selected_model

            # If the model has changed, clear chat history
            if selected_model != st.session_state.prev_model:
                st.session_state.chat_history = []
                st.session_state.prev_model = selected_model

            st.checkbox(
                "Show Reasoning Steps", 
                key=REASONING_TOGGLE_KEY
            )
            

            self.user_controls["selected_model"] = selected_model
            self.user_controls["show_reasoning"] = st.session_state[REASONING_TOGGLE_KEY]

            if "state" not in st.session_state:
                st.session_state.state = self.initialize_session()

        return self.user_controls