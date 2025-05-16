import streamlit as st
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import uuid
from langgraph.types import Command
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.callbacks.manager import (
    dispatch_custom_event,
)
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig


class ReasoningHandler(BaseCallbackHandler):
    def __init__(self, isrequire):
        self.require = isrequire
    def on_custom_event(
        self,
        name: str,
        data: Any,
        *,
        run_id: UUID,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        print(self.require)
        if not self.require:
            # Just print for debugging but don't display
            print(name)
            print(data['data'])
            return
        
        st.markdown("""
        <style>
        .reasoning-header {
            color: #1E88E5;
            font-size: 20px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        .reasoning-content {
            font-size: 18px;
            line-height: 1.5;
            background-color: #f8f9fa;
            border-left: 4px solid #1E88E5;
            padding: 12px 15px;
            border-radius: 4px;
            margin-left: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if name == "determine_search":
            container = st.container()
            with container:
                # Add some empty space for left padding
                col1, col2 = st.columns([1, 2])
                with col2:
                    st.markdown('<div class="reasoning-header">🔍 Reasoning Step </div>', unsafe_allow_html=True)
            
            container = st.container()
            with container:
                # Add some empty space for left padding
                col1, col2 = st.columns([1, 20])
                with col2:
                    st.markdown(f'<div> 💻 {data['data']}</div>', unsafe_allow_html=True)
        elif name == "search_selection" or name == "sql_search_result" or name == "gen_sql_query_result" or name == "vector_search_result" or name == "require_human_feedback_result" :
            container = st.container()
            with container:
                # Add some empty space for left padding
                col1, col2 = st.columns([1, 15])
                with col2:
                    st.markdown(f'<div> ✔️ {data['data']}</div>', unsafe_allow_html=True)
        else:
            container = st.container()
            with container:
                # Add some empty space for left padding
                col1, col2 = st.columns([1, 20])
                with col2:
                    st.markdown(f'<div> 💻 {data['data']}</div>', unsafe_allow_html=True)
        print(name)
        print(data['data'])

class DisplayResultStreamlit:
    def __init__(self, graph, user_message, show_reasoning):
        self.show_reasoning = show_reasoning
        self.handler = ReasoningHandler(self.show_reasoning)
        self.graph = graph
        self.user_message = user_message
        self.config = {"callbacks":[self.handler], "tags":["cheese productions"], "configurable": {"thread_id": "1"}}

    def clean_chat_history(self, history):
        """Ensure all messages in chat history have valid content strings."""
        cleaned_history = []
        for message in history:
            # Make a copy of the message
            cleaned_message = message.copy()
            # Ensure content is a string
            if 'content' not in cleaned_message or cleaned_message['content'] is None:
                cleaned_message['content'] = ""
            cleaned_history.append(cleaned_message)
        return cleaned_history

    def display_result_on_ui(self):
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        graph = self.graph
        user_message = self.user_message
        print("display_result_on_ui")
        
        # Add and display user message first
        with st.chat_message("user"):
            st.write(user_message)
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        cleaned_history = self.clean_chat_history(st.session_state.chat_history)

        graph_config = st.session_state.get('graph_config', self.config)
        
        if st.session_state.get('current_feedback_state', False):
            print("command resume")
            human_command = Command(resume={
                "feedback": user_message,
                "history": cleaned_history   # Add this line
            })
            events = list(graph.stream(human_command, config = graph_config))    
            print(events)
            if events:
                last_event = events[-1]
                if "__interrupt__" in last_event:
                    interrupt_tuple = last_event["__interrupt__"]
                    interrupt_obj = interrupt_tuple[0]  # The Interrupt object is the first element
                    state = interrupt_obj.value
                    with st.chat_message("assistant"):
                        st.write(state['hitl_feedback_message'])
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": state['hitl_feedback_message']
                    }) 
                    st.session_state.current_feedback_state = True            
                    return
                for value in last_event.values():
                    if isinstance(value, dict) and "messages" in value:
                        assistant_messages = value["messages"]
                        with st.chat_message("assistant"):
                            st.write(assistant_messages)
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": assistant_messages
                        })
                        st.session_state.current_feedback_state = False
            
            # Reset feedback state after processing
            st.session_state.current_feedback_state = False
            return
        
        uuid_v1 = uuid.uuid1()
        st.session_state.graph_config = {"callbacks":[self.handler], "tags":["cheese productions"], "configurable": {"thread_id": uuid_v1}}
        events = list(graph.stream({'history': cleaned_history, 'query': user_message}, config=st.session_state.graph_config))
    
        # Only process the last event
        if events:
            last_event = events[-1]

            if "__interrupt__" in last_event:
                interrupt_tuple = last_event["__interrupt__"]
                interrupt_obj = interrupt_tuple[0]  # The Interrupt object is the first element
                state = interrupt_obj.value
                with st.chat_message("assistant"):
                    st.write(state['hitl_feedback_message'])
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": state['hitl_feedback_message']
                }) 
                st.session_state.current_feedback_state = True            
                return
            for value in last_event.values():
                if "messages" in value:
                    assistant_messages = value["messages"]
                    with st.chat_message("assistant"):
                        st.write(assistant_messages)
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": assistant_messages
                    })             
