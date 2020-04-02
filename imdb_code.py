# imdb.py
from tqdm import tqdm
import os
import pandas as pd
import numpy as np

BASIC_FILE = r'D:\imdb\basic_data.tsv'
RATING_FILE = r'D:\imdb\rating_data.tsv'
EPISODE_FILE = r'D:\imdb\episode_data.tsv'
KEYWORDS = ['Star Trek', 'Next Generation']
KEYWORDS = ['The Office']
ROW_ID = None
ROW_ID = 'tt0386676'
RAKING_THRES = 7.0


def load_database(name, filename):
    print('Loading {0} databases'.format(name))
    if os.path.exists(filename + '.pickle'):
        database = pd.read_pickle(filename + '.pickle')
    else:
        database = pd.read_csv(filename, sep='\t')
        database.to_pickle(filename + '.pickle')
    return database

BASIC = load_database('basic', BASIC_FILE)
EPISODE = load_database('episode', EPISODE_FILE)
RATING = load_database('rating', RATING_FILE)

class IMDB:
    def __init__(self, tconst, parent=None):
        self.tconst = tconst
        # rows
        self.b_row = None
        self.e_row = None
        self.r_row = None
        if parent is not None:
            self.name = parent.name
        else:
            self.name = None
        self.epname = None
        self.season = None
        self.episode = None
        self.rating = None
        self.votes = None
        self.number = np.nan
        # get ratings
        self.search(tconst)

    def search(self, tconst):
        # get all id names
        basic = BASIC.tconst
        episode = EPISODE.tconst
        rating = RATING.tconst
        # get masks
        b_mask = basic == tconst
        e_mask = episode == tconst
        r_mask = rating == tconst
        # set rows
        if np.sum(b_mask) != 0:
            self.b_row = np.where(b_mask)[0][0]
            self.epname = BASIC.originalTitle[self.b_row]
            if self.name is None:
                self.name = self.epname
        if np.sum(e_mask) != 0:
            self.e_row = np.where(e_mask)[0][0]
            self.season = EPISODE.seasonNumber[self.e_row]
            self.episode = EPISODE.episodeNumber[self.e_row]
            try:
                season = int(self.season)
                episode = int(self.episode)
                self.number = int(season) + episode/1000.0
            except Exception as _:
                pass
        if np.sum(r_mask) != 0:
            self.r_row = np.where(r_mask)[0][0]
            self.rating = RATING.averageRating[self.r_row]
            self.votes = RATING.numVotes[self.r_row]

    def info(self):
        print('CODE: {0}'.format(self.tconst))
        if self.b_row is not None:
            print('\tName: {0}'.format(self.name))
        if self.e_row is not None:
            print('\tEpisode: {0} x {1}'.format(self.season, self.episode))
        if self.r_row is not None:
            print('\tRating: {0} ({1})'.format(self.rating, self.votes))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if np.isnan(self.number):
            return 'IMDB[{0}]'.format(self.name)
        else:
            return 'IMDB[{0}({1})]'.format(self.name, self.number)


def select_id(indices):
    # start condition as True
    cond = True
    # loop around until condition met
    while cond:
        # get user to select id from above
        userinput = input('Select id from list above: ')
        # clean input
        userinput = userinput.strip()
        # test if in indices list
        if userinput in indices:
            return userinput
        else:
            print('WARNING:  User input "{0}" not in list'.format(userinput))


def find_title(*findstrings, logic='AND'):

    # get columns
    idnum = BASIC.tconst
    title = BASIC.originalTitle

    # set up mask
    mask = None

    # get all unique names
    for findstring in findstrings:
        if mask is None:
            mask = title.str.contains(findstring)
        elif logic == 'AND':
            mask &= title.str.contains(findstring)
        else:
            mask |= title.str.contains(findstring)

    for row in title[mask].index:
        print('ID = {0} Name = {1}'.format(idnum[row], title[row]))

    return np.array(idnum[mask])


def get_episodes(parentid):

    # get columns
    idnum = EPISODE.tconst
    parentids = EPISODE.parentTconst
    # find all ids with parentid
    mask = parentids == parentid
    # return ids
    return np.array(idnum[mask])


def get_instances(ids, parent=None):

    instances = []
    # loop around ids
    for idnum in tqdm(ids):
        # make imdb object
        instance = IMDB(idnum, parent=parent)
        # append to list
        instances.append(instance)
    # return instances
    return instances


def find_ratings(instances):
    # define empty storage
    ratings, votes, numbers = [], [], []
    for instance in instances:
        # append to lists
        ratings.append(instance.rating)
        votes.append(instance.votes)
        numbers.append(instance.number)


    # return ratings and votes
    return np.array(ratings), np.array(votes), np.array(numbers).astype(float)



if __name__ == '__main__':

    if ROW_ID is None:
        # find title
        print('Finding titles')
        title_ids = find_title(*KEYWORDS)
        
        # from ask for id
        print('Selcting title')
        rowid = select_id(title_ids)
    else:
        rowid = str(ROW_ID)

    # get parent
    parent = IMDB(rowid)

    # get episodes for this rowid
    print('Get episodes for rowid={0}'.format(rowid))
    ep_ids = get_episodes(rowid)

    # get objects
    print('Getting IMDB objects')
    episodes = get_instances(ep_ids, parent=parent)

    # get all ratings
    ratings, votes, numbers = find_ratings(episodes)

    # sort by number
    sort = np.argsort(numbers)
    episodes = np.array(episodes)[sort]
    ratings = ratings[sort]
    votes = votes[sort]
    numbers = numbers[sort]

    # fig, frame = plt.subplots(ncols=1, nrows=1)
    # sc = frame.scatter(np.arange((len(ratings))), ratings)
    # frame.set_xticks(np.arange((len(ratings))))
    # frame.set_xticklabels(numbers)

    # mask by ranking
    mask = ratings >= RAKING_THRES

    for it, episode in enumerate(episodes[mask]):
        args = [it + 1, episode.season, episode.episode, 
                episode.rating, episode.votes, episode.epname]
        print('{0}: {1}x{2}  {3}  ({4}) {5}'.format(*args))




