import os
import torch
import argparse
from tqdm import tqdm
import traceback

from load_data import *
from core.players.user_async import Seeker_async as Seeker
from baselines.agent_async import ReAct_Async as ReAct
from baselines.agent_async import PCCRS_Async as PCCRS
from core.players.tool import Tool
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from utils import critic_async, _get_conversation_history

import asyncio
from tqdm.asyncio import tqdm_asyncio

torch.cuda.init()
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)


collected_predictions = []

total_cost = 0
lock = asyncio.Lock()

baseline_model = {
    "react-crs": ReAct,
    "pc-crs": PCCRS
}

async def async_generate(cmd_args, data):
    global collected_predictions

    tool = Tool(cmd_args.domain, cmd_args.file_name)
    
    SR, AT, SWR = 0, 0, 0

    user = Seeker(data, cmd_args.user_model, cmd_args.temerature)
    system = baseline_model[cmd_args.baseline](tool, cmd_args.rec_model)

    try:
        init_utt = await user.init_utt_async(data)
        conversation_history = [
            HumanMessage(content=init_utt),
        ]
        res = -1

        for i in range(cmd_args.max_turn):

            sys_utt = await system.generate_utterance(conversation_history)
            conversation_history.append(AIMessage(content=sys_utt))

            usr_utt = await user.generate_utterance(conversation_history)
            conversation_history.append(HumanMessage(content=usr_utt))

            if "#STOP#" in usr_utt:

                SR += 1
                AT += i+1

                final_item_id = await critic_async(conversation_history)
                if system.selected[0].id == final_item_id:
                    res = 0
                elif final_item_id in [candidate.id for candidate in system.candidates]:
                    SWR += 1
                    res = 1
                break

        output_conv = _get_conversation_history(system, conversation_history, res, SR, AT, SWR, data.data)
    
    except Exception as e:
        traceback.print_exc()
        print(f"Exception occurred: {e}")
        output_conv = None

    async with lock:
        try:
            if output_conv is not None:
                collected_predictions.append(output_conv)
        except Exception as e:
            print(f'save error: {e}')
    
async def generate_concurrently(args, dset, batch_size=10):
    for i in range(0, len(dset), batch_size):
        print(f'batch processing : {i // batch_size} / {len(dset) // batch_size}')
        batch_data = dset[i:i + batch_size]
        tasks = [async_generate(args, data) for data in batch_data]
        batch_results = await tqdm_asyncio.gather(*tasks)
        print_current_result()


async def run_main(args, dset):
    await generate_concurrently(args, dset)


def _get_conversation_history(sys, conversation_history, res, sr, at, swr, data):
    output = {}
    serializable_history = [
        {
            "role": "system" if isinstance(msg, SystemMessage) else "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content
        }
        for msg in conversation_history
    ]
    output['conversation'] = serializable_history

    thoughts = sys.thoughts
    output['thoughts'] = [tmp['Thoughts'] for tmp in thoughts]
    output['actions'] = [tmp['Action'] for tmp in thoughts]

    output['persuasion strategies'] = sys.persuasion_strategies
    output['result'] = (-1, -1) if res == -1 else (1, res)
    output['sr'] = sr
    output['at'] = at
    output['swr'] = swr
    output['user_data'] = data

    return output


def print_current_result():
    global collected_predictions

    SR = [ d['sr'] for d in collected_predictions]
    SWR = [ d['swr'] for d in collected_predictions]
    AT = [ d['at'] for d in collected_predictions]

    print(f"{cmd_args.baseline} - {type} - {len(dataset)}")
    print("Total : ", len(SR))
    print("Sucess Rate : ", sum(SR)/len(SR))
    try:
        print("SWR : ", sum(SWR)/sum(SR))
        print("Average Turn : ", sum(AT)/sum(SR))
    except ZeroDivisionError:
        print("SWR : 0") 
        print("Average Turn : 0")


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
    parser.add_argument('--user_model', type=str, default='gpt-3.5-turbo', help='model name')
    parser.add_argument('--rec_model', type=str, default='gpt-3.5-turbo', help='model name')
    parser.add_argument('--file_name', type=str, default='data/clothing/css_data.json')
    parser.add_argument('--baseline', type=str, default='pc-crs', help='baseline name')
    parser.add_argument('--domain', type=str, default='clothing', help='domain name')
    parser.add_argument('--type', type=str, default='Less Active', help='type of the dataset')
    parser.add_argument('--temerature', type=float, default=0, help='temperature')

    cmd_args = parser.parse_args()
    cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

    type = cmd_args.type
    
    if type in ['Rational', 'Intuitive', 'Dependent']:
        dataset, _, _ = load_decision(cmd_args.file_name, type=type)
    else:
        dataset, _, _ = load_openness(cmd_args.file_name, type=type)
    dataset = dataset[:150]
    cmd_args.sample_times = len(dataset)

    asyncio.run(run_main(cmd_args, dataset))
    
    save_dir = f'baselines/{cmd_args.baseline}-example/{datetime.datetime.now().strftime("%Y-%m-%d")}'
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    save_path = f'{save_dir}/test_{type}{len(dataset)}_{datetime.datetime.now().strftime("%H-%M-%S")}.json'
    with open(save_path, "w", encoding='utf-8') as f:
        json.dump(collected_predictions, f, indent=4)

    print(f"Save results to {save_path}")
    SR = [ d['sr'] for d in collected_predictions]
    SWR = [ d['swr'] for d in collected_predictions]
    AT = [ d['at'] for d in collected_predictions]

    print(f"{cmd_args.baseline} - {type} - {len(dataset)}")
    print("Total : ", len(SR))
    print("Sucess Rate : ", sum(SR)/len(SR))
    print("SWR : ", sum(SWR)/sum(SR))
    print("Average Turn : ", sum(AT)/sum(SR))