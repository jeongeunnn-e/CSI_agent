from core.players.user import Seeker


def get_agent(args):
    if "gpt" in args.rec_model:
        from core.players.agent import Recommender
        return Recommender
    if "llama" in args.rec_model:
        from core.players.agent_llama import RecommenderLLama
        return RecommenderLLama

    