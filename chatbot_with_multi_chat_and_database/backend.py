from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver #Learning purpose sql db memory
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
import sqlite3 #This is used to make sqlite databases in python
load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # send to llm
    response = llm.invoke(messages)

    # response store state
    return {'messages': [response]}

conn = sqlite3.connect(database='chatbot.db',check_same_thread=False) #By default, sqlite is used only in a single thread. We make it false to allow multiple threads to access it

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():

    all_threads = set()

    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)