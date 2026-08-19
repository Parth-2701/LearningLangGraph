import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

CONFIG = {'configurable':{'thread_id':'thread_1'}}
# We use session state, which is a built in streamlit dictionary type which resets only when pages is refreshed and not when enter is pressed
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
# We reload conversation history, since each time we press enter, the whole script re runs from top to bottom
# making previous messages disappear
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# {'role':'user','content':''}
# {'role':'assisstant','content':''}
user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]},config = CONFIG)
    st.session_state['message_history'].append({'role':'assistant','content':response['messages'][-1].content})
    with st.chat_message('assisstant'):
        st.text(response['messages'][-1].content)
