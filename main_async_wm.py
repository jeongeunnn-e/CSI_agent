import pdb
import debug
import torch
import json
import traceback
import argparse
from tqdm import tqdm
from utils import _get_conversation_history, critic_async, _conv_history_to_string
import os
from load_data import load_dataset, load_decision, load_openness
from core.players.agent_async_wm import Recommender_WMemory as Recommender_async
from core.players.user_async import Seeker_async
from core.players.tool import Tool
from core.players.memory import Memory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import asyncio
from tqdm.asyncio import tqdm_asyncio

torch.cuda.init()
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)


collected_predictions = []

total_cost = 0
lock = asyncio.Lock()
memory = Memory()
# memory.load_memory("memory/memory_conv_99")

with open('result_style_sample_150.json', "r", encoding='utf-8') as f:
    pre_result = json.load(f)


def calculate_cost(prompt_tokens, completion_tokens, model="gpt-3.5-turbo"):
    if model == "gpt-3.5-turbo":
        prompt_cost_per_1M = 0.150
        completion_cost_per_1M = 0.6

    elif model == 'gpt-4o':
        prompt_cost_per_1M = 2.5
        completion_cost_per_1M = 10

    elif model == "gpt-3.5-turbo":
        prompt_cost_per_1M = 0.5
        completion_cost_per_1M = 1.5

    elif model == "gpt-3.5-turbo-instruct":
        prompt_cost_per_1M = 1.5
        completion_cost_per_1M = 2

    else:
        raise ValueError("Invalid model. Choose 'gpt-3.5-turbo'")

    # 비용 계산
    prompt_cost = (prompt_tokens / 1000000) * prompt_cost_per_1M
    completion_cost = (completion_tokens / 1000000) * completion_cost_per_1M

    total_cost = prompt_cost + completion_cost
    return total_cost


async def async_generate(cmd_args, data):
    global collected_predictions
    tool = Tool(cmd_args.domain, cmd_args.file_name)
    SR, AT, SWR = 0, 0, 0

    user = Seeker_async(data, cmd_args.user_model, cmd_args.temperature)
    system = Recommender_async(tool, memory, cmd_args)
    try:
        conversation_history, profile = load_previous_conversation(data.data['id'])
        system.load_reconstructed_profile(profile)
        res = -1
        
        while True:

            if len(conversation_history) // 2 > cmd_args.max_turn:
                break

            thought, action = await system.plan(conversation_history)
            sys_utt = await system.generate_utterance(action, conversation_history)
            conversation_history.append(AIMessage(content=sys_utt))

            usr_utt = await user.generate_utterance(conversation_history)
            conversation_history.append(HumanMessage(content=usr_utt))

            # print("\033[1;34mSystem:\033[0m", sys_utt)
            # print("\033[1;32mUser:\033[0m", usr_utt)

            # if system.actions[-1] == "Persuasion":
            #     continue``
 
            if "#STOP#" in usr_utt:
                try:
                    final_item_id = await critic_async(conversation_history)
                    print(final_item_id)
                    if final_item_id in [candidate.id for candidate in system.candidates]:
                        SWR += 1
                        print("Accepted out-of-budget item")
                        res = 1
                        system.memory.add_memory(system.reconstructed_profile._string_format(), memory_format(system, conversation_history))
                        print("memory updated")
                    elif system.selected[0].id == final_item_id:
                        res = 0

                    SR += 1
                    AT += len(conversation_history) // 2
                except Exception as e:
                    traceback.print_exc()
                    print("Error in critic_async : ", e)
                    break
                break
            
        output_conv = _get_conversation_history(system, conversation_history, res, SR, AT, SWR, data.data)
    except Exception as e:
        traceback.print_exc()
        print(f"Exception occurred: {e}")
        # output_conv = _get_conversation_history(system, conversation_history, res, SR, AT, SWR, data.data)

    async with lock:
        try:
            if output_conv is not None:
                collected_predictions.append(output_conv)
        except Exception as e:
            print(f'save error: {e}')


async def generate_concurrently(args, dset, batch_size=10):
    for i in range(0, len(dset), batch_size):
        batch_data = dset[i:i + batch_size]
        tasks = [async_generate(args, data) for data in batch_data]
        batch_results = await tqdm_asyncio.gather(*tasks)
        print(f'batch processing : {i // batch_size} / {len(dset) // batch_size}')


async def run_main(args, dset):
    await generate_concurrently(args, dset)


def memory_format(system, conversation_history):
    return {
        "strategy": system.persuasion_strategies[-1],
        "utterance": conversation_history[-2].content
    }


def load_previous_conversation(data_num):
    data_num = int(data_num)
    prev_res = pre_result[data_num]
    assert prev_res['user_data']['id'] == str(data_num)
    prev_action = prev_res['actions']
    try:
        limit_turn = len(prev_action[:prev_action.index('Persuasion')])
    except ValueError:
        limit_turn = len(prev_action[:prev_action.index('Suggestion')])
    except:
        return prev_res['conversation'][:5], prev_res['profile update'][2]

    prev_conv = prev_res['conversation'][:limit_turn*2+1]
    prev_conv_list = []
    for utt in prev_conv:
        if utt['role'] == 'user':
            prev_conv_list.append(HumanMessage(utt['content']))
        else:
            prev_conv_list.append(AIMessage(utt['content']))

    return prev_conv_list, prev_res['profile update'][limit_turn+1]


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
    parser.add_argument("--save_path", type=str, default=f'example/test_passive_100.json')
    parser.add_argument('--domain', type=str, default='clothing', help='domain name')
    parser.add_argument('--temperature', type=float, default=0, help='temperature')
    parser.add_argument('--type', type=str, default='Less Active', help='type of the experiment')

    cmd_args = parser.parse_args()
    cmd_args.device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'

    # dataset, _, _ = load_dataset(cmd_args.file_name)
    # cmd_args.sample_times = len(dataset)
    # dset = dataset[:10]

    type = 'Active'

    dataset, _, _ = load_dataset('data/clothing/css_style_sample_150.json')
    cmd_args.sample_times = len(dataset)
    dset = dataset

    asyncio.run(run_main(cmd_args, dset))

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f'example/wm_test_{type}{len(dset)}_{current_date}.json', "w", encoding='utf-8') as f:
        json.dump(collected_predictions, f, indent=4)

    print(f'saved at example/wm_test_{type}{len(dset)}_{current_date}.json')

    SR = [ d['sr'] for d in collected_predictions]
    SWR = [ d['swr'] for d in collected_predictions]
    AT = [ d['at'] for d in collected_predictions]

    print(f"{type} - {len(dataset)}")
    print("Total : ", len(SR))
    print("Sucess Rate : ", sum(SR)/len(SR))
    print("SWR : ", sum(SWR)/sum(SR))
    print("Average Turn : ", sum(AT)/sum(SR))

    memory.save_memory(f"memory/memory_{type}{len(dset)}_{current_date}")
    print(f"saved at memory/memory_{type}{len(dset)}_{current_date}")