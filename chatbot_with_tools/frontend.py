import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

#-------------------------------------UTILITY FUNCTIONS--------------------------------------------

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(thread_id)

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    config = {
        'configurable': {
            'thread_id': thread_id
        }
    }

    state = chatbot.get_state(config)

    return state.values.get('messages', [])
#-------------------------------------SESSION SETUP------------------------------------------------

# We use session state, which is a built in streamlit dictionary type which resets only when pages is refreshed and not when enter is pressed
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads']=retrieve_all_threads()

add_thread(st.session_state['thread_id'])
CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']},
        'metadata':{'thread_id':st.session_state['thread_id']},
        'run_name':'chat_turn'}
#-------------------------------------SIDEBAR UI----------------------------------------------------

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages = load_conversation(thread_id)

        temp_messages=[]

        for message in messages:
            if isinstance(message,HumanMessage):
                role='user'
            else:
                role='assisstant'
            temp_messages.append({'role':role,'content':message.content})

        st.session_state['message_history'] = temp_messages


#-------------------------------------MAIN UI-------------------------------------------------------------

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
    # Below commented code lines are for without streaming effect
    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]},config = CONFIG)
    # st.session_state['message_history'].append({'role':'assistant','content':response['messages'][-1].content})
    # Assistant streaming block
    with st.chat_message("assistant"):

        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():

            for message_chunk, metadata in chatbot.stream(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
                config=CONFIG,
                stream_mode="messages",
            ):

                # Lazily create & update the SAME status container
                # when any tool runs
                if isinstance(message_chunk, ToolMessage):

                    tool_name = getattr(
                        message_chunk,
                        "name",
                        "tool"
                    )

                    if status_holder["box"] is None:

                        status_holder["box"] = st.status(
                            f"🛠 Using `{tool_name}` ...",
                            expanded=True
                        )

                    else:

                        status_holder["box"].update(
                            label=f"🛠 Using `{tool_name}` ...",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content


        ai_message = st.write_stream(ai_only_stream())
        st.session_state['message_history'].append({'role':'assistant','content':ai_message})
