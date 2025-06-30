import streamlit as st
import torch
from core.players import *
from core.players.tool import Tool
from langchain.schema import HumanMessage, AIMessage
from utils import critic
from utils import _get_conversation_history

# Set up device
if torch.cuda.is_available():
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats(device=None)
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

def get_system(domain, file_name, rec_model):
    tool = Tool(domain, file_name)
    # You may want to customize agent selection logic here
    class Args:
        pass
    args = Args()
    args.device = device
    args.domain = domain
    args.file_name = file_name
    args.rec_model = rec_model
    return get_agent(args)(tool, rec_model)

def save_output(output):
    import json
    import datetime

    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"chat_demo_output/{current_date}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)
    return


# Streamlit UI
st.set_page_config(page_title="CSI Chat Demo", page_icon="🤖")
st.title("🤖 CSI Chat Demo")

# Sidebar for settings
domain = st.sidebar.selectbox('Domain', ['clothing', 'electronics'])
rec_model = st.sidebar.text_input('Rec model', 'gpt-4o-mini')

# Session state for system and conversation
def init_session():
    file_name = f'data/{domain}/css_data.json'
    st.session_state['system'] = get_system(domain, file_name, rec_model)
    st.session_state['conversation_history'] = []
    st.session_state['stopped'] = False
    st.session_state['SR'] = 0
    st.session_state['AT'] = 0
    st.session_state['SWR'] = 0
    st.session_state['res'] = -1

if 'system' not in st.session_state:
    init_session()

if st.sidebar.button('Reset Conversation'):
    init_session()
    st.rerun()

conversation_history = st.session_state['conversation_history']
system = st.session_state['system']
stopped = st.session_state.get('stopped', False)

# Chat display
for msg in conversation_history:
    if isinstance(msg, HumanMessage):
        st.chat_message('user').write(msg.content)
    elif isinstance(msg, AIMessage):
        st.chat_message('assistant').write(msg.content)

if not stopped:
    user_input = st.chat_input('Type your message...')
    if user_input:
        conversation_history.append(HumanMessage(content=user_input))
        if "#STOP#" in user_input:
            st.session_state['stopped'] = True
            st.success("Conversation stopped.")
            final_item_id = critic(conversation_history)
            st.info(final_item_id)
            if system.selected[0].id == final_item_id:
                st.info("Accepted in-budget item")
                st.session_state['res'] = 0
                st.session_state['SR'] += 1
                st.session_state['AT'] += len(conversation_history) // 2  # Each turn is 2 messages
            elif final_item_id in [candidate.id for candidate in system.candidates]:
                st.info("Accepted out-of-budget item")
                st.session_state['res'] = 1
                st.session_state['SWR'] += 1
                st.session_state['AT'] += len(conversation_history) // 2
            output = _get_conversation_history(
                system,
                conversation_history,
                st.session_state['res'],
                st.session_state['SR'],
                st.session_state['AT'],
                st.session_state['SWR'],
                None
            )
            save_output(output)
        else:
            st.session_state['pending_agent'] = True
            st.rerun()

# pending_agent가 True면 agent 답변 생성
if st.session_state.get('pending_agent', False):
    with st.spinner("Loading..."):
        thought, action = system.plan(conversation_history)
        sys_utt = system.generate_utterance(action, conversation_history).replace('"', '')
        conversation_history.append(AIMessage(content=sys_utt))
        st.session_state['pending_agent'] = False
        st.rerun() 