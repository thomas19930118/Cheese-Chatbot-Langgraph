import json
import streamlit as st
from typing import List, Dict
from src.CheeseLanggraphChatbot.db.vectordb import vector_db
from src.CheeseLanggraphChatbot.db.mysql import mysql_db
from langchain_core.messages import SystemMessage, HumanMessage
from src.CheeseLanggraphChatbot.graph.graph_state import GraphState, DatabaseEnum
from src.CheeseLanggraphChatbot.template.prompt_templates.sql_vector import sql_vector
from src.CheeseLanggraphChatbot.template.prompt_templates.generate_sql import generate_sql
from src.CheeseLanggraphChatbot.template.prompt_templates.generate_response import generate_response
from src.CheeseLanggraphChatbot.template.prompt_templates.generate_feedback import feedback_prompt
from src.CheeseLanggraphChatbot.template.function_templates.sql_vector import sql_vector_tool
from langchain_core.callbacks.manager import (
    dispatch_custom_event,
)

class BasicChatbotNode:
    """
    Basic chatbot logic implementation.
    """
    def __init__(self,model):
        self.model = model
        
    def reasoning_node(self, state: GraphState) -> GraphState:
        if state.feedback:
            state.query = self.get_base_string(state.feedback)
            state.feedback = ''
            state.requires_human_review = False
            print(state.query)
        dispatch_custom_event("determine_search", {"data": "Let's determine to use which search: sql search or vector search."})
        return state
    
    def extract_function_params(self, prompt, function):
        function_name = function[0]["function"]["name"]
        arg_name = list(function[0]["function"]["parameters"]['properties'].keys())[0]
        model_ = self.model.bind_tools(function, tool_choice=function_name)
        messages = [SystemMessage(prompt)]
        tool_call = model_.invoke(messages).tool_calls
        prop = tool_call[0]['args'][arg_name]

        return prop
    
    def format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

    def determine_database(self, state: GraphState) -> DatabaseEnum:
        which_db = self.extract_function_params(prompt=sql_vector.format(
            query=state.query,
            conversation=self.format_conversation_history(state.history)
        ), function=sql_vector_tool)
        if which_db == "sql":
            dispatch_custom_event("search_selection", {"data": "Result =>  Let's use the sql search"})
            return DatabaseEnum.MYSQL
        elif which_db == "vector":
            dispatch_custom_event("search_selection", {"data": "Result =>  Let's use the vector search"})
            return DatabaseEnum.VECTORDB
        elif which_db == "parallel":
            dispatch_custom_event("search_selection", {"data": "Result =>  Let's use the parallel search with sql and vectorDB"})
            return DatabaseEnum.PARALLEL
        elif which_db == "nodb":
            dispatch_custom_event("search_selection", {"data": "Result =>  DB is unnecessary"})
            return DatabaseEnum.NoDB
    def gen_sql_query_node(self, state: GraphState) -> GraphState:
        print("gen_sql_query_node")
        dispatch_custom_event("gen_sql_query_start", {"data": "Let's generate the sql query for the user question."})
        state.database = DatabaseEnum.MYSQL
        response = self.model.invoke([SystemMessage(generate_sql.format(
            query=state.query,
            conversation=self.format_conversation_history(state.history)
        ))])
        state.sql_query = response.content.strip().replace('``sql', '').replace('`', '')
        dispatch_custom_event("gen_sql_query_result", {"data": f"Result =>  {state.sql_query}"})
        return {"sql_query":state.sql_query }
    def sql_search_node(self, state: GraphState) -> GraphState:
        dispatch_custom_event("sql_search_start", {"data": "Let's start the sql query search for the database."})
        results = mysql_db.query(state.sql_query)

        if isinstance(results, dict):
            print(f"--- SQL_SEARCH_NODE: WARNING - mysql_db.query returned a single dict. Wrapping in a list. ---")
            state.raw_data = [results]
        elif results is None:
            state.raw_data = []
        else: # Assuming it's already a list of dicts or an empty list
            state.raw_data = results
        dispatch_custom_event("sql_search_result", {"data": f"Result =>  {state.raw_data}"})
        return {"raw_data":state.raw_data}
    def vector_search_node(self, state: GraphState) -> GraphState:
        dispatch_custom_event("vector_search_start", {"data": "Let's start the vector search for the database."})
        results = vector_db.query(state.query)
        results = [result.model_dump() for result in results]

        if isinstance(results, dict):
            print(f"--- SQL_SEARCH_NODE: WARNING - mysql_db.query returned a single dict. Wrapping in a list. ---")
            state.raw_data = [results]
        elif results is None:
            state.raw_data = []
        else: # Assuming it's already a list of dicts or an empty list
            state.raw_data = results
        
        dispatch_custom_event("vector_search_result", {"data": f"Result =>  {state.raw_data}"})
        return {"raw_data":state.raw_data}
    
    def parallel_search_node(self, state: GraphState) -> GraphState:
        dispatch_custom_event("parallel_search_start", {"data": "Let's start the parallel search for sql and vectorDB."})
        return state


    def determine_feedback(self, state: GraphState) -> GraphState:
        print("determine_feedback")
        if state.requires_human_review == True:
            dispatch_custom_event("require_human_feedback_result", {"data": "Result =>  We need to use human feedback"})
            dispatch_custom_event("get_human_feedback", {"data": "Let's get human feedback"})
            return True
        else:
            dispatch_custom_event("require_human_feedback_result", {"data": "Result =>  We have enough information"})
            return False
    def data_retrieval_node(self, state: GraphState) -> GraphState:
        try:
            dispatch_custom_event("require_human_feedback", {"data": "Let's determine that we have enough information to generate the answer."})
            context = "\n\n".join(
                "\n".join([
                    f"{key.replace('_', ' ').title()}: {value}"
                    for key, value in cheese.items()
                    if value is not None
                ]) for cheese in state.raw_data
            )
            # print("context--------",context)
            print("query------", state.query)
            confidence_prompt = feedback_prompt.format(
                context=context, query=state.query
            )

            confidence_response = self.model.invoke(state.history+[HumanMessage(confidence_prompt)])
            confidence_content = json.loads(confidence_response.content)
            
            print(confidence_content)
            if confidence_content['confidence'] < 75:
                state.requires_human_review = True
                if confidence_content['feedbackQuestion']:
                    confidence_response = self.model.invoke(state.history+[HumanMessage(confidence_prompt)])
                state.hitl_feedback_message = confidence_content['feedbackQuestion']

                print(state.hitl_feedback_message)

        except Exception as e:
            state.history.append({
                "role": "assistant",
                "content": "I apologize, but I encountered an error while retrieving the information. Could you please rephrase your question?"
            })

        return {"history":[{"role": "assistant", "content": confidence_content['feedbackQuestion']}], "hitl_feedback_message":state.hitl_feedback_message, "requires_human_review":state.requires_human_review}    
    def generate_response(self, state: GraphState) -> GraphState:
        try:
            dispatch_custom_event("generate_response", {"data": "Let's generate the final response"})
            prompt = generate_response.format(
                context=state.raw_data, query=state.query
            )


            response = self.model.invoke(state.history + [HumanMessage(prompt)])
 
            state.messages = response.content


        except Exception as e:
            state.history.append({
                "role": "assistant",
                "content": "I apologize, but I encountered an error while retrieving the information. Could you please rephrase your question?"
            })

        return {"history":[{"role": "assistant", "content": response.content}], "messages":state.messages}
  
    def get_base_string(self, text):
        """
        Extract the base string from a text that consists of multiple repetitions.
        Works for any number of repetitions (2, 3, 4, etc.)
        """
        text_length = len(text)
        
        # Try different potential base string lengths
        for base_length in range(1, text_length // 2 + 1):
            # Extract potential base string
            base = text[:base_length]
            
            # Check if text is just repetitions of this base
            repetitions = text_length // base_length
            reconstructed = base * repetitions
            
            # Account for partial repetition at the end
            if text_length % base_length != 0:
                reconstructed += base[:text_length % base_length]
                
            # If we can reconstruct the original text with repetitions,
            # we found the base string
            if reconstructed == text:
                return base
        
        # If no repetition pattern is found, return the original text
        return text

  