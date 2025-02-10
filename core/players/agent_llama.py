import json
import torch
from core.prompt import *
from core.players.tools.retriever import Retriever
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import transformers


class Profile:
    def __init__(self):
        self.preference = None
        self.personality = None
        self.category = None
        self.category_path = ['Clothing Shoes & Jewelry']
        self.item_id = None

    def update(self, thought):
        self.preference = thought['Preference']
        self.personality = thought['Personality']
        self.price_range = thought['Expected Price Range']
        self.category_path = thought['Category Path']
        self.item_id = thought['Selected Item ID']
        return self

    def _save_format(self):
        return {
            'Preference': self.preference,
            'Personality': self.personality,
            'Category': self.category,
            'Category Path': self.category_path
        }

    def _string_format(self):
        return f"Preference: {self.preference}\nPersonality: {self.personality}\nCategory Path: {self.category_path}"


class RecommenderLLama:
    def __init__(self, tool, model_name):
        if 'llama'in model_name:
            model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
        else:
            model_id="mistralai/Mistral-7B-Instruct-v0.3"

        self.pipeline = transformers.pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device_map="auto",
        )

        self.terminators = [
            self.pipeline.tokenizer.eos_token_id,
            self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        self.tool = tool
        self.reconstructed_profile = Profile()
        self.selected = []
        self.candidates = []
        self.thoughts = []
        self.persuasion_strategies = []

    def plan(self, conversation_history):

        messages = [
            {"role": "system", "content": react_system.format(conversation_history=conversation_history,
                                                              user_profile=self.reconstructed_profile._string_format()) + "Return JSON only."}
        ]

        response = self.generate(messages)
        
        try:
            response = json.loads(response)
        except:
            return "", "Persuasion"

        thought = response['Thoughts']
        user_profile = response['Profile']
        action = response['Action']

        self.thoughts.append(response)

        user_profile['Category Path'] = self.tool.category_update(user_profile['Category Path'], self.reconstructed_profile.category_path)
        print("Updated category path: ", user_profile['Category Path'])
        self.reconstructed_profile.update(user_profile)

        if 'Selected Item ID' in user_profile and user_profile['Selected Item ID'] is not None:
            if user_profile['Selected Item ID'] not in ['null', '']:
                item = user_profile['Selected Item ID'].split(", ")[0].split("; ")[0]
                print("selected item: ", item)
                self.selected.append(self.tool.retriever.retrieve_by_id(item))

        return thought, action 


    def generate_utterance(self, action, conversation_history):

        if action in ['Category Search']:

            messages = [
                {"role": "system", "content": chat_system_category_search.format(preference=self.reconstructed_profile.preference,
                                                                            category_list=self.tool.category_search(self.reconstructed_profile.category_path)) + "Return a question only."}
            ]

            response = self.generate(messages, False)
            try:
                response = "Which category path " + response.split("Which category path ")[1]
            except:
                pass
            return response

        elif action in ['Preference Probing']:

            messages = [
                {"role": "system", "content": chat_system_question_generation.format(conversation_history=conversation_history,
                                                                                     user_preference=self.reconstructed_profile.preference) + "Return a question only."}
            ]
            
            response = self.generate(messages, False)
            try:
                response = "What do you prefer " + response.split("What do you prefer ")[1]
            except:
                pass
            return response

        elif action in ['Suggestion']:
            if isinstance(self.reconstructed_profile.preference, dict):
                self.reconstructed_profile.preference = " ".join(list(self.reconstructed_profile.preference.values()))
            if isinstance(self.reconstructed_profile.preference, list):
                self.reconstructed_profile.preference = " ".join(self.reconstructed_profile.preference)
            _, items = self.tool.retriever.retrieve(self.reconstructed_profile.preference, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path, self.tool.category_tree)
            # self.y[0] = items[0]
            items_info = [item.short_description for item in items]

            utt = "Here are some items that you might like: \n"
            for i, item in enumerate(items_info):
                utt += f"{i + 1}. {item}\n"

            return utt
        elif action in ['Persuasion']:
            try:
                candidates = self.tool.retriever.select_candidate(self.reconstructed_profile.item_id, self.reconstructed_profile.price_range, self.reconstructed_profile.category_path, self.tool.category_tree)
                print("\033[1;33mCandidate: \033[0m", candidates[0].id)
                self.candidates.append(candidates[0])

                messages = [
                    {"role": "system", "content": chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=self.candidates[0].description)},
                ]

            except Exception as e:
                print(e)
                print('No candidate exists')

                messages = [
                    {"role": "system", "content": chat_system_persuasion.format(conversation_history=conversation_history,
                                                                        item_request=self.reconstructed_profile.preference,
                                                                        user_personality=self.reconstructed_profile.personality,
                                                                        item1=self.selected[0].description,
                                                                        item2=None)},
                ]

            response = self.generate(messages)
            print(response, "\n")
            try:
                response = json.loads(response)
                self.persuasion_strategies.append(response['strategy'])
                return response['sentence']
            except:
                return response

    def generate(self, messages, return_json=True):

        outputs = self.pipeline(
            messages,
            max_new_tokens=256,
            eos_token_id=self.terminators,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )

        output =  outputs[0]["generated_text"][-1]['content']
        if not return_json:
            return output    
        response = output[output.index('{'):]
        try:            
            response = response[:response.rindex('}')+1]
        except:
            pass
        response = response.strip("'```json").strip("```'").replace("{{", "{").replace("}}", "}").replace("None", "null")# .replace("'", "\"")
        return response


    def _conv_history_to_string(self, conversation_history):
        serializable_history = [{"role": "system" if isinstance(msg, SystemMessage) else "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content} for msg in conversation_history]

        resp = "\n".join([f"{msg['role']}: {msg['content']}" for msg in serializable_history])
        return resp

    def _conv_history_to_json(self, conversation_history):
        serializable_history = [{"role": "System" if isinstance(msg, SystemMessage) else "Seeker" if isinstance(msg, HumanMessage) else "Recommender", "content": msg.content} for msg in conversation_history]
        return serializable_history 