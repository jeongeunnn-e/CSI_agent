import core.players.tools.category_tree as ct


def category_search(category_path):
    category_tree = ct.get_tree()

    if category_path is None:
        path_options = category_tree.get_init_detph_3_paths()

    return path_options
    