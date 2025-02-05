import json
import datetime
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI
import os


def _save_conversation_history(sys, conversation_history, user_data, res):
    output = {}
    serializable_history = [
        {
            "role": "system" if isinstance(msg, SystemMessage) else "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content
        }
        for msg in conversation_history
    ]
    output['conversation'] = serializable_history

    thoughts = sys.thoughts
    output['thoughts'] = [ tmp['Thoughts'] for tmp in thoughts ]
    output['profile update'] = [ tmp['Profile'] for tmp in thoughts ]
    output['actions'] = [ tmp['Action'] for tmp in thoughts ]

    output['persuasion strategies'] = sys.persuasion_strategies
    output['result'] = (-1, -1) if res == -1 else (1, res)
    output['y'] = [sys.y[0].id, sys.y[1].id]
        
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(f'example/{current_date}'):
        os.makedirs(f'example/{current_date}')
    
    with open(f'example/{current_date}/{user_data.id}_{datetime.datetime.now().strftime("%H-%M-%S")}.json', "w") as file:
        json.dump(output, file, indent=4)

    return


def critic(conversation_history):

    model = ChatOpenAI(model="gpt-4o-mini")

    def _conv_history_to_string(conversation_history):
        serializable_history = [{"role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender", "content": msg.content} for msg in conversation_history]

        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp
    
    messages = [
        SystemMessage(content="Given conversation, extract the item ID that user finally agreed to purchase."),
        SystemMessage(content="Return only the extracted item ID.\nConversation History:\n{conversation_history}".format(conversation_history=_conv_history_to_string(conversation_history)))
    ]

    output = model.generate([messages])
    response = output.generations[0][0].text
    print("Final item ID: ", response)
    return response

