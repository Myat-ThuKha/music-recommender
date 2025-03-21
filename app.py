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
            <div class="dataset-card bg-yellow-100 bg-opacity-50 p-6 rounded-lg shadow-lg transition-transform transform hover:scale-105">
                <h2 class="text-pink-900 text-2xl font-bold text-center mb-4">Individual Tracks</h2>
                <p class="text-pink-700 text-lg leading-relaxed mb-2"><span class="font-bold">Diversity:</span> Tracks span decades with varied artist representation</p>
                <p class="text-pink-700 text-lg leading-relaxed mb-2"><span class="font-bold">Trends:</span> Popularity skews modern; audio features correlate (e.g., energy and loudness)</p>
                <p class="text-pink-700 text-lg leading-relaxed mb-4"><span class="font-bold">Insight:</span> Musical keys and modes suggest composition biases; recent decades dominate popularity due to streaming.</p>
                <div class="image-container mb-4">
                    <img src="/static/images/tracks/tracks_distribution.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                    <p class="text-pink-700 text-sm text-center mt-2">Distribution of Tracks Across Decades</p>
                </div>
                <div class="image-container">
                    <img src="/static/images/tracks/track_Correlation.png" alt="Track Correlation" class="rounded-md shadow-md" align="center">
                    <p class="text-pink-700 text-sm text-center mt-2">Correlation Between Audio Features</p>
                </div>
            </div>
        '''
    elif selected_dataset == 'artists':
        return '''
            <h2 class="text-pink-900 text-center font-bold" text-center font-bold">Artists</h2>
            <p class=text-pink-700><b>Variability</b>: Artists range from niche (low count) to prolific (high count).</p>
            <p class=text-pink-700><b>Popularity</b>: Not strongly tied to output—modern artists excel.</p>
            <p class=text-pink-700><b>Insight</b>: Feature averages reflect artist style consistency; outliers indicate unique profiles.</p>
            <div class="image-container mb-4">
                    <img src="/static/images/artists/distributionFeatures.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
            <div class="image-container mb-4">
                    <img src="/static/images/artists/popularityVsTrackCount.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>

        '''
    elif selected_dataset == 'genres':
        return '''
            <h2 class="text-pink-900 text-center font-bold">Genres</h2>
            <p class=text-pink-700><b>Clustering</b>: Genres form distinct feature clusters (e.g., high dance/energy for Dance genres).</p>
            <p class=text-pink-700><b>Correlations</b>: Strong relationships between energy, loudness, and acousticness.</p>
            <p class=text-pink-700><b>Insight</b>: Genre defines sound; danceable genres align with modern trends.</p>
            <div class="image-container mb-4">
                    <img src="/static/images/genres/correlation.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
        '''
    elif selected_dataset == 'years':
        return '''
            <h2 class="text-pink-900 text-center font-bold">Yearly Trends</h2>
            <p class=text-pink-700><b>Evolution</b>: Clear shift from acoustic to danceable/energetic music over time.</p>
            <p class=text-pink-700><b>Popularity</b>: Rises with streaming era.</p>
            <p class=text-pink-700><b>Insight</b>: Reflects technological (e.g., production) and cultural (e.g., dance music) shifts.</p>
            <div class="image-container mb-4">
                    <img src="/static/images/year/5YearRollingAverage.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
            <div class="image-container mb-4">
                    <img src="/static/images/year/audioFeaturesOverTime.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
        '''
    elif selected_dataset == 'artists-genres':
        return '''
            <h2 class="text-pink-900 text-center font-bold">Artists with Genres</h2>
            <p class=text-pink-700><b>Versatility</b>: Many artists span multiple genres.</p>
            <p class=text-pink-700><b>Popularity</b>: Multi-genre artists show varied success</p>
            <p class=text-pink-700><b>Insight</b>: Genre count may broaden appeal or dilute focus.</p>
            <div class="image-container mb-4">
                    <img src="/static/images/artistWgenres/numberOfGenresPerArtist.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
            <div class="image-container mb-4">
                    <img src="/static/images/artistWgenres/top10genresperArtist.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
        '''
    elif selected_dataset == 'merged':
        return '''
            <h2 class="text-pink-900 text-center font-bold">Merged Insights</h2>
            <p class=text-pink-700><b>Integration</b>: Merging reveals how tracks align with artist and genre averages over time.</p>
            <p class=text-pink-700><b>Deviation</b>: Tracks deviating from genre norms (e.g., danceability_dev) may be innovative.</p>
            <p class=text-pink-700><b>Insight</b>: Top genres drive popularity trends; modern tracks cluster in high-energy/dance space.</p>
            <div class="image-container mb-4">
                    <img src="/static/images/cross/popularity_trend.png" alt="Tracks Distribution" class="rounded-md shadow-md">
                </div>
        '''
    else:
        return '<p class=text-pink-700>Select a dataset above to see its analysis.</p>'


@app.route('/recommendation', methods=['POST'])
def recommendation():
    songs = recommend_songs([{'name': request.form['song_name'], 'year':2015 ,'artist': request.form['artist']}])
    for song in songs:
        song['artists'] = ast.literal_eval(song['artists'])
    return render_template('recommended_songs.html',songs=songs,len=len(songs))


@app.route('/eda_data_details', methods=['GET'])
def eda_data_details():
    return render_template('EDA_data.html')


if __name__ == '__main__':
    app.run(debug=True)