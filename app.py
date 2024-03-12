from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
# from scraper import scrape_and_analyze
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from collections import Counter

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
DB_NAME = 'main_news'
DB_USER = 'main_news_user'
DB_PASSWORD = 'mIfkhuS7GrG4tfJTrGU9WubiVoNUnVPj'
DB_HOST = 'dpg-cno12p20si5c73auqskg-a'


import psycopg2


def create_history_table():
    try:
        # Create a cursor object to execute SQL commands
        conn = connect_to_db()
        cursor=conn.cursor()


        # Define the SQL command to create the table
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                link VARCHAR(255) NOT NULL,
                date_time TIMESTAMP NOT NULL,
                username VARCHAR(255) NOT NULL
            )
        '''

        # Execute the SQL command to create the table
        cursor.execute(create_table_query)

        # Commit the transaction
        conn.commit()

        # Close the cursor
        conn.close()
        
        print("Table 'info' created successfully.")
    except Exception as e:
        print("Error:", e)

def create_info_table():
    try:
        # Create a cursor object to execute SQL commands
        conn = connect_to_db()
        cursor=conn.cursor()


        # Define the SQL command to create the table
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS info (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                question VARCHAR(255) NOT NULL,
                answer VARCHAR(255) NOT NULL
            )
        '''

        # Execute the SQL command to create the table
        cursor.execute(create_table_query)

        # Commit the transaction
        conn.commit()

        # Close the cursor
        conn.close()
        
        print("Table 'info' created successfully.")
    except Exception as e:
        print("Error:", e)

# Example of how to use the function with an existing connection
# Assume 'conn' is your existing connection object
# create_info_table(conn)


def scrape_and_analyze(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract article heading
    heading = soup.find('h1').text.strip()  # Adjust this according to the HTML structure of the page
    
    article = ""
    for paragraph in soup.find_all('p'):
        article += paragraph.get_text() + " "

    words = word_tokenize(article)
    sentences = sent_tokenize(article)
    
    num_words = len(words)
    num_sentences = len(sentences)
    
    tagged_words = pos_tag(words)
    
    pos_tags = [tag for (word, tag) in tagged_words]
    pos_tag_counts = Counter(pos_tags)
    
    cleaned_article = article  # You can modify this to clean the article as per your requirements
    
    analysis_results = {
        'heading': heading,
        'num_words': num_words,
        'num_sentences': num_sentences,
        'pos_tag_counts': pos_tag_counts
    }
    
    return analysis_results, cleaned_article

# Function to establish connection with PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

# Home route
@app.route('/')
def home():
    return render_template('login.html')

# Authentication route
@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']

    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM info WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['username'] = username
            # Redirect to the profile page with the username as a parameter
            return redirect(url_for('profile', username=username, name=user[2]))  # Pass the name too
        else:
            return redirect(url_for('home'))
    else:
        return "Error connecting to database"


# Profile route
@app.route('/profile/<username>/<name>')
def profile(username,name):
    if 'username' in session and session['username'] == username:
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT username, name FROM info WHERE username = %s", (username,))
            user_data = cur.fetchone()
            username = user_data[0]
            name = user_data[1]
            cur.close()
            conn.close()
            return render_template('profile.html', username=username, name=name)
    return redirect('/')

# Edit Route
@app.route('/edit')
def edit():
    if 'username' in session:
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT name, username FROM info WHERE username = %s", (session['username'],))
            user_data = cur.fetchone()
            cur.close()
            conn.close()
            if user_data:
                return render_template('edit.html', name=user_data[0], username=user_data[1])
            else:
                # Handle case where user data is not found
                return "User data not found"
        else:
            return "Error connecting to database"
    else:
        return redirect(url_for('home'))

# Update route for updating user profile
@app.route('/update', methods=['POST'])
def update():
    if 'username' not in session:
        return redirect(url_for('home'))  # Redirect if user is not logged in

    # Get form data
    name = request.form['name']
    new_username = request.form['new_username']
    new_password = request.form['new_password']

    # Only allow updates for the currently logged-in user
    if session['username'] == new_username:
        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            # Update user profile in the database
            cur.execute("UPDATE info SET name = %s, password = %s WHERE username = %s", (name, new_password, session['username']))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('profile', username=new_username, name=name))  # Redirect to profile page with updated details
        else:
            return "Error connecting to database"
    else:
        # Handle case where user tries to update another user's details
        return "Unauthorized update attempt"





# Create route
@app.route('/create')
def create():
    return render_template('register.html')

# Submit route for registering users
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        question = request.form['question']
        answer = request.form['answer']

        conn = connect_to_db()
        if conn:
            cur = conn.cursor()
            create_info_table()
            cur.execute('''INSERT INTO info (username, password, name, question, answer) VALUES (%s, %s, %s, %s, %s)''', (username, password, name, question, answer))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))  
    return "Error registering user"


    
# @app.route('/forgot')
# def forgot():
#     return render_template('forgot.html')

@app.route('/register')
def register():
    return render_template('register.html')

# Route for scraping and analyzing
@app.route('/scrape_and_analyze', methods=['GET'])
def analyze():
    if 'username' not in session:
        return redirect(url_for('home'))  # Redirect if user is not logged in

    username = session['username']
    url = request.args.get('url')
    
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        create_history_table()
        cur.execute("INSERT INTO history (link, date_time, username) VALUES (%s, %s, %s)", (url, datetime.now(), username))
        conn.commit()
        cur.close()
        conn.close()
        
        analysis_results, cleaned_article = scrape_and_analyze(url)
        return render_template('analysis_result.html', analysis_results=analysis_results, cleaned_article=cleaned_article)
    else:
        return "Error connecting to database"
    

@app.route('/history')
def history():
    conn = connect_to_db()
    if conn:
        cur = conn.cursor()
        if 'username' in session and session['username'] == "artist":
            # Admin with username "artist" can see all history
            cur.execute("SELECT link, date_time, username FROM history ORDER BY date_time DESC")
            admin = True
        elif 'username' in session:
            # Non-admin users can only see their own history
            cur.execute("SELECT link, date_time FROM history WHERE username = %s ORDER BY date_time DESC", (session['username'],))
            admin = False
        else:
            # Redirect to login page or handle unauthorized access
            return redirect('/login')
        
        search_history = cur.fetchall()
        return render_template('history.html', search_history=search_history, admin=admin)





if __name__ == '__main__':
    app.run(debug=True)
