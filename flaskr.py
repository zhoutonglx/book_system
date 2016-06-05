#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sqlite3
import pymysql
import os
import sys
#import MySQLdb
import sys
from contextlib import closing
from flask import Flask,request,session,g,redirect,url_for,abort,render_template,flash
from flask import send_from_directory
from werkzeug import secure_filename

#configuration
host='127.0.0.1'
port = '3306'
user = 'root'
#password = 'fengweisi'
db = 'books'
UPLOAD_FOLDER = '/home/zhoutonglx/Desktop/flaskr/static/'
ALLOWED_EXTENSIONS = set(['jpg','png','jpeg'])

#create our little application:)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

def connect_db():
    conn =  pymysql.connect(host='127.0.0.1',port=3306,user='root',password='fengweisi',db='books',charset='utf8')
    return conn

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql',mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g,'db',None)
    if db is not None:
        db.close()

@app.route('/test',methods=['GET'])
def test():
    sql = "select * from book where id=20"
    g.db = g.db.cursor()
    g.db.execute(sql)
    res = g.db.fetchall()
    return 'helloworld' 

@app.route('/')
def index():
    if session.get('logged_in') is None:
        return render_template('login.html');
    cur = g.db.cursor()
    cur.execute('select id,author,name,brief,img_path,price,cot from book')
    L = []
    res = cur.fetchall()
    entries = [dict(uid=row[0],author=row[1],name=row[2],brief=row[3],img_path=row[4],price=row[5],cot=row[6]) for row in res]
    cur.close()
    cur = g.db.cursor()
    sql = "select img_path,author,price from book order by create_time desc"
    cur.execute(sql)
    res = cur.fetchall()
    news = [dict(img_path=row[0],author=row[1],price=row[2]) for row in res]
    return render_template('index.html',entries=entries,news=news)
     

@app.route('/login',methods=['POST'])
def login():
    error = None
    username = request.form['username']
    password = request.form['password']
    sql = "select * from user where username= '"+username+ "' and password = '"+password+"'"
    g.db = g.db.cursor()
    g.db.execute(sql)
    res = g.db.fetchall()
    if len(res) is 0:
        error = 'invalid username or password'
    else:
        session['logged_in'] = True
        session['username'] = res[0][1]
        session['uid'] = res[0][0]
        flash('you were logged in')
        return redirect(url_for('index'))

    return render_template('login.html',error=error)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/login',methods=['POST'])
def admin_login():
    error = None
    admin = request.form['username']
    password = request.form['password']
    sql = "select * from administrator where username= '%s' and password = '%s'" % (admin,password)
    g.db = g.db.cursor()
    g.db.execute(sql)
    res = g.db.fetchone()
    if len(res) is 0:
        error = 'invalid admin or password'
    else:
        session['logged_in'] = True
        session['uid'] = res[0]
        session['username'] = res[1]
        flash('you were logged in')
        return redirect(url_for('show',error=error))
    return render_template('admin.html',error=error)

@app.route('/show')
def show():
    if session.get('logged_in') is None:
        return render_template('login.html');
    g.db = g.db.cursor()
    g.db.execute('select id,author,name,brief,price,cot from book')
    L = []
    res = g.db.fetchall()
    entries = [dict(uid=row[0],author=row[1],name=row[2],brief=row[3],price=row[4],cot=row[5]) for row in res]
    g.db.close()
    return render_template('show.html',entries=entries)


@app.route('/admin/index')
def admin_index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    flash('you were logged out')
    return redirect(url_for('index'))

@app.route('/delete/<int:uid>')
def delete(uid):
#sql = "delete from book where id = %s" % uid
    try:
        g.db.cursor().execute('call del(%d);'%uid)
        g.db.commit()
    except Exception as e:
        return e
    flash('delete succeed')
    return redirect(url_for('show'))	


@app.route('/modify/<int:uid>')
def modify(uid):
    sql = "select * from book where id=%d;" % uid
    try:
        g.db = g.db.cursor()
        res = g.db.execute(sql)
        res = g.db.fetchone()
        #entry = [dict(uid=res[0],author=res[1],brief=res[2],price=res[3],cot=res[5])]
        g.db.close()
        return render_template('modify.html',uid=res[0],author=res[1],name=res[2],brief=res[3],price=res[4],cot=res[5])
    except Exception as e:
        return e

def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/modify_entry',methods=['POST'])
def modify_entry():
    file = request.files.get('file')
    uid = request.form.get('uid')
    name = request.form.get('name')
    cot = request.form.get('cot')
    author = request.form.get('author')
    price = request.form.get('price')
    brief = request.form.get('brief')
    img_path = None
    sql = None
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            send_from_directory(app.config['UPLOAD_FOLDER'],filename)
            img_path = filename
            sql = "update book set author='%s',name='%s' brief='%s',price='%s',img_path='%s',cot='%s' where id='%s'" % (author,name,brief,price,img_path,cot,uid)
        except Exception as e:
            return e
    else:
        sql = "update book set author='%s',name='%s',brief='%s',price='%s',cot='%s' where id='%s'" % (author,name,brief,price,cot,uid)
    try:
        g.db.cursor().execute(sql)
        g.db.commit()
        flash('modified !!')
    except Exception as e:
        return e
    return redirect(url_for('show'))

@app.route('/add-entry')
def add_entry():
    return render_template('add.html')


@app.route('/add',methods=['post'])
def add():
    author = request.form.get('author')
    brief = request.form.get('brief')
    price = request.form.get('price')
    cot = request.form.get('count')
    name = request.form.get('name')
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            send_from_directory(app.config['UPLOAD_FOLDER'],filename)
            img_path = filename
            sql = "insert into book(author,name,brief,price,img_path,cot) values('%s','%s','%s','%s','%s')" % (author,name,brief,price,img_path,cot)
        except Exception as e:
            return e
    else:
        sql = "insert into book(author,brief,price,cot) values('%s','%s','%s','%s');" % (author,brief,price,cot)
        try:
            g.db.cursor().execute(sql) 
            g.db.commit()
            g.db.close()
        except Exception as e:
            return e
	
    flash('add succeed')
    return redirect(url_for('show'))


@app.route('/buy',methods=['POST','GET'])
def buy():
    book_id = request.args.get('book_id')
    uid = request.args.get('uid')
    cot = request.args.get('cot')
    sql = "select cot from book where id='%s'" % book_id
    g.db = g.db.cursor()
    g.db.execute(sql)
    res = g.db.fetchall()
    res = res[0][0]
    if res is 0:
        flash('sold out')
    else:
        sql = "insert into book_order(book_id,uid) values('%s','%s')" % (book_id,uid)
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            return e
        flash('congratulations! you got it')

    return redirect(url_for('index'))

@app.route('/statics')
def statics():
	sql = "select user.id as uid,user.username,book.id as book_id,book.brief from book_order left join user on"\
		   " book_order.uid=user.id left join book on book_order.book_id=book.id"
	cur = g.db.cursor()
	cur.execute(sql)
	res = cur.fetchall()
	entries = [dict(uid=row[0],username=row[1],book_id=row[2],book_name=row[3]) for row in res]
	return render_template('statics.html',entries=entries)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)
