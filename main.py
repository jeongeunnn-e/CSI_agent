import torch
import json
import argparse
from tqdm import tqdm

from load_data import load_dataset
from core.players import *
from langchain.schema import HumanMessage, AIMessage, SystemMessage

torch.cuda.init() 
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)

def main(cmd_args, dataset):
	
	for data in dataset[:3]:
		user = Seeker(data)
		system = Recommender()

		conversation_history = [
			HumanMessage(content=user.init_utt),
		]
		
		for i in range(cmd_args.max_turn):
			_, action = system.plan(conversation_history)
			sys_utt = system.generate_utterance(action, conversation_history)
			conversation_history.append(AIMessage(content=sys_utt))
			
			usr_utt = user.generate_utterance(conversation_history)
			conversation_history.append(HumanMessage(content=usr_utt))
			
			print(f"System: {sys_utt}")
			print(f"User: {usr_utt}")
            
		_save_conversation_history(conversation_history)


def _save_conversation_history(conversation_history):
    serializable_history = [
        {
            "role": "system" if isinstance(msg, SystemMessage) else "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content
        }
        for msg in conversation_history
    ]

    with open(f'example/conversation_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")}.json', "w") as file:
        json.dump(serializable_history, file, indent=4)
		

if __name__ == "__main__":

	import json
	import datetime
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument('--seed', type=int, default=0, help='random seed')
	parser.add_argument('--max_steps', type=int, default=1, help='max training steps')
	parser.add_argument('--max_turn', type=int, default=10, help='max conversation turn')
	parser.add_argument('--sample_times', type=int, default=3, help='the epoch of sampling')
	parser.add_argument('--eval_num', type=int, default=1, help='the number of steps to evaluate RL model and metric')
	parser.add_argument('--save_num', type=int, default=1, help='the number of steps to save RL model and metric')
	parser.add_argument('--model_name', type=str, default='gpt-4o-mini', help='model name')

	cmd_args = parser.parse_args()
	cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

	dataset = load_dataset()
	cmd_args.sample_times = len(dataset)
	
	main(cmd_args, dataset)

