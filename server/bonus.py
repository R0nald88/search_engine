from spider import *

def run_bonus_feature():
    db = Session()
    word_ids = db.query(Keyword.word).all()
    word_ids = set(w[0] for w in word_ids)
    compute_pmi(word_ids)
    compute_pagerank()

if __name__ == '__main__':
    time_start = time.time()
    # run_bonus_feature()
    with Session() as db: 
        print(db.query(func.avg(Webpage.pagerank)).scalar())
    print('Time taken:', time.time() - time_start)