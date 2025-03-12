import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from flask import Flask, request, render_template

# Load the dataset (replace with your actual file path)
data = pd.read_csv('universal_top_spotify_songs copy.csv')  # Adjust filename as per your dataset

# Preprocessing: Select relevant features for content-based filtering
content_features = ['danceability', 'energy', 'loudness', 'tempo', 'valence']  # Example features
song_data = data[['name', 'artists'] + content_features].drop_duplicates()

# Normalize the features
scaler = MinMaxScaler()
song_features_scaled = scaler.fit_transform(song_data[content_features])
song_features_df = pd.DataFrame(song_features_scaled, columns=content_features, index=song_data.index)

# Content-Based Filtering: Compute similarity between songs
content_similarity = cosine_similarity(song_features_df)

# Collaborative Filtering: Simulate a user-song interaction matrix (if not in dataset)
# Assuming a small user base for demo (replace with real data if available)
np.random.seed(42)
n_users = 100
user_song_matrix = pd.DataFrame(np.random.randint(0, 2, size=(n_users, len(song_data))),
                                columns=song_data['name'])
user_similarity = cosine_similarity(user_song_matrix)

# Function for content-based recommendations
def get_content_based_recommendations(song_title, top_n=5):
    if song_title not in song_data['name'].values:
        return ["Song not found in dataset"]
    song_idx = song_data[song_data['name'] == song_title].index[0]
    similarity_scores = content_similarity[song_idx]
    similar_indices = similarity_scores.argsort()[-top_n-1:-1][::-1]  # Exclude the song itself
    return song_data.iloc[similar_indices][['name', 'artists']].values.tolist()

# Function for collaborative filtering recommendations
def get_collaborative_recommendations(user_id, top_n=5):
    similar_users = user_similarity[user_id]
    similar_user_indices = similar_users.argsort()[-top_n-1:-1][::-1]  # Top similar users
    user_ratings = user_song_matrix.iloc[similar_user_indices].mean(axis=0)
    recommended_indices = user_ratings.argsort()[-top_n:][::-1]
    return song_data.iloc[recommended_indices][['name', 'artists']].values.tolist()

# Hybrid Recommendations: Combine both methods
def get_hybrid_recommendations(song_title, user_id, top_n=5, content_weight=0.6):
    content_recs = get_content_based_recommendations(song_title, top_n * 2)
    collab_recs = get_collaborative_recommendations(user_id, top_n * 2)
    
    # Convert to dictionaries for scoring
    content_dict = {f"{rec[0]} - {rec[1]}": score * content_weight 
                    for rec, score in zip(content_recs, range(top_n * 2, 0, -1))}
    collab_dict = {f"{rec[0]} - {rec[1]}": score * (1 - content_weight) 
                   for rec, score in zip(collab_recs, range(top_n * 2, 0, -1))}
    
    # Combine scores
    combined_scores = {}
    for song in set(content_dict.keys()).union(collab_dict.keys()):
        combined_scores[song] = content_dict.get(song, 0) + collab_dict.get(song, 0)
    
    # Sort and return top N
    sorted_recs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [song.split(" - ") for song, _ in sorted_recs]

# Flask Web Application
app = Flask(__name__)

@app.route('/')
def index():
    songs = song_data['name'].tolist()
    return render_template('index.html', songs=songs)

@app.route('/recommend', methods=['POST'])
def recommend():
    song_title = request.form['song']
    user_id = int(request.form['user_id'])  # Simulated user ID (0 to 99)
    recommendations = get_hybrid_recommendations(song_title, user_id)
    return render_template('results.html', song=song_title, recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True)