
#requirements
pip install Flask
pip install flask_socketio
pip install flask_session
pip install flask_login
pip install pymongo
pip install eventlet
pip install gevent

##Run the script
##The app should run on either of the two hosts #prefer 127.0.0.1:5000

http://127.0.0.1:5000/
http://localhost:5000/

####
#Two ways to run in commandline
##1 HTTP 
###need install brew and http
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install httpie  
#then directly run http commands in another commandline after installation
http GET http://localhost:5000/users.json  

##2 curl 
	#cd to flask app directory first
	export FLASK_APP=app.py #replace the name
	flask run
	#open a new terminal for curl command
	curl -X GET 'http://localhost:5000/users.json'

##############
# curl commands for test (might need to replace the id)
###GET
##0 GET root
curl -X GET 'http://localhost:5000/.json'
##1 GET all users:
curl -X GET 'http://localhost:5000/users.json'
##2 GET users with "_id" greater than or equal to 10002:
curl -X GET 'http://localhost:5000/users.json?orderBy="$key"&startAt=10002' 
##3 GET users with "_id" less than or equal to 10002:
curl -X GET 'http://localhost:5000/users.json?orderBy="$key"&endAt=10002'
##4 GET users with "_id" equal to 10002:
curl -X GET 'http://localhost:5000/users.json?orderBy="$key"&equalTo=10002' 

##POST
curl -X POST -H "Content-Type: application/json" -d '{"username":"user_curl1"}' http://localhost:5000/users.json
##POST other info for a user
curl -X POST -H "Content-Type: application/json" -d '{"age":20}' http://localhost:5000/users/10005.json

##PUT
curl -X PUT -H "Content-Type: application/json" -d '{"_id": 10005, "username": "updated_user1"}' http://localhost:5000/users.json

##PATCH
curl -X PATCH -H "Content-Type: application/json" -d '{"_id": 10005, "username": "updated_user1"}' http://localhost:5000/users.json

##DELETE
curl -X DELETE -H "Content-Type: application/json" -d '{"_id": 10005}' http://localhost:5000/users.json

