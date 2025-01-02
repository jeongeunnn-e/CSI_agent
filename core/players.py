import os
import random
import logging
from typing import List, Tuple
from core.helpers import DialogSession
from core.gen_models import DialogModel
from core.game import CRS
from core.prompt import *
from core.generate import *
from core.item import *
from core.gen_models import OpenAIChatModel


logger = logging.getLogger(__name__)


class Recommender(DialogModel):

	def __init__(self, inference_args={}):
		super().__init__()
		
		self.mode = 'preference elicitation' # or 'persuasion'
		self.da_prompts_mapping = PersuasionAct
		self.dialog_acts = list(self.da_prompts_mapping.keys())
			
		self.backbone_model = OpenAIChatModel('gpt-4o-mini')
		self.max_hist_num_turns = 3
		self.inference_args = inference_args
		
		self.retriever = Retriever()
		return
	
	def reset(self):
		self.mode = 'preference elicitation'
	
	def change_mode(self):
		logger.info(f"Changing mode from Question Generation to Persuasion")
		if self.mode == 'persuasion':
			return 1
		
		self.mode = 'persuasion'
		self.item = self.retriever.retrieve(self.preference)
		logger.info("[INFO] Item selected: ", self.item.name)
		return 1
	
	def get_utterance(self, state:DialogSession, action) -> str:

		if len(state)==3:
			self.change_mode()
			next_utt = chat_based_recommendation(self.backbone_model, state, self.inference_args, self.item, self.preference)
			return next_utt
	
		if self.mode == 'preference elicitation':
			next_utt, self.preference = chat_based_question_generation(self.backbone_model, state, self.inference_args)
			return next_utt
		
		next_utt = chat_based_persuasion(self.backbone_model, state, self.inference_args, self.item, self.preference, self.da_prompts_mapping[action])
		return next_utt

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
	
	def _init_profile(self, profile):
		self.item_request = "Summer Shoes"
		self.budget = profile['budget']
		self.profile = profile['user_profile']
		self.user_profile = (self.item_request, self.budget, self.profile)

	def get_initial_utterance(self):
		init_utt = f"Hi, I'm looking for {self.item_request}."
		print("Seeker: ", init_utt)
		return init_utt
		

	def get_utterance(self, state:DialogSession, action=None) -> str:
		user_resp = chat_based_seeker(self.backbone_model, state, self.user_profile)
		return user_resp
	