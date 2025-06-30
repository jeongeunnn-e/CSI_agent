import faiss
import pickle
import numpy as np
from transformers import AutoTokenizer, AutoModel
from collections import defaultdict
import torch

torch.cuda.init()
print(torch.cuda.is_available())
torch.cuda.reset_peak_memory_stats(device=None)


class Memory:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.embedding_dim = self.model.config.hidden_size
        self.index = faiss.IndexFlatL2(self.embedding_dim) 
        self.user_memory = {}  #
        self.conversation_history = defaultdict(list)  
        self.next_id = 0

    def _embed(self, text):
        # Tokenize sentences
        encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        
        # Compute token embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        # Perform pooling
        embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
        return embeddings.numpy()

    def mean_pooling(self, model_output, attention_mask):
        # Mean pooling - take attention mask into account for correct averaging
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 0) / torch.clamp(input_mask_expanded.sum(0), min=1e-9)

    def add_memory(self, user_description, conversation):
        embedding = self._embed(user_description)
        embedding = np.expand_dims(embedding, axis=0).astype(np.float32)  
        
        self.index.add(embedding)
        self.user_memory[self.next_id] = user_description
        self.conversation_history[user_description].append(conversation)
        self.next_id += 1

    def retrieve_memory(self, user_description, top_k=1):
        if self.index.ntotal == 0:
            return None  # No memory stored yet
        
        embedding = self._embed(user_description)
        embedding = np.expand_dims(embedding, axis=0).astype(np.float32)
        
        distances, indices = self.index.search(embedding, top_k)
        retrieved_users = [self.user_memory[idx] for idx in indices[0] if idx != -1]
        
        return [(user, self.conversation_history[user]) for user in retrieved_users]

    def update_memory(self, user_description, new_conversation):
        closest_memories = self.retrieve_memory(user_description)
        if closest_memories:
            user = closest_memories[0][0]  # Get the closest matching user
            self.conversation_history[user].append(new_conversation)
        else:
            self.add_memory(user_description, new_conversation)
    
    def save_memory(self, filepath):
        faiss.write_index(self.index, filepath + ".faiss")
        with open(filepath + ".pkl", "wb") as f:
            pickle.dump((self.user_memory, self.conversation_history, self.next_id), f)

    def load_memory(self, filepath):
        self.index = faiss.read_index(filepath + ".faiss")
        with open(filepath + ".pkl", "rb") as f:
            self.user_memory, self.conversation_history, self.next_id = pickle.load(f)


if __name__ == "__main__":
    memory = Memory()
    memory.add_memory("User who likes sci-fi movies", "Had a conversation about Interstellar.")
    memory.add_memory("User interested in AI", "Discussed about GPT models.")
    
    print(memory.retrieve_memory("I enjoy sci-fi films"))  # Should return closest conversation about Interstellar
    memory.update_memory("User who likes sci-fi movies", "Talked about Dune.")
    print(memory.retrieve_memory("I enjoy sci-fi films"))  # Should now include Dune