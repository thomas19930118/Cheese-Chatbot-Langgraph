import streamlit as st
import json
from src.CheeseLanggraphChatbot.ui.streamlitui.loadui import LoadStreamlitUI
from src.CheeseLanggraphChatbot.model.model import OpenAiModel
from src.CheeseLanggraphChatbot.graph.graph_builder import GraphBuilder
from src.CheeseLanggraphChatbot.ui.streamlitui.display_result import DisplayResultStreamlit

# MAIN Function START
def show_langgraph_diagram():
    st.sidebar.subheader("LangGraph Diagram")
    st.sidebar.graphviz_chart('''
digraph LangGraph {

    START -> reasoning

    // Conditional edges from reasoning
    reasoning -> gen_sql_query [label="if MYSQL"]
    reasoning -> parallel_search [label="if PARALLEL"]
    reasoning -> vector_search_node [label="if VECTORDB"]
    reasoning -> generate_response [label="if NoDB"]

    // Parallel search expands to both SQL and vector search
    parallel_search -> gen_sql_query
    parallel_search -> vector_search_node

    // SQL branch
    gen_sql_query -> sql_search_node
    sql_search_node -> require_human_feedback

    // Vector search branch
    vector_search_node -> require_human_feedback

    // Feedback handling
    require_human_feedback -> human_assistance [label="if True"]
    require_human_feedback -> generate_response [label="if False"]

    human_assistance -> reasoning

    generate_response -> END

    // Node styles
    START [shape=oval, style=filled, color=lightgray]
    END [shape=oval, style=filled, color=lightgray]
    reasoning [shape=box, style=filled, color=lightblue]
    gen_sql_query [shape=box, style=filled, color=lightblue]
    sql_search_node [shape=box, style=filled, color=lightblue]
    vector_search_node [shape=box, style=filled, color=lightblue]
    parallel_search [shape=box, style=filled, color=lightpink]
    require_human_feedback [shape=box, style=filled, color=lightblue]
    human_assistance [shape=box, style=filled, color=lightgreen]
    generate_response [shape=box, style=filled, color=lightblue]
}
''')
def load_langgraph_cheese_app():
    """
    Loads and runs the LangGraph AgenticAI application with Streamlit UI.
    This function initializes the UI, handles user input, configures the LLM model,
    sets up the graph based on the selected use case, and displays the output while 
    implementing exception handling for robustness.
    """
   
    # Load UI
    ui = LoadStreamlitUI()
    user_input = ui.load_streamlit_ui()
    show_langgraph_diagram()

    if not user_input:
        st.error("Error: Failed to load user input from the UI.")
        return
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        st.session_state.chat_history.append(
            {"role": "assistant", "content": "Hello! I’m here to help with all your cheese-related questions. Whether you need info on types of cheese, pairing suggestions, recipes, or storage tips, I’m ready to assist you. Ask away!"}
        )

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Text input for user message
    if st.session_state.IsFetchButtonClicked:
        user_message = st.session_state.timeframe 
    else :
        user_message = st.chat_input("Enter your message:")

    if user_message:
        try:
            # Configure LLM
            obj_model_config = OpenAiModel(user_controls_input=user_input)
            model = obj_model_config.get_model()
            
            if not model:
                st.error("Error: OpenAI model could not be initialized.")
                return

        # Initialize and set up the graph based on use case

        ### Graph Builder
            graph_builder=GraphBuilder(model)

            try:
                graph = graph_builder.setup_graph()
                print(user_input['show_reasoning'])
                DisplayResultStreamlit(graph,user_message, user_input['show_reasoning']).display_result_on_ui()
            except Exception as e:
                st.error(f"Error: Graph setup failed - {e}")
                print(e)
                return
            

        except Exception as e:
                raise ValueError(f"Error Occurred with Exception : {e}")