import json
from core.prompt import *
from core.helpers import DialogSession
from colorama import Fore, Style, init
init(autoreset=True)

def react_based(backbone_model, task_prompt, state:DialogSession):
    
    obs = state[-1][2]
    print(f"Observation: {obs}")
    prompt = task_prompt + f"\nObservation {turn} : {obs}\nThought {turn}: "
    response = backbone_model.chat_generate([{'role':'system', 'content':'You are a helpful assistant.'},{'role': 'user', 'content': prompt}], **inference_args)
    response = response[0]['generated_text']
    
    try:
        thought, action = response.strip().split(f"Thought {turn}: ")[1].split(f"\nAction {turn}: ")
        print(f"Thought: {thought}")
        prompt += f"{thought}\nAction {turn}: {action}"
    except IndexError:
        thought, action = response.strip().split(f"\nAction {turn}: ")
        print(f"Thought: {thought}")
        prompt += f"{thought}\nAction {turn}: {action}"
    except:
        action = response 
        prompt += f"Action {turn}: {response}"

    print(f"Action: {action}")
    task_prompt = prompt
    turn += 1

    return action[action.find('[') + 1 : action.find(']', action.find('['))].strip() if '[' in action and ']' in action else action


def chat_based_question_generation(backbone_model, state:DialogSession, inference_args):

    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    
    message = [
        {'role':'system', 'content': chat_system_question_generation},
        {'role': 'user', 'content': chat_assistant_question_generation.format(dial=conversation_history)}
    ]

    response = backbone_model.chat_generate(message, **inference_args)[0]['generated_text']

    preference = chat_based_preference_elicitation(backbone_model, state, inference_args)

    return response, preference


def chat_based_preference_elicitation(backbone_model, state:DialogSession, inference_args):
    
        conversation_history = ""
        for (role, da, utt) in state:
            conversation_history += f"{role}: {utt}\n"
    
        message = [
            {'role':'system', 'content': chat_system_preference_elicitation},
            {'role': 'user', 'content': chat_assistant_preference_elicitation.format(dial=conversation_history)}
        ]
    
        response = backbone_model.chat_generate(message, **inference_args)[0]['generated_text']
    
        try:
            preference = response.split("The user is looking for ")[1].strip()
        except:
            preference = response

        print(f"{Fore.LIGHTBLUE_EX}Preference: {Style.RESET_ALL}{preference}\n")
        return preference


def chat_based_recommendation(backbone_model, state:DialogSession, inference_args, item, preference):

    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    
    message = [
        {'role':'system', 'content': chat_system_recommendation},
        {'role': 'user', 'content': chat_assistant_recommendation.format(item_request=preference, item_info=item.description)}
    ]

    response = backbone_model.chat_generate(message, **inference_args)[0]['generated_text']

    return response


def chat_based_persuasion(backbone_model, state:DialogSession, inference_args, item, preference, action):

    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    
    message = [
        {'role':'system', 'content': chat_system_persuasion},
        {'role': 'user', 'content': chat_assistant_persuasion.format(item_request=preference, item_info=item.description, action=action)}
    ]

    response = backbone_model.chat_generate(message, **inference_args)[0]['generated_text']

    return response


def chat_based_reward(backbone_model, state:DialogSession, item):

    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    
    message = [
        {'role':'system', 'content': "You are a helpful assistant."},
        {'role': 'user', 'content': chat_assistant_reward.format(item_name=item.name, dial=conversation_history)}
    ]

    response = backbone_model.chat_generate(message)
    response = response[0]['generated_text']

    return response

def chat_based_seeker(backbone_model, state:DialogSession, user_data):

    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    
    message = [
        {'role':'system', 'content': chat_system_seeker.format(user_personality=user_data.user_personality, user_decision_making_style=user_data.decision_making_style, target_needs=user_data.target_needs, user_profile=user_data.user_profile) },
        {'role': 'user', 'content': chat_assistant_seeker.format(dialogue_context=conversation_history)}
    ]

    response = backbone_model.chat_generate(message)
    response = response[0]['generated_text']

    if 'Seeker' in response:
        return response.split('Seeker: ')[1].strip()

    return response


def _conv_history_to_list(state):
    conversation_history = []
    for (role, da, utt) in state:
        conversation_history.append({"role": role, "content": utt})
    return conversation_history


def _conv_history_to_string(state):
    conversation_history = ""
    for (role, da, utt) in state:
        conversation_history += f"{role}: {utt}\n"
    return conversation_history


def _clear_chat_response(response):
    try:
        data_dict = json.loads(response)
    except json.JSONDecodeError as e:
        fixed_json_string = response.strip() + '}'
        try:
            data_dict = json.loads(fixed_json_string)
        except json.JSONDecodeError as e:
            return None
    return data_dict