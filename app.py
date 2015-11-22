import psycopg2 as dbapi2
import random
from flask import Flask, request, render_template, redirect
import string, sqlite3
from urlparse import urlparse

db = dbapi2.connect (database="slitli", user="slitliadmin", password="addmin45")
cur = db.cursor()
db.autocommit = True

host = 'http://localhost:5000/'
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        print "***form Submitted***" #
        long_url = request.form.get('long-url')
        print "***long-url:",long_url,"***" #
        alias = request.form.get('custom-alias')
        print "***custom-alias:",alias,"***" #
        if urlparse(long_url).scheme == '':
            long_url = 'http://' + long_url
        if alias == '':
            alias = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqstuvwxyz') for i in range(6))
        cur.execute ("INSERT INTO urls (longurl,alias,clicks) VALUES (%s,%s,0)",(long_url,alias))
        db.commit ()
        print "***inserted***" #
        return render_template('index.html',slit_url= host + alias)
    return render_template('index.html')



@app.route('/<alias>')
def redirect_short_url(alias):
    cur.execute ("SELECT longurl FROM urls WHERE alias = %s",(alias,))
    try:
        long_url = cur.fetchall()[0][0]
        print "***long-url:",long_url,"***"
        cur.execute ("UPDATE urls SET clicks = clicks + 1 WHERE alias = %s",(alias,))
        return redirect(long_url)
    except:
        return render_template('404.html')


if __name__ == '__main__':
    print "***initiated***" #
    app.run(host="0.0.0.0")