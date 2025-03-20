import ast
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
# from surprise import SVD, Dataset, Reader, accuracy
# from surprise.model_selection import train_test_split
import pandas as pd
import joblib
import os
from contentbased_recommender import recommend_songs
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['song_recommendation_db']
users_collection = db['users']
ratings_collection = db['ratings']

# # Load the song catalog from the Kaggle dataset
# songs = {}
# song_popularity = {}
# def load_songs():
#     global songs, song_popularity
#     try:
#         df = pd.read_csv('top_spotify_songs.csv')  # Kaggle dataset
#         # Assuming columns: track_id, track_name, artist_name, streams
#         required_columns = ['track_id', 'track_name', 'artist_name', 'streams']
#         if not all(col in df.columns for col in required_columns):
#             print("Dataset columns:", df.columns)
#             raise ValueError("Dataset must contain 'track_id', 'track_name', 'artist_name', and 'streams' columns")
        
#         # Map track_id to song info
#         for _, row in df.iterrows():
#             track_id = str(row['track_id'])  # Ensure track_id is a string
#             songs[track_id] = f"{row['track_name']} by {row['artist_name']}"
#             song_popularity[track_id] = row['streams']
#     except Exception as e:
#         print(f"Error loading songs: {e}")
#         # Fallback to dummy data
#         songs.update({
#             'song1': 'Shape of You by Ed Sheeran',
#             'song2': 'Bohemian Rhapsody by Queen',
#             'song3': 'Billie Jean by Michael Jackson',
#             'song4': 'Rolling in the Deep by Adele',
#             'song5': 'Sweet Child O\' Mine by Guns N\' Roses'
#         })
#         song_popularity.update({
#             'song1': 3200000000,
#             'song2': 2500000000,
#             'song3': 1800000000,
#             'song4': 1500000000,
#             'song5': 1200000000
#         })

# # Train and test the recommendation model
# def train_and_test_model():
#     # Fetch all ratings from MongoDB
#     user_ratings = list(ratings_collection.find())
#     if not user_ratings:
#         return None, None

#     # Convert to DataFrame
#     user_ratings_df = pd.DataFrame(user_ratings, columns=['username', 'song_id', 'rating'])

#     # Prepare data for Surprise
#     reader = Reader(rating_scale=(1, 5))
#     data = Dataset.load_from_df(user_ratings_df[['username', 'song_id', 'rating']], reader)

#     # Split into training and testing sets (80% train, 20% test)
#     trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

#     # Train SVD model
#     algo = SVD()
#     algo.fit(trainset)

#     # Test the model
#     predictions = algo.test(testset)
#     rmse = accuracy.rmse(predictions)
#     print(f"Model RMSE: {rmse}")

#     # Optionally save the trained model to disk
#     if not os.path.exists('models'):
#         os.makedirs('models')
#     joblib.dump(algo, 'models/svd_model.pkl')

#     return algo, rmse

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            if 'bio' in user:
                session['bio'] = user['bio']
            session['joined'] = user['joined']
            session['password'] = password
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({'username': username}):
            return render_template('register.html', error='User already exists')
        users_collection.insert_one({'username': username, 'password': password, 'joined': pd.Timestamp.now()})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    if 'username' not in session:
        return redirect(url_for('login'))
    else :
        if request.method == 'POST':
            if 'username' in request.form:
                username = request.form['username']
            else:
                username = session['username']
            if 'password' in request.form:
                password = request.form['password']
            else:
                password = session['password']
            bio = request.form['bio']
            users_collection.update_one({'username': session['username']}, {'$set': {'username': username, 'password': password, 'bio': bio}})
            return redirect(url_for('info'))
    return render_template('edit_info.html')

@app.route('/deleteAccount', methods=['GET', 'POST'])
def deleteAccount():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('delete_account.html')


@app.route('/info', methods=['GET'])
def info():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        user = users_collection.find_one({'username': session['username']})
        if user: 
            session['username'] = user['username']
            if 'bio' in user:  
                session['bio'] = user['bio']
            if 'joined' in user:
                session['joined'] = user['joined']
            return render_template('info.html', username=session['username'], bio=session['bio'], joined=session['joined'])
        return render_template('info.html')
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('recommendations.html')

@app.route('/songDetails', methods=['GET'])
def songDetails():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('song_details.html')

@app.route('/recommendSongList', methods=['GET'])
def recommendSongList():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('recommended_songs.html')

@app.route('/eda', methods=['GET'])
def eda():
    selected_dataset = request.args.get('dataset', None)
    return render_template('eda.html', selected_dataset=selected_dataset)

@app.route('/eda-content', methods=['GET'])
def eda_content():
    selected_dataset = request.args.get('dataset', None)
    if selected_dataset == 'tracks':
        return '''
            <h2>Individual Tracks</h2>
            <p>Tracks span decades, with popularity peaking post-2000 due to streaming.</p>
            <p>Energy and loudness are strongly correlated (~0.7).</p>
            <img src="/static/images/popularity_by_decade.png" alt="Popularity by Decade">
        '''
    elif selected_dataset == 'artists':
        return '''
            <h2>Artists</h2>
            <p>High track counts don’t guarantee popularity—modern artists lead.</p>
            <p>Artists show consistent audio styles.</p>
            <img src="/static/images/popularity_vs_count.png" alt="Popularity vs Track Count">
        '''
    elif selected_dataset == 'genres':
        return '''
            <h2>Genres</h2>
            <p>EDM is danceable and energetic; classical is acoustic.</p>
            <p>Energy and loudness correlate (~0.8).</p>
            <iframe src="/static/plots/genre_3d_scatter.html" width="100%" height="400px"></iframe>
        '''
    elif selected_dataset == 'years':
        return '''
            <h2>Yearly Trends</h2>
            <p>Danceability and energy rise post-1980; acousticness drops.</p>
            <p>Popularity spikes in the streaming era.</p>
            <img src="/static/images/feature_trends.png" alt="Feature Trends Over Time">
        '''
    elif selected_dataset == 'artists-genres':
        return '''
            <h2>Artists with Genres</h2>
            <p>Multi-genre artists (3-5 genres) have broader appeal.</p>
            <p>Pop, rock, and hip-hop dominate.</p>
            <img src="/static/images/top_10_genres.png" alt="Top 10 Genres">
        '''
    elif selected_dataset == 'merged':
        return '''
            <h2>Merged Insights</h2>
            <p>Modern tracks cluster in high-energy, danceable spaces.</p>
            <p>Top genres like pop drive trends.</p>
            <iframe src="/static/plots/pca_clusters.html" width="100%" height="400px"></iframe>
        '''
    else:
        return '<p>Select a dataset above to see its analysis.</p>'


@app.route('/recommendation', methods=['POST'])
def recommendation():
    songs = recommend_songs([{'name': request.form['song_name'], 'year':2015 ,'artist': request.form['artist']}])
    for song in songs:
        song['artists'] = ast.literal_eval(song['artists'])
    return render_template('recommended_songs.html',songs=songs,len=len(songs))


# @app.route('/recommend', methods=['GET', 'POST'])
# def recommend():
#     if 'username' not in session:
#         return redirect(url_for('login'))
    
#     # Load songs
#     load_songs()

#     if request.method == 'POST':
#         song_id = request.form['song_id']
#         rating = int(request.form['rating'])
#         # Store rating in MongoDB
#         ratings_collection.insert_one({
#             'username': session['username'],
#             'song_id': song_id,
#             'rating': rating
#         })

#     # Train and test the model
#     algo, rmse = train_and_test_model()

#     recommendations = []
#     if algo:
#         # Fetch user ratings to check which songs the user has already rated
#         user_ratings = list(ratings_collection.find({'username': session['username']}))
#         user_ratings_df = pd.DataFrame(user_ratings, columns=['username', 'song_id', 'rating'])

#         # Get recommendations for the current user
#         user_id = session['username']
#         predictions = []
#         for song_id in songs.keys():
#             if not user_ratings_df.empty and song_id in user_ratings_df['song_id'].values:
#                 continue
#             pred = algo.predict(user_id, song_id).est
#             predictions.append((song_id, pred))

#         # Sort predictions by rating
#         predictions.sort(key=lambda x: x[1], reverse=True)
#         recommendations = [(song_id, songs[song_id], round(pred, 2)) for song_id, pred in predictions[:3]]
#     else:
#         # Fallback to popularity-based recommendations for new users
#         sorted_songs = sorted(song_popularity.items(), key=lambda x: x[1], reverse=True)
#         recommendations = [(song_id, songs[song_id], "Popular") for song_id, _ in sorted_songs[:3]]

#     return render_template('recommendations.html', songs=songs, recommendations=recommendations, rmse=rmse)

if __name__ == '__main__':
    app.run(debug=True)