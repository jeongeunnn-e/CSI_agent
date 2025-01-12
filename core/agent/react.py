import save
import json
from core.agent.react_prompt import *
from core.gen_models import OpenAIChatModel
from colorama import Fore, Back, Style, init


class ReActPlanner(object):

    def __init__(self):
        super().__init__()
        self.backbone_model = OpenAIChatModel('gpt-4o-mini')
        self.inference_args = {
            "temperature": 0.7,
            "return_full_text": False,
            "max_new_tokens": 128,
        }
        self.thoughts = []
        self.actions = []

    def reset(self):
        self.thoughts = []
        self.actions = []
        
    def select_action(self, state):
        context = self._history_to_context(state)

        message = [
            {'role':'system', 'content': react_system},
            {'role': 'user', 'content': react_user.format(context=context)}
        ]

        response = self.backbone_model.chat_generate(message, **self.inference_args)
        try:
            response = json.loads(response[0]['generated_text'])
            thought = response['Thought']
            action = response['Action']
        except:
            response = response[0]['generated_text']
            thought = response
            action = 'Recommendation'
            for possible_action in act:
                if possible_action in response:
                    action = possible_action
                    break

        self.thoughts.append(thought)
        self.actions.append(action)

        save.write("react", (f" Thought {len(self.thoughts)} ", thought))
        save.write("react", (f" Action {len(self.actions)} ", action))

        return action
    
    
    def _history_to_context(self, state):
        context = ""
        for i, (role, da, utt) in enumerate(state):

            if i == 0:
                context += "[ Observation {} ]\n".format(i//2+1)

            if i%2==1:
                context += "[ Observation {} ]\n".format(i//2+2)

            context += f"{role}: {utt}\n"

            if i > 0 and i % 2 == 0:
                context += f"\n[ Thought {i//2+1} ] {self.thoughts[i//2-1]}\n" 
                context += f"[ Action {i//2+1} ] {self.actions[i//2-1]}\n\n" 


        # context += "Thought {} :\n".format(len(thought_and_action) + 1)
        # context += "Action {} :\n".format(len(thought_and_action) + 1)
        return context
    