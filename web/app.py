"""
SIMILARITY OF TEXT
Regristracija korisnika
Detekcija slicnosti dokumenata

Resource    Adress      Protocol    Param       Response+Status
--------------------------------------------------------------------------
Register    /register   POST        username    200 OK
user                                password    301 Invalid username
.                                               
--------------------------------------------------------------------------
Detect      /detect     POST        username    200 OK
Similarity                          password    301 Invalid username
.                                   text1       302 Invalid password
.                                   text2       303 Out of tokens
--------------------------------------------------------------------------
Refill      /refill     POST        username    200 OK
.                                   admin_pw    301 Invalid username
.                                   refill      304 Invalid admin password
--------------------------------------------------------------------------
"""

from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def userExists(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if userExists(username):
            retJson = {
                "msg":"Invalid Username"
            }
            return retJson, 301
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "msg":"Successful singup"
        }
        return retJson, 200

def verifyPw(username, password):
    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if hashed_pw == bcrypt.hashpw(password.encode('utf-8'), hashed_pw):
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not userExists(username):
            retJson = {
                "msg":"Invalid Username"
            }
            return retJson, 301

        correct_pw = verifyPw(username, password)
        if not correct_pw:
            retJson = {
                "msg":"Invalid Password"
            }
            return retJson, 302

        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = {
                "msg":"Out of tokens"
            }
            return retJson, 303

        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)

        users.update({
            "Username": username
        },{
            "$set":{
                "Tokens": num_tokens - 1
            }
        })

        retJson = {
                "msg":"Similarity score calculated",
                "ratio": ratio
            }
        return retJson, 200

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        admin_pw = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not userExists(username):
            retJson = {
                "msg":"Invalid Username"
            }
            return retJson, 301

        correct_pw = "abc123"
        if not admin_pw == correct_pw:
            retJson = {
                "msg":"Invalid Admin Password"
            }
            return retJson, 304

        current_tokens = countTokens(username)
        users.update({
            "Username": username
        },{
            "$set":{
                "Tokens": current_tokens + refill_amount
            }
        })
        
        retJson = {
            "msg":"Tokens refilled successfully",
            "current_tokens": current_tokens + refill_amount
        }
        return retJson, 200

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == "__main__":
    app.run(host='0.0.0.0')