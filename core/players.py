import os
import save
import logging
from typing import List, Tuple
from core.helpers import DialogSession
from core.gen_models import DialogModel
from core.game import CRS
from core.prompt import *
from core.generate import *
from core.retrieve import *
from core.gen_models import OpenAIChatModel
from colorama import Fore, Back, Style, init

init(autoreset=True) 

logger = logging.getLogger(__name__)


class Recommender(DialogModel):

	def __init__(self, inference_args={}):
		super().__init__()
		
		self.mode = 'preference elicitation' # or 'persuasion'
		self.da_prompts_mapping = UnifiedAct
		self.dialog_acts = list(self.da_prompts_mapping.keys())
			
		self.backbone_model = OpenAIChatModel('gpt-4o-mini')
		self.max_hist_num_turns = 3
		self.inference_args = inference_args
		self.recommendation = None
		self.retriever = Retriever()
		return
	
	def reset(self):
		self.mode = 'preference elicitation'
	
	def change_mode(self):
		print(Back.LIGHTBLACK_EX + "Changing mode from Question Generation to Persuasion")
		if self.mode == 'persuasion':
			return 1
		
		self.mode = 'persuasion'
		self.recommendation = self.retriever.retrieve(self.preference)
		print("[INFO] Item selected: " + self.recommendation.name + "\n")
		return 1
	
	def get_utterance(self, state:DialogSession, action) -> str:
		
		if action.lower() in [ 'contextual probing', 'preference narrowing']:
			next_utt = chat_based_question_generation(self.backbone_model, state, self.inference_args)
			return None, next_utt
		
		if action.lower() in ['recommendation']:
			top_k_items_id = self._get_recommendation(state)
			next_utt = chat_based_recommendation(self.backbone_model, state, self.inference_args, self.recommendation, self.search_qeury)
			return top_k_items_id, next_utt

		if self.recommendation is None:
			top_k_items_id = self._get_recommendation(state)
		next_utt = chat_based_persuasion(self.backbone_model, state, self.inference_args, self.recommendation, self.search_qeury, self.da_prompts_mapping[action])
		return top_k_items_id, next_utt

	def _get_recommendation(self, state: DialogSession):
		self.search_qeury = chat_based_query_generation(self.backbone_model, state, self.inference_args)
		save.write("query", self.search_qeury)
		self.recommendation, top_k_items_id = self.retriever.retrieve(self.search_qeury)
		save.write("recommendation", str(self.recommendation.name))
		return top_k_items_id

	def __process_chat_exp(self, exp: DialogSession, max_hist_num_turns: int = -1):
		if not exp:
			return []

		# Ensure the session starts with the system
		assert exp[0][0] == CRS.SYS

		num_turns_to_truncate = max(0, len(exp) // 2 - max_hist_num_turns) if max_hist_num_turns > 0 else 0
		prompt_messages = [
			{
				"role": "assistant" if role == CRS.SYS else "user",
				"content": f"{role}: {utt}".strip()
			}
			for i, (role, da, utt) in enumerate(exp)
			if (i // 2) >= num_turns_to_truncate
		]

		return prompt_messages
	

	
class Seeker(DialogModel):

	def __init__(self, inference_args={}):
		super().__init__()
		self.backbone_model = OpenAIChatModel('gpt-4o-mini')
		self.max_hist_num_turns = 3
		self.inference_args = inference_args
		return
	
	def _init_profile(self, user_data):
		self.item_request = "Amazon Fashion" # user_data.target_category
		self.user_data = user_data

	def get_initial_utterance(self):
		init_utt = f"Hi, I'm looking for {self.item_request}."
		save.write("usr", init_utt)
		return init_utt
		
	def get_utterance(self, state:DialogSession, action=None) -> str:
		user_resp = chat_based_seeker(self.backbone_model, state, self.user_data)
		return user_resp
	
