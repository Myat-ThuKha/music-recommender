import os
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.metrics import euclidean_distances
from scipy.spatial.distance import cdist


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict

import warnings
warnings.filterwarnings("ignore")

data = pd.read_csv("./data/data.csv")
genre_data = pd.read_csv('./data/data_by_genres.csv')
year_data = pd.read_csv('./data/data_by_year.csv')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id='20d6ffba508b4317b4f716fc5452c8a0',
                                                           client_secret='8d74366e1f4a4e47b0a44c32b9140be7'))



def find_song(name, year,artist):
    song_data = defaultdict()
    results = sp.search(q= 'track:{} year:{} artist:{}'.format(name,year,artist), limit=1)

    if results['tracks']['items'] == []:
        return None

    results = results['tracks']['items'][0]
    
    song_data['name'] = [name]
    song_data['year'] = [year]
    song_data['explicit'] = [int(results['explicit'])]
    song_data['duration_ms'] = [results['duration_ms']]
    song_data['popularity'] = [results['popularity']]
    genres = sp.artists([str(results['artists'][0]['id'])])['artists'][0]['genres']

    if genres == []:
        audio_features = year_data[year_data['year'] == year]
        audio_features = audio_features.drop(columns=['year'])
        for key, value in audio_features.items():
            song_data[key] = value
    else:
        audio_features= genre_data[genre_data['genres'] == genres[0]]
        audio_features = audio_features.drop(columns=['genres'])
        for key, value in audio_features.items():
            song_data[key] = value
    return pd.DataFrame(song_data)

from collections import defaultdict
from scipy.spatial.distance import cdist

number_cols = ['valence','year', 'acousticness', 'danceability', 'duration_ms', 'energy', 'explicit',
 'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'popularity', 'speechiness', 'tempo',]


def get_song_data(song, spotify_data):
    spotify_data[(spotify_data['name'] == song['name'])& (spotify_data['year'] == song['year'])]
     
    try:
        song_data = spotify_data[(spotify_data['name'] == song['name']) 
                                & (spotify_data['year'] == song['year'])].iloc[0]
        print("Song found in database!")
        return song_data
    
    except IndexError:
        
        print("Song not found in database. Searching Spotify...")
        return find_song(song['name'],song['year'], song['artist']).iloc[0]
        

def get_mean_vector(song_list, spotify_data):
    
    song_vectors = []
    
    for song in song_list:
        song_data = get_song_data(song, spotify_data)
        if song_data is None:
            print('Warning: {} does not exist in Spotify or in database'.format(song['name']))
            continue
        song_vector = song_data[number_cols].values
        song_vectors.append(song_vector)  
    
    song_matrix = np.array(list(song_vectors))
    return np.mean(song_matrix, axis=0)


def flatten_dict_list(dict_list):
    
    flattened_dict = defaultdict()
    for key in dict_list[0].keys():
        flattened_dict[key] = []
    
    for dictionary in dict_list:
        for key, value in dictionary.items():
            flattened_dict[key].append(value)
            
    return flattened_dict


def recommend_songs( song_list, n_songs=10):
    
    metadata_cols = ['name', 'year', 'artists']
    song_dict = flatten_dict_list(song_list)
    
    song_center = get_mean_vector(song_list, data)
    song_cluster_pipeline = Pipeline([('scaler', StandardScaler()), 
                                  ('kmeans', KMeans(n_clusters=20, 
                                   verbose=False))
                                 ], verbose=False)
    X = data.select_dtypes(np.number)
    song_cluster_pipeline.fit(X)
    scaler = song_cluster_pipeline.steps[0][1]
    scaled_data = scaler.transform(data[number_cols])
    scaled_song_center = scaler.transform(song_center.reshape(1, -1))
    distances = cdist(scaled_song_center, scaled_data, 'cosine')
    index = list(np.argsort(distances)[:, :n_songs][0])
    
    rec_songs = data.iloc[index]
    rec_songs = rec_songs[~rec_songs['name'].isin(song_dict['name'])]
    return rec_songs[metadata_cols].to_dict(orient='records')
