import os
import psycopg2
import random
from flask import Flask, request, render_template, redirect, send_from_directory
import string
import urllib.parse

# Parse the DATABASE_URL from environment variables
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# Connect to the PostgreSQL database
db = psycopg2.connect(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)

# Initialize cursor
cur = db.cursor()
db.autocommit = True

PORT = int(os.environ.get("PORT", 3001))
# Host for URL generation
HOST = os.environ.get("HOST", 'http://127.0.0.1')
# Max table capacity
MAX_CAPACITY = int(os.environ.get("MAX_CAPACITY", 1000))

app = Flask(__name__)

# Function to create the table if it does not exist
def create_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS urls(
        id SERIAL PRIMARY KEY NOT NULL,
        longurl TEXT NOT NULL,
        alias TEXT NOT NULL,
        clicks INT DEFAULT 0
    );
    """
    cur.execute(create_table_query)

# Call the create_table function to ensure the table exists
create_table()

# Function to check the number of rows in the table
def check_table_capacity():
    cur.execute("SELECT COUNT(*) FROM urls")
    row_count = cur.fetchone()[0]
    return row_count

# Function to recycle (delete) the oldest entry if the table is too full
def recycle_old_entries():
    if check_table_capacity() >= MAX_CAPACITY:
        cur.execute("DELETE FROM urls WHERE id IN (SELECT id FROM urls ORDER BY id ASC LIMIT 1)")
        print("Deleted oldest entry to free up space.")

# Function to validate the URL
def valid(long_url):
    protocol_exists = False
    protocols = ["http://", "https://", "ftp://", "ftps://"]
    if "." not in long_url:
        return False
    if long_url.rfind('.') == len(long_url) - 1:
        return False
    for protocol in protocols:
        if protocol in long_url:
            protocol_exists = True
    return protocol_exists

# Function to check if alias already exists
def already_exists(alias):
    cur.execute("SELECT longurl FROM urls WHERE alias = %s", (alias,))
    return cur.fetchone() is not None

# Function to fetch URL stats
def url_stats(alias):
    cur.execute("SELECT * FROM urls WHERE alias = %s", (alias[:-1],))
    try:
        id, long_url, alias, clicks = cur.fetchone()
        return render_template('stat.html', host=HOST, long_url=long_url, slit_url=HOST + alias, clicks=clicks)
    except:
        return render_template('404.html', host=HOST)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url = request.form.get('long-url')
        alias = request.form.get('custom-alias')
        if urllib.parse.urlparse(long_url).scheme == '':
            long_url = 'http://' + long_url
        if not valid(long_url):
            return render_template('index.html', err_msg="Enter a Valid URL.")
        if alias == '':
            while already_exists(alias) or alias == '':
                alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(6))
        if not alias.isalnum():
            return render_template('index.html', err_msg="Please Enter a Valid Alphanumeric Alias or leave the field empty.")
        if already_exists(alias):
            return render_template('index.html', err_msg="Alias already taken.")

        # Recycle old entries if the table has reached its max capacity
        recycle_old_entries()

        cur.execute("INSERT INTO urls (longurl, alias, clicks) VALUES (%s, %s, 0)", (long_url, alias))
        return render_template('index.html', slit_url=HOST + alias)
    return render_template('index.html')

@app.route('/<alias>')
def redirect_short_url(alias):
    if alias[-1] == '~':
        return url_stats(alias)
    cur.execute("SELECT longurl FROM urls WHERE alias = %s", (alias,))
    try:
        long_url = cur.fetchone()[0]
        cur.execute("UPDATE urls SET clicks = clicks + 1 WHERE alias = %s", (alias,))
        return redirect(long_url)
    except:
        return render_template('404.html', host=HOST)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
