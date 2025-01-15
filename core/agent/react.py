import save
import json
from core.agent.react_prompt import *
from core.gen_models import OpenAIChatModel


class ReactPlanner(object):

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
        self.reflections = []

    def reset(self):
        self.thoughts = []
        self.actions = []
        self.reflections = []
        
    def select_action(self, state):
        context = self._history_to_context(state)

        self.reflect(context)

        message = [
            {'role':'system', 'content': react_system},
            {'role': 'assistant', 'content': react_user.format(context=context)}
        ]

        response = self.backbone_model.chat_generate(message, **self.inference_args)
        thought, action = self._process_thought_action(response)

        self.thoughts.append(thought)
        self.actions.append(action)

        save.write("react", (f" Thought {len(self.thoughts)} ", thought))
        save.write("react", (f" Action {len(self.actions)} ", action))

        return action
    
    def reflect(self, context):
        message = [
            {'role': 'user', 'content': REFLECT_INSTRUCTION.format(context=context)}
        ]

        response = self.backbone_model.chat_generate(message, **self.inference_args)
        print("Reflexion ", response[0]['generated_text'])
        self.reflections.append(response[0]['generated_text'])
        
    
    def _history_to_context(self, state):
        context = ""
        for i, (role, da, utt) in enumerate(state):

            if i == 0:
                context += "[ Observation {} ]\n".format(i//2+1)

            if i%2==1:
                context += "[ Observation {} ]\n".format(i//2+2)

            context += f"{role}: {utt}\n"

            if i > 0 and i % 2 == 0:
                context += f"\n[ Reflexion {i//2+1} ] {self.reflections[i//2-1]}\n" 
                context += f"\n[ Thought {i//2+1} ] {self.thoughts[i//2-1]}\n" 
                context += f"[ Action {i//2+1} ] {self.actions[i//2-1]}\n\n" 

        return context
    

    def _process_thought_action(self, response):
        
        try:
            response = json.loads(response[0]['generated_text'])
            thought = response['Thought']
            action = response['Action']
            if isinstance(action, int):
                action = act[action-1]
            if isinstance(action, list):
                action = action[0]
        except:
            response = response[0]['generated_text']
            thought = response
            action = 'Recommendation'
            for possible_action in act:
                if possible_action in response:
                    action = possible_action
                    break

        return thought, action
    
