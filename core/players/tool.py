import core.players.tools.category_tree as ct
from core.players.tools.retriever import Retriever

class Tool:
    def __init__(self):
        self.category_tree = ct.get_tree()
        self.retriever = Retriever()

    def category_search(self, current_path):

        if len(current_path) == 0:
            path_options = self.category_tree.get_init_detph_3_paths()
        else:
            path_options = self.category_tree.get_depth_3_paths_from(current_path[-1])

        return path_options


    def category_update(self, thought_category, current_path):
        
        if isinstance(thought_category, str):
            thought_category = thought_category.split(" > ")

        if len(thought_category) == 0:
            return current_path
        
        if isinstance(thought_category[0], str):
            thought_category = thought_category[0].split(" > ")
        
        category_paths = self.category_tree.get_paths_to_node(thought_category[-1])

        if len(category_paths) == 0:
            return current_path
        
        if len(category_paths) == 1:
            category_path = category_paths[0]
        else:
            k = 0
            for category_path in category_paths:
                if len(set(category_path) & set(current_path)) > k:
                    k = len(set(category_path) & set(current_path))
                    new_path = category_path

        new_path = category_path if len(category_path) > len(current_path) else current_path

        return new_path


