import logging
import numpy as np
from enum import Enum
from typing import List, Tuple
from core.helpers import DialogSession
from core.gen_models import GenerationModel, DialogModel
from core.game import CRS
from abc import ABC, abstractmethod
from collections import Counter
from core.agent.ppdpp import PPDPP
from core.agent.config import get_config
# from core.agent.mcts_base import MCTSPlanner

logger = logging.getLogger(__name__)

class AgentType(Enum):
    RELEXION = 'reflexion'
    PPDPP = 'ppdpp'
    MCTS = 'mcts'


class DialogPlanner(ABC):
	@abstractmethod
	def get_valid_moves(self, state):
		# 1 if the i-th dialog act is valid, 0 otherwise
		pass

	@abstractmethod
	def predict(self, state) -> "Tuple[np.ndarray, float]":
		# returns a prob and value
		pass


class SystemPlanner(object):
	def __init__(self, dialog_acts):
		
		super().__init__()
		self.dialog_acts = dialog_acts
		# self.max_hist_num_turns = max_hist_num_turns
		# self.user_dialog_acts = user_dialog_acts
		# self.user_max_hist_num_turns = user_max_hist_num_turns
		# self.generation_model = generation_model
		self.smoothing = 1.0
		

	def get_planner(self, agent_type, game=None):
		if agent_type == "PPDPP":
			return PPDPP(
				act=self.dialog_acts,
				args=get_config("PPDPP")
			)
		if agent_type == "MCTS":
			return MCTSPlanner(
				game=game,
				act=self.dialog_acts,
				args=get_config("MCTS"),
			)
		return self.planner

