from argparse import Namespace

PPDPP = {
    "seed": 1,
    "num_gpus": 1,
    "epochs": 50000,
    "gamma": 0.999,
    "learning_rate": 1e-6,
    "system": "gpt-4o-mini",
    "user": "gpt-4o-mini",
    "critic": "gpt-4o-mini",
    "sft_dir": "sft",
    "max_turn": 8,
    "mode": "train",
    "load_rl_epoch": 0,
    "cache_dir": "/data/huggingface_cache",
    "max_new_tokens": 32,
    "max_seq_length": 512,
    "debug": False,  #
    "model_path": "arya555/vicuna-7b-v1.5-hf",
    "model_name": "roberta",
    "model_name_or_path": "roberta-large"
}

MTCS = {
    "output": "outputs/gdpzero.pkl",
    "llm": "gpt-4o-mini",
    "gen_sentences": -1,
    "num_mcts_sims": 20,
    "max_realizations": 3,
    "Q_0": 0.0,
    "num_dialogs": 20,
    "debug": False,
    "cpuct": 1.0
}

def get_config(agent_type):
    if agent_type == 'PPDPP':
        return Namespace(**PPDPP)
    elif agent_type == 'MCTS':
        return Namespace(**MTCS)