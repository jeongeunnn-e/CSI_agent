from core.gen_models import DialogModel
from core.helpers import DialogSession
from core.gen_models import OpenAIChatModel
from core.generate import chat_based_reward
from colorama import Fore, Style, init

init(autoreset=True) 


class CRS(object):
	SYS = "Recommender"
	USR = "Seeker"

	def __init__(self, system_agent:DialogModel, user_agent:DialogModel, max_conv_turns=15):

		super().__init__()

		self.system_agent = system_agent
		self.user_agent = user_agent
		self.max_conv_turns = max_conv_turns
		self.backbone_model = OpenAIChatModel('gpt-4o-mini')

		return
	
	def init_dialog(self) -> DialogSession:  # [(sys_act, sys_utt, user_act, user_utt), ...]
		init_state = DialogSession(self.SYS, self.USR)
		init_state.add_single(self.USR, None, self.user_agent.get_initial_utterance())
		return init_state

	def step(self, state, sys, usr, sys_da):

		sys_utt = sys.get_utterance(state, sys_da)
		state.add_single(CRS.SYS, sys_da, sys_utt)

		usr_utt = usr.get_utterance(state)
		state.add_single(CRS.USR, None, usr_utt)

		print(Fore.YELLOW + "Recommender:" + Style.RESET_ALL + " " + Fore.GREEN + "[" + sys_da + "]" + Style.RESET_ALL + " " + sys_utt)
		print(Fore.MAGENTA + "Seeker:" + Style.RESET_ALL + " " + usr_utt + "\n")

		reward, done = self._get_reward(state, sys)
		return state, reward, done

	def _get_reward(self, state, sys):

		if sys.mode == 'preference elicitation':
			return 0, False

		response = chat_based_reward(self.backbone_model, state, sys.item)

		if state[-1][0] == CRS.USR and "#STOP#" in state[-1][2]:
			return -1, True

		mapping = {
			"reject": (-1, False),
			"neutral": (0, False),
			"positive": (0.5, False),
			"negative": (-0.5, False),
		}

		response = response.lower()
		for key, value in mapping.items():
			if key in response:
				return value
		return 1, True
	
