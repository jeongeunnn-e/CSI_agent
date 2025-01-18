import torch
import argparse
from tqdm.auto import tqdm

from data import load_dataset
from core.players import *
from core.game import CRS
from core.planner import SystemPlanner


# export OPENAI_API_KEY=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

torch.cuda.init() 
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)

def main(args, dataset):

	sys = Recommender(
		inference_args={
			"temperature": 0.7,
			"return_full_text": False,
			"max_new_tokens": 128,
		}
	)

	usr = Seeker(
		inference_args={
			"max_new_tokens": 128,
			"temperature": 1.1,
			"repetition_penalty": 1.0,
			"return_full_text": False,
		},
	)

	game = CRS(sys, usr)
	planner = SystemPlanner(sys.dialog_acts).get_planner("ReAct")
	print(f"System dialog acts: {sys.dialog_acts}")

	sys.reset()
	planner.reset()
	state = DialogSession("Recommender", "Seeker")

	your_utt = input("You: ")
	while your_utt.strip() != "q":
		
		state.add_single("Seeker", None, your_utt)
		sys_da = planner.select_action(state)
		sys_utt = sys.get_utterance(state, sys_da)
		state.add_single("Recommender", sys_da, sys_utt)
		print(f"System: {sys_utt}")
		your_utt = input("You: ")

	return


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--seed', type=int, default=0, help='random seed')
	parser.add_argument('--max_steps', type=int, default=1, help='max training steps')
	parser.add_argument('--max_turn', type=int, default=10, help='max conversation turn')
	parser.add_argument('--sample_times', type=int, default=3, help='the epoch of sampling')
	parser.add_argument('--eval_num', type=int, default=1, help='the number of steps to evaluate RL model and metric')
	parser.add_argument('--save_num', type=int, default=1, help='the number of steps to save RL model and metric')

	parser.parse_args()
	cmd_args = parser.parse_args()
	cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

	dataset = load_dataset()
	cmd_args.sample_times = len(dataset)
	main(cmd_args, dataset)