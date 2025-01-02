import logging
import numpy as np
from tqdm.auto import tqdm
from .mcts import OpenLoopMCTS
from core.game import CRS
from core.helpers import DialogSession
from core.gen_models import OpenAIChatModel

logger = logging.getLogger(__name__)

class MCTSPlanner(object):
	def __init__(self, game, act, args):
		super().__init__()
		self.args = args
		self.dialog_acts = act
		self.mcts = OpenLoopMCTS(
			game=game,
			player=self,
			configs=self.args
		)
		
		self.generation_model = OpenAIChatModel('gpt-4o-mini')

	def select_action(self,state):
		for i in tqdm(range(self.args.num_mcts_sims)):
			self.mcts.search(state)

		mcts_policy = self.mcts.get_action_prob(state)
		mcts_policy_next_da = self.dialog_acts[np.argmax(mcts_policy)]

		utt = self.mcts.get_best_realization(state, np.argmax(mcts_policy))
		
		print(f"mcts_policy_next_da: {mcts_policy_next_da}")
		print(f"utt: {utt}")
		
		return mcts_policy_next_da
	

	def get_valid_moves(self, state):
		turn = len(state)
		if turn < 1:
			return np.array([1 if da == CRS.S_Greeting else 0 for da in self.dialog_acts])
		return np.array([1 for _ in self.dialog_acts])
	
	
	def predict(self, state:DialogSession):
		messages = [
			{'role': 'system', 'content': self.task_prompt},
			*self.prompt_examples,
			{'role': 'system', 'content': self.new_task_prompt}
		]
		if len(state) == 0:
			messages.append({'role': 'user', 'content': f'{CRS.USR}: Hello.'})
		else:
			assert(state[-1][0] == CRS.USR)
			messages += self.__proccess_chat_exp(state, keep_sys_da=True, keep_user_da=False)
		# produce a response
		data = self.generation_model.chat_generate(messages, **self.inf_args)

		sampled_das = self._get_generated_da(data)
		logger.debug(f"sampled das: {sampled_das}")
		# convert to prob distribution
		prob = np.zeros(len(self.dialog_acts))
		prob += self.smoothing
		for da in sampled_das:
			prob[self.dialog_acts.index(da)] += 1
		prob /= prob.sum()
		v = self.heuristic(state)
		return prob, v

	def heuristic(self, state:DialogSession) -> float:

		assert(state[-1][0] == CRS.USR)
		
		user_task_prompt = f"""
		You are a Seeker. A Recommender is trying to persuade you to buy the suggested item.
		You can choose amongst the following actions during a conversation to respond to the Recommender:
		{" ".join([f"[{da}]" for da in self.user_dialog_acts])}
		The following is a new conversation between a Recommender and a Seeker (you).
		""".replace("\t", "").strip()
		user_new_task_prompt = "The following is a new conversation between a Persuader and a Persuadee (you)."

		messages = [
			{'role': 'system', 'content': user_task_prompt},
			*self.process_chat_exp(new_task_prompt=user_new_task_prompt, assistant_role=CRS.USR, keep_sys_da=False, keep_user_da=True),
			{'role': 'system', 'content': user_new_task_prompt}
		]
		messages += self.__proccess_chat_exp(state, assistant_role=CRS.USR, keep_sys_da=False, keep_user_da=True)
		messages.append({
			'role': 'user', 'content': f'{CRS.SYS}: Would you be interested in donating to Save the Children?'
		})

		inf_args = {
			"max_new_tokens": 12,
			"temperature": 1.1,
			"return_full_text": False,
			"do_sample": True,
			"num_return_sequences": 10,
		}
		data = self.generation_model.chat_generate(messages, **inf_args)
		sampled_das = self._get_user_generated_da(data)

		logger.debug(f"persuadee prompt: {messages}")
		logger.debug(f"sampled das: {sampled_das}")

		# heuristic score
		score = []
		for da in sampled_das:
			if da == CRS.U_NoDonation:
				score.append(-1.0)
			elif da == CRS.U_NegativeReaction:
				score.append(-0.5)
			elif da == CRS.U_Neutral:
				score.append(0.0)
			elif da == CRS.U_PositiveReaction:
				score.append(0.5)
			elif da == CRS.U_Donate:
				score.append(1.0)
		v = 0.0 if len(score) == 0 else np.mean(score)
		logger.debug(f"sampled das to v: {v}")
		return float(v)