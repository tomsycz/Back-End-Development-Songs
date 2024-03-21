from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route('/health')
def health():
    return {"status":"ok"}


@app.route('/count')
def count():
    count = db.songs.count_documents({})

    return {"count": count}


@app.route('/song')
def get_songs():
    data = db.songs.find({})
 
    result = json_util.dumps(list(data))

    return {"songs": result}


@app.route('/song/<int:id>')
def get_song_by_id(id):
    result = db.songs.find_one({"id": id})
    print(result)

    if not result: 
        return {"Message": "song with id not found"}, 404

    return json_util.dumps(result), 200

@app.route('/song', methods=["POST"])
def create_song():
    data = request.get_json()
    id = data['id']
    result = db.songs.find_one({"id": id})

    if result:
        return {"Message": "song with id {0} already present".format(id)}


    song_doc = db.songs.insert_one(data)
    inserted_id = song_doc.inserted_id

    print(inserted_id)
    return {"inserted id": json_util.dumps(inserted_id)}, 200 


@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    song = db.songs.find_one({"id": id})

    if not song:
        return {"message": "Song not found"}, 404
    
    data = request.get_json() 
    newData ={ "$set": data }

    song_doc = db.songs.update_one({"id": id}, newData)
    modified_count = song_doc.modified_count

    if modified_count == 0:
        return {"message": "song found, but nothing updated"}

    updated_song = db.songs.find_one({"id": id})
    return json_util.dumps(updated_song), 200


@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    deleted_count = result.deleted_count
    
    if deleted_count == 0:
        return {"message": "song not found"}, 404

    return {},204




