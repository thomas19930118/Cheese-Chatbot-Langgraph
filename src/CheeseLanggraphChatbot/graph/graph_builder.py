from langgraph.graph import StateGraph, START,END, MessagesState
from langgraph.prebuilt import tools_condition,ToolNode
from langchain_core.prompts import ChatPromptTemplate
from src.CheeseLanggraphChatbot.graph.graph_state import GraphState, DatabaseEnum
from src.CheeseLanggraphChatbot.nodes.basic_chatbot_node import BasicChatbotNode
from src.CheeseLanggraphChatbot.nodes.hitl_node import HITLNode
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

class GraphBuilder:

    def __init__(self,model):
        self.model=model
        self.graph_builder=StateGraph(GraphState)
        self.hitl_node = HITLNode()


    # def needs_human_feedback(self, state):
    #     """Route to human input if feedback is required"""
    #     return state.requires_human_review

    # def no_feedback_needed(self, state):
    #     """Route to response generation if no feedback is required"""
    #     return not state.requires_human_review
    
    def basic_chatbot_build_graph(self):
    # Existing nodes
        self.basic_chatbot_node = BasicChatbotNode(self.model)
        self.graph_builder.add_node("reasoning", self.basic_chatbot_node.reasoning_node)
        self.graph_builder.add_node("gen_sql_query", self.basic_chatbot_node.gen_sql_query_node)
        self.graph_builder.add_node("sql_search_node", self.basic_chatbot_node.sql_search_node)
        self.graph_builder.add_node("vector_search_node", self.basic_chatbot_node.vector_search_node)
        self.graph_builder.add_node("data_retrieval", self.basic_chatbot_node.data_retrieval_node)
        self.graph_builder.add_node("human_assistance", self.hitl_node.get_human_feedback)
        self.graph_builder.add_node("generate_response", self.basic_chatbot_node.generate_response)
        self.graph_builder.add_node("parallel_search", self.basic_chatbot_node.parallel_search_node)

        # Add conditional edges
        self.graph_builder.add_conditional_edges(
            "reasoning",
            self.basic_chatbot_node.determine_database,
            {
                DatabaseEnum.MYSQL: "gen_sql_query",
                DatabaseEnum.PARALLEL: "parallel_search",
                DatabaseEnum.VECTORDB: "vector_search_node",
                DatabaseEnum.NoDB:"generate_response"
            }
        )

        self.graph_builder.add_conditional_edges(
            "data_retrieval",
            self.basic_chatbot_node.determine_feedback,
            {
                True: "human_assistance",
                False: "generate_response"
            }
        )

        # Add edges
        self.graph_builder.add_edge("parallel_search", "gen_sql_query")
        self.graph_builder.add_edge("parallel_search", "vector_search_node")
        self.graph_builder.add_edge("gen_sql_query", "sql_search_node")
        self.graph_builder.add_edge("sql_search_node", "data_retrieval")
        self.graph_builder.add_edge("vector_search_node", "data_retrieval")
        self.graph_builder.add_edge("human_assistance", "reasoning")
        self.graph_builder.add_edge("generate_response", END)
        self.graph_builder.add_edge(START, "reasoning")    
    def setup_graph(self):
        """
        Sets up the graph for the selected use case.
        """
        self.basic_chatbot_build_graph()

        return self.graph_builder.compile(checkpointer=memory)
    




    

