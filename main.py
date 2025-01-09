import torch
import random
import logging
import argparse
from tqdm.auto import tqdm

from data import load_dataset
from core.players import *
from core.game import CRS
from core.planner import SystemPlanner


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
	planner = SystemPlanner(sys.dialog_acts).get_planner("PPDPP")
	print(f"System dialog acts: {sys.dialog_acts}")
	
	for i in range(1, args.max_steps+1):

		SR, AvgT, total_reward = 0, 0, 0
		loss = torch.tensor(0, dtype=torch.float, device=args.device)

		for i_episode in tqdm(range(args.sample_times),desc='sampling'):
			
			data = random.choice(dataset)

			print(f"Case {i_episode+1} : {data.id}")
			usr._init_profile(data)
			sys.reset()
			state = game.init_dialog()
			epi_reward, done, sys_da, mode = 0, False, "Elicitation", 0

			for t in range(10):

				if sys.mode == 'persuasion' :
					sys_da = planner.select_action(state)

				state, reward, done = game.step(state , sys, usr, sys_da)

				if sys.mode == 'persuasion' :
					epi_reward += reward
					reward = torch.tensor([reward], device=args.device, dtype=torch.float)
					planner.rewards.append(reward)

					print(f"Reward: {reward.item()}\n")
				
				if done:
					if done == 1:
						SR += 1
					AvgT += t+1
					total_reward += epi_reward
					break
			
			try:
				newloss = planner.optimize_model()
				if newloss is not None:
					loss += newloss
			except Exception as e:
				pass
		
		print('loss : {} in epoch_uesr {}'.format(loss.item()/args.sample_times, args.sample_times))
		print('SR:{}, AvgT:{}, rewards:{} Total epoch_uesr:{}'.format(SR / args.sample_times,
					AvgT / args.sample_times, total_reward / args.sample_times, args.sample_times))

	return


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--seed', type=int, default=0, help='random seed')
	parser.add_argument('--max_steps', type=int, default=1, help='max training steps')
	parser.add_argument('--max_turn', type=int, default=8, help='max conversation turn')
	parser.add_argument('--sample_times', type=int, default=5, help='the epoch of sampling')
	parser.add_argument('--eval_num', type=int, default=1, help='the number of steps to evaluate RL model and metric')
	parser.add_argument('--save_num', type=int, default=1, help='the number of steps to save RL model and metric')

	parser.parse_args()
	cmd_args = parser.parse_args()
	cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

	dataset = load_dataset()
	main(cmd_args, dataset)