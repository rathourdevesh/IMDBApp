from flask import Flask,jsonify,g,request,make_response
import sqlite3
import hashlib

app=Flask(__name__)
DATABASE = 'database.db'

def get_db_conn():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def verify_user(username,password):
    hpass=hashlib.md5(password.encode('utf-8')).hexdigest()
    query = "select 1 from users where user=? and pass=?"
    args=([username,hpass])
    cur = get_db_conn().execute(query, args)
    res = cur.fetchall()
    if 1 in res[0]:
        return True
    else:
        return False
    cur.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_to_db(popularity,director,genre,imdb_score,name):
    print(popularity,director,genre,imdb_score,name)
    query = "insert into Ratings(name,director,popularity,imdb_score) values(?,?,?,?)"
    args=([name,director,popularity,imdb_score])
    cur = get_db_conn().execute(query, args)
    get_db_conn().commit()
    query = "select id from Ratings where name=?"
    args=([name])
    cur = get_db_conn().execute(query, args)
    id = cur.fetchall()[0][0]
    print(id)
    for i in genre:
        query = "insert into genre_list(title,movie_id) values(?,?)"
        args=([i,id])
        cur = get_db_conn().execute(query, args)
    get_db_conn().commit()

def remove_from_db(movieId):
    query = "delete from Ratings where id=?"
    args=([movieId])
    cur = get_db_conn().execute(query, args)
    query = "delete from genre_list where movie_id=?"
    args=([movieId])
    cur = get_db_conn().execute(query, args)   
    get_db_conn().commit()

def update_db(movieId,fieldName,fieldValue):
    if(fieldName != 'genre'):
        print('update')
        query = "update Ratings set " + fieldName + "=? where id=?"
        args=([fieldValue,movieId])
        cur = get_db_conn().execute(query, args)   
        get_db_conn().commit()
        print('commit')
    else:
        query = "delete from genre_list where movie_id=?"
        args=([movieId])
        cur = get_db_conn().execute(query, args)      
        for i in genre:
            query = "insert into genre_list(title,movie_id) values(?,?)"
            args=([i,movieId])
            cur = get_db_conn().execute(query, args)
        get_db_conn().commit()

def search_db(movieName):
    query = "select * from Ratings where upper(name) like '%"+ movieName.upper() +"%'"
    cur = get_db_conn().execute(query)
    res = cur.fetchall()
    out=[]
    if(len(res) != 0):
        for i in range(len(res)):
            resp={}
            resp["id"] = res[i][0]
            resp["name"] = res[i][1]
            resp["director"] = res[i][2]
            resp["popularity"] = res[i][3]
            resp["imdb_score"] = res[i][4]
            query = "select title from genre_list where movie_id =?"
            args=([res[i][0]])
            cur = get_db_conn().execute(query, args)
            genre_res = cur.fetchall()
            genre_list = [title[0] for title in genre_res]
            resp["genre"]= genre_list
            out.append(resp)
        return out
    else:
        return {"error":"no record found!!!"}


@app.route("/imdbapp/add", methods = ['POST'])
def add_movies():
    print(request.json)
    if(('username' in request.json) & ('password' in request.json)):
        username = request.json['username']
        password = request.json['password']
        print(username)
        vf_code = verify_user(username,password)
        if(vf_code == True):
            popularity = request.json['popularity']
            director = request.json['director']
            genre = request.json['genre']
            imdb_score = request.json['imdb_score']
            name = request.json['name']
            add_to_db(popularity,director,genre,imdb_score,name)
            return jsonify({"message":"Record Added!!"})
        else:
            message = jsonify(message='Unauthrised access!!')
            return make_response(message, 400)
    else:
        message = jsonify(message='Admin User Required!!')
        return make_response(message, 400)

@app.route("/imdbapp/remove/<movieId>", methods = ['DELETE'])
def remove_movies(movieId):
    print(movieId)
    if(('username' in request.json) & ('password' in request.json)):
        username = request.json['username']
        password = request.json['password']
        vf_code = verify_user(username,password)
        if(vf_code == True):
            remove_from_db(movieId)
            return jsonify({"message":"Record Deleted!!"})
        else:
            message = jsonify(message='Unauthrised access!!')
            return make_response(message, 400)
    else:
        message = jsonify(message='Admin User Required!!')
        return make_response(message, 400)

@app.route("/imdbapp/modify",methods=['PUT'])
def modify_movies():
    print(request.json)
    if(('username' in request.json) & ('password' in request.json)):
        username = request.json['username']
        password = request.json['password']
        vf_code = verify_user(username,password)
        if(vf_code == True):
            movieId = request.json['id']
            fieldName = request.json['fieldName']
            fieldValue = request.json['fieldValue']
            if(fieldName in ['popularity','director','genre','imdb_score','name']):
                print(movieId,fieldName,fieldValue)
                update_db(movieId,fieldName,fieldValue)
                return jsonify({"message":"Record Modified!!"})
            else:
                message = jsonify(message='Unauthrised access!!')
                return make_response(message, 400)
        else:
            message = jsonify(message='Unauthrised access!!')
            return make_response(message, 400)
    else:
        message = jsonify(message='Admin User Required!!')
        return make_response(message, 400)     

@app.route("/imdbapp/search/movie/<movieName>",methods=['GET'])
def search_movie(movieName):
    print(movieName)
    resp = search_db(movieName)
    return jsonify(resp)