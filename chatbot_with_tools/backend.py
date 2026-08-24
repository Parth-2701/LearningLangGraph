from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver #Learning purpose sql db memory
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition # We use a single ToolNode for our chatbot which contains all available tools. Also we dont need to write logic for when to call which tool, that is handled by tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool # Used to create custom tools 
import os
from dotenv import load_dotenv
import requests # We hit an api endpoint using this library
import sqlite3 #This is used to make sqlite databases in python
load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)
# Tools
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    stock_api = os.getenv('ALPHAVANTAGE_API_KEY')
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={stock_api}"
    r = requests.get(url)
    return r.json()

tools = [search_tool,calculator,get_stock_price]
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

# graph nodes
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)  # Executes tool calls

conn = sqlite3.connect(database='chatbot.db',check_same_thread=False) #By default, sqlite is used only in a single thread. We make it false to allow multiple threads to access it

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)

graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)


graph.add_edge(START, "chat_node")

# If the LLM asked for a tool, go to ToolNode; else finish
graph.add_conditional_edges("chat_node", tools_condition)

graph.add_edge("tools", "chat_node") 

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():

    all_threads = set()

    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)