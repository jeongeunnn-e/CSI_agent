import json
import datetime
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI


def _save_conversation_history(thoughts, conversation_history, res):
    output = {}
    serializable_history = [
        {
            "role": "system" if isinstance(msg, SystemMessage) else "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content
        }
        for msg in conversation_history
    ]
    output['conversation'] = serializable_history

    if res == -1:
        output['result'] = (-1, -1)
    else:
        output['result'] = (1, res)

    with open(f'example/conversation_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")}.json', "w") as file:
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

