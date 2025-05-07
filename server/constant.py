db_uri = "sqlite:///./db/project.db"
bulk_write_limit = 100
relationship_limit = 5
max_thread_worker = 20

# crawler config
seed_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
backup_url = 'https://comp4321-hkust.github.io/testpages/testpage.htm'
max_page = 300
remove_cyclic_relationship: bool = True
delete_unfounded_item: bool = False

# search scoring weights
title_weight = 0.7

# relevance feedback
relevant_weight = 0.5
non_relevant_weight = 0.25
max_relevant_query_considered = 5
max_ranked_words = 5

# co occurence
co_occurence_weight = 0.5
max_query_co_occurence_terms = 5
co_occurence_title_frequency_threshold = 1
co_occurence_body_frequency_threshold = 3
pmi_threshold = 0.3
pmi_title_weight = 0.3

# pagerank
pagerank_damping_factor = 0.85
pagerank_weight = 0.3
pagerank_iteration = 20

# fuzzy word matching
max_fuzzy_word_matching = 5