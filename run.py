import os
import psycopg2
import random
from flask import Flask, request, render_template, redirect, send_from_directory
import string, sqlite3
import urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

db = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = db.cursor()
db.autocommit = True

myhost = 'http://slitli.heroku.com/'
app = Flask(__name__)

def valid(long_url):
    protocol_exists=False
    protocols=["http://","https://","ftp://","ftps://"]
    if "." not in long_url:
        return False
    if not long_url.index('.') < len(long_url)-1:
        return False
    for protocol in protocols:
        if protocol in long_url:
            protocol_exists=True
    return protocol_exists

def already_exists(alias):
    cur.execute("SELECT longurl FROM urls WHERE alias = %s", (alias,))
    return cur.fetchone() is not None

def url_stats(alias):
    print "***stats***" #
    cur.execute ("SELECT * FROM urls WHERE alias = %s",(alias[:-1],))
    id, long_url, alias, clicks = cur.fetchone()
    print id,long_url,alias,clicks
    return render_template('stat.html',long_url = long_url,slit_url = myhost + alias,clicks = clicks)
    

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        print "***form Submitted***" #
        long_url = request.form.get('long-url')
        print "***long-url:",long_url,"***" #
        alias = request.form.get('custom-alias')
        print "***custom-alias:",alias,"***" #
        if urlparse.urlparse(long_url).scheme == '':
            long_url = 'http://' + long_url
        if not valid(long_url):
            print "validation",long_url #
            return render_template('index.html',err_msg = "Enter a Valid URL.")
        if alias == '':
            alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqstuvwxyz') for i in range(6))
            while already_exists(alias):
                alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqstuvwxyz') for i in range(6))
        if not alias.isalnum():
            return render_template('index.html',err_msg = "Please Enter a Valid Alphanumeric Alias or leave the field empty.")
        if already_exists(alias):
            return render_template('index.html',err_msg = "Alias already taken.")
        cur.execute ("INSERT INTO urls (longurl,alias,clicks) VALUES (%s,%s,0)",(long_url,alias))
        print "***inserted***" #
        return render_template('index.html',slit_url = myhost + alias)
    return render_template('index.html')



@app.route('/<alias>')
def redirect_short_url(alias):
    print "***alias[-1]",alias[-1] #
    if alias[-1] == '~':
        print "***condition ok***" #
        return url_stats(alias)
    cur.execute ("SELECT longurl FROM urls WHERE alias = %s",(alias,))
    try:
        long_url = cur.fetchone()[0]
        print "***long-url:",long_url,"***"
        cur.execute ("UPDATE urls SET clicks = clicks + 1 WHERE alias = %s",(alias,))
        return redirect(long_url)
    except:
        return render_template('404.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
                               
if __name__ == '__main__':
    print "***initiated***" #
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0',port=port)