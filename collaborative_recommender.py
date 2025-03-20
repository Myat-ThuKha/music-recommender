import pandas as pd
from scipy.spatial.distance import cdist 

user_data = pd.read_csv('data/user_history.csv')

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id='20d6ffba508b4317b4f716fc5452c8a0',
                                                           client_secret='8d74366e1f4a4e47b0a44c32b9140be7'))

genre_data = pd.read_csv('./data/data_by_genres.csv')
year_data = pd.read_csv('./data/data_by_year.csv')

def find_song(genre,artist):
    song_data = defaultdict()
    results = sp.search(q= 'artist:{}'.format(artist), limit=10)
    return results['tracks']['items'][0]

def recommend_songs(user_id):
    user = user_data[user_data['user'] == user_id]
    if user.empty:
        return "User not found in dataset."
    user = user.iloc[0]
    user_tempo = (user['min_tempo'], user['max_tempo'])
    user_list = user_data[user_data['user'] != user_id]
    user_list.loc[:, 'tempo'] = list(zip(user_list['min_tempo'], user_list['max_tempo']))
    user_list.loc[:, 'distance'] = user_list['tempo'].apply(lambda x: cdist([user_tempo], [x], metric='euclidean')[0][0])
    user_list = user_list.sort_values('distance')
    user_list = user_list.head(5)
    recs = []
    recs.append(find_song(user_list.iloc[0]['top_genre'],user_list.iloc[0]['top_artist']))
    return recs
recommended_songs = recommend_songs(65)
for song in recommended_songs:
    print(song['name'], " by " , song['artists'][0]['name'])