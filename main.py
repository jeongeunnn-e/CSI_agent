import torch
import debug
import argparse
from tqdm import tqdm

from load_data import load_dataset
from core.players import *
from core.players.tool import Tool
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from utils import _save_conversation_history, critic


torch.cuda.init()
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)


def main(cmd_args, dataset):
    tool = Tool()
    
    SR, AT, SWR = 0, 0, 0

    for data_idx in tqdm(range(10)):

        data = dataset[data_idx]

        user = Seeker(data, cmd_args.user_model)
        system = Recommender(tool, cmd_args.rec_model)
        conversation_history = [
            HumanMessage(content=user.init_utt),
        ]

        print(f"\033[1;34m User: {user.init_utt}\033[0m\n")

        action = None
        res = -1

        for i in range(cmd_args.max_turn):

            thought, action = system.plan(conversation_history)
            sys_utt = system.generate_utterance(action, conversation_history)
            conversation_history.append(AIMessage(content=sys_utt))

            usr_utt = user.generate_utterance(conversation_history)
            conversation_history.append(HumanMessage(content=usr_utt))

            print(f"\033[1;34mSystem: {sys_utt}\033[0m\n")
            print(f"\033[1;32mUser: {usr_utt}\033[0m\n")

            if "#STOP#" in usr_utt:

                print("Conversation is stopped.")
                SR += 1
                AT += i+1
                
                print(system.y[0].id, system.y[1].id)

                if system.y[0].id == system.y[1].id:
                    debug.save_bad_id(data.id)

                final_item_id = critic(conversation_history)
                if system.y[0].id == final_item_id:
                    print("Accepted in-budget item")
                    res = 0
                elif system.y[1].id == final_item_id:
                    print("Accepted out-of-budget item")
                    SWR += 1    
                    res = 1

                break

        _save_conversation_history(system, conversation_history, data, res)

    print(f'SR: {SR / (data_idx+1)} / AT: {AT / SR} / SWR: {SWR / SR}')




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
    parser.add_argument('--user_model', type=str, default='gpt-4o-mini', help='model name')
    parser.add_argument('--rec_model', type=str, default='gpt-4o-mini', help='model name')
    parser.add_argument('--file_name', type=str, default='data/clothing/css_data.json')

    cmd_args = parser.parse_args()
    cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

    dataset, _, _ = load_dataset(cmd_args.file_name)
    cmd_args.sample_times = len(dataset)

    main(cmd_args, dataset)
