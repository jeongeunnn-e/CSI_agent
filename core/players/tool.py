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
            path_options = self.category_tree.get_depth_3_paths_from_path(current_path)

        return path_options
    
    
    def category_update(self, thought_category, current_path):
        if len(thought_category) == 0 or thought_category == "None":
            return current_path

        # thought_category = thought_category.split(" > ")
        current_path.extend(thought_category)
        new_path = self.category_tree.check_existing_path(current_path)

        return new_path



