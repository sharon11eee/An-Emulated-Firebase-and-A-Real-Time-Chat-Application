from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient, ASCENDING, DESCENDING
import certifi
from datetime import datetime
from flask_socketio import SocketIO, emit
from bson import ObjectId
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# MongoDB
client = MongoClient("mongodb+srv://dsci551:dsci551@dsci551project.2dqenlp.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client["blah"]
users = db.users
msgs = db.msgs
histories = db.histories
root=db.root
users.create_index([("name", ASCENDING)])

#index creation and optimization
def create_index(collection):
    index_user = []
    users_list = list(collection.find())
    for dic in users_list:
        index_user.append(dic['_id'])
    cnt_index = 10001+len(index_user)
    if cnt_index in index_user:
        new_index = max(index_user)+1
    else:
        new_index = cnt_index
    return new_index

def create_index_2(cl1,cl2):
    index_cl1=[]
    index_cl2=[]
    list_cl1 = list(cl1.find())
    list_cl2 = list(cl2.find())
    for dic in list_cl1:
        index_cl1.append(dic['_id'])
    for dic in list_cl2:
        index_cl2.append(dic['_id'])
    index_new = max(create_index(db.msgs),create_index(db.users))
    while index_new in index_cl1 or (index_new in index_cl2):
        index_new += 1
    return index_new

#set up for filtering
def apply_filtering(request, query):
    sort_key = "_id"
    sort_order = 1

    order_by = request.args.get("orderBy")
    limit_to_first = request.args.get("limitToFirst")
    limit_to_last = request.args.get("limitToLast")
    start_at = request.args.get("startAt")
    end_at = request.args.get("endAt")
    equal_to = request.args.get("equalTo")

    if order_by:
        order_by = order_by.strip('"')
        if order_by == "$key":
            sort_key = "_id"
        elif order_by == "$value" or order_by == "username":
            sort_key = "username"
        sort_order = ASCENDING

    if start_at:
        query[sort_key] = {"$gte": int(start_at)} if sort_key == "_id" else {"$gte": start_at}
    if end_at:
        query[sort_key] = {"$lte": int(end_at)} if sort_key == "_id" else {"$lte": end_at}
    if equal_to:
        equal_to = equal_to.strip("'")
        if sort_key == "_id":
            try:
                query[sort_key] = {"$eq": int(equal_to)}
            except ValueError:
                pass
        else:
            query[sort_key] = {"$eq": equal_to}

    return query, sort_key, sort_order

#set up for more function
def handle_collection_operations(collection, query, request):
    if request.method == 'GET':
        query, sort_key, sort_order = apply_filtering(request, query)

        cursor = collection.find(query)

        if sort_key and sort_order:
            cursor.sort(sort_key, sort_order)

        items = list(cursor)

        response_data = {}
        for item in items:
            new_item = {key: value for key, value in item.items() if key != "_id"}
            response_data[str(item["_id"])] = new_item

        return jsonify(response_data)

    elif request.method == 'POST':
        data = request.get_json()
        if "username" in data:
            data["_id"] = create_index(collection)
            collection.insert_one(data)
            return jsonify(data), 201
        else:
            return jsonify({"error": "Invalid data"}), 400

    elif request.method == 'PUT':
        data = request.get_json()
        if "_id" in data and "username" in data:
            collection.replace_one({"_id": data["_id"]}, data)
            return jsonify(data)
        else:
            return jsonify({"error": "Invalid data"}), 400

    elif request.method == 'PATCH':
        data = request.get_json()
        if "_id" in data and "username" in data:
            collection.update_one({"_id": data["_id"]}, {"$set": {"username": data["username"]}})
            return jsonify(data)
        else:
            return jsonify({"error": "Invalid data"}), 400

    elif request.method == 'DELETE':
        data = request.get_json()
        if "_id" in data:
            collection.delete_one({"_id": data["_id"]})
            return jsonify({"result": "Item deleted"})
        else:
            return jsonify({"error": "Invalid data"}), 400

    return jsonify({"error": "Invalid request method"}), 405

#set up for curl with detalied route
def handle_collection_operations_by_id(collection, query, request):
    if request.method == 'GET':

        query, sort_key, sort_order = apply_filtering(request, query)

        cursor = collection.find(query)

        if sort_key and sort_order:
            cursor.sort(sort_key, sort_order)

        items = list(cursor)

        response_data = {}
        for item in items:
            new_item = {key: value for key, value in item.items() if key != "_id"}
            response_data[str(item["_id"])] = new_item

        return jsonify(response_data)    

    elif request.method == 'POST':
        new_data = request.get_json()
        if "_id" not in new_data:
            new_data["_id"] = query["_id"]
        collection.update_one(query, {"$set": new_data}, upsert=True)
        return jsonify(new_data), 201

    elif request.method == 'PUT':
        new_data = request.get_json()
        collection.replace_one(query, new_data)
        return jsonify(new_data)

    elif request.method == 'PATCH':
        new_data = request.get_json()
        collection.update_one(query, {"$set": new_data})
        return jsonify(new_data)

    elif request.method == 'DELETE':
        result = collection.delete_one(query)
        return jsonify({"result": "Document deleted" if result.deleted_count > 0 else "Document not found"}), (200 if result.deleted_count > 0 else 404)

    return jsonify({"error": "Invalid request method"}), 405


#for users collection
@app.route('/users.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_users():
    users_collection = db.get_collection("users")
    query = {}
    return handle_collection_operations(users_collection, query, request)

@app.route('/users/<int:user_id>.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_users_by_id(user_id):
    users_collection = db.get_collection("users")
    query = {"_id": user_id}
    return handle_collection_operations_by_id(users_collection, query, request)

#for msgs collection
@app.route('/msgs.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_msgs(msg_id=None):
    msgs_collection = db.get_collection("msgs")
    query = {}
    return handle_collection_operations(msgs_collection, query, request)

@app.route('/msgs/<int:msg_id>.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_msgs_by_id(msg_id):
    msgs_collection = db.get_collection("msgs")
    query = {"_id": msg_id}
    return handle_collection_operations_by_id(msgs_collection, query, request)

#for histories collection
@app.route('/histories.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_histories(history_id=None):
    histories_collection = db.get_collection("histories")
    query = {}
    return handle_collection_operations(histories_collection, query, request)

@app.route('/histories/<int:history_id>.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_histories_by_id(history_id):
    histories_collection = db.get_collection("histories")
    query = {"_id": history_id}
    return handle_collection_operations_by_id(histories_collection, query, request)

#for root collection
@app.route('/.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_root(_id=None):
    root_collection = db.get_collection("root")
    query = {}
    return handle_collection_operations(root_collection, query, request)

@app.route('/<int:root_id>.json', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def handle_root_by_id(root_id):
    root_collection = db.get_collection("root")
    query = {"_id":root_id}
    return handle_collection_operations_by_id(root_collection, query, request)

# home page and message form
@app.route('/', methods=['GET', 'POST'])
def home():
    formType = request.form.get("formType", "")
    if formType == 'add_form':
        username = request.form['name']
        message = request.form['message']
        #save messages, usernames and time
        # cnt_msgs = create_index(msgs)
        cnt = create_index_2(db.users,db.msgs)
        db.msgs.insert_one({'_id':cnt,'message': message, 'username': username, 'created_at': datetime.now()})
        #save usernames
        # cnt_users = create_index(users)
        db.users.insert_one({'_id':cnt,'username': username})
        #update all data to root
        user_data = db.users.find()
        msg_data=db.msgs.find()
        user_documents = [json.loads(json.dumps(document, default=str)) for document in user_data]
        db.root.update_one({"_id":"users"}, {"$set": {"users_list": user_documents}}, upsert=True)
        msg_documents = [json.loads(json.dumps(document, default=str)) for document in msg_data]
        db.root.update_one({"_id":"msgs"}, {"$set": {"msgs_list": msg_documents}}, upsert=True)
        return redirect(url_for('home'))
    elif formType == "delete_form":
        messageId = request.form.get("messageId", "")
        db.msgs.delete_one({"_id": int(messageId)})
        db.users.delete_one({"_id": int(messageId)})
        #update all data to root
        user_data = db.users.find()
        msg_data=db.msgs.find()
        user_documents = [json.loads(json.dumps(document, default=str)) for document in user_data]
        db.root.update_one({"_id":"users"}, {"$set": {"users_list": user_documents}}, upsert=True)
        msg_documents = [json.loads(json.dumps(document, default=str)) for document in msg_data]
        db.root.update_one({"_id":"msgs"}, {"$set": {"msgs_list": msg_documents}}, upsert=True)    
        return redirect(url_for('home'))
    elif formType == "edit_form":
        messageId = request.form.get("messageId", "")
        message = request.form['message']
        db.msgs.update_one({"_id": int(messageId)}, {"$set": {"message": message}})
        #update all data to root
        user_data = db.users.find()
        msg_data=db.msgs.find()
        user_documents = [json.loads(json.dumps(document, default=str)) for document in user_data]
        db.root.update_one({"_id":"users"}, {"$set": {"users_list": user_documents}}, upsert=True)
        msg_documents = [json.loads(json.dumps(document, default=str)) for document in msg_data]
        db.root.update_one({"_id":"msgs"}, {"$set": {"msgs_list": msg_documents}}, upsert=True)
        return redirect(url_for('home'))
    elif formType == "save_form":
        messageId = request.form.get("messageId", "")
        his_msg = list(db.msgs.find({"_id":int(messageId)}))
        his_cnt = create_index(db.histories)
        db.histories.insert_one({'_id':his_cnt,'history':his_msg})
        db.msgs.delete_one({"_id": int(messageId)})
        #update all data to root
        user_data = db.users.find()
        msg_data=db.msgs.find()
        his_data=db.histories.find()
        user_documents = [json.loads(json.dumps(document, default=str)) for document in user_data]
        db.root.update_one({"_id":"users"}, {"$set": {"users_list": user_documents}}, upsert=True)
        msg_documents = [json.loads(json.dumps(document, default=str)) for document in msg_data]
        db.root.update_one({"_id":"msgs"}, {"$set": {"msgs_list": msg_documents}}, upsert=True) 
        his_documents = [json.loads(json.dumps(document, default=str)) for document in his_data]
        db.root.update_one({"_id":"histories"}, {"$set": {"histories_list": his_documents}}, upsert=True) 
        return redirect(url_for('home'))
    messages = list(db.msgs.find())
    histories = list(db.histories.find())
    return render_template('index.html', messages=messages, histories=histories)

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

@socketio.on('request_history')
def send_history():
    histories = list(db.histories.find())
    messages = []
    for history in histories:
        messages.extend(history['history'])
    emit('history', messages)


if __name__ == '__main__':
    socketio.run(app, host='localhost', debug=True)

