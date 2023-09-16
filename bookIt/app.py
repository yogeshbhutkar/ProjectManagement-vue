from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_api import status
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, JWTManager
from flask_cors import CORS
import uuid
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = '4ddfebb964f84323a8fb8a19234637bc'
jwt = JWTManager(app)
CORS(app)

db=SQLAlchemy(app)

# Ensuring FOREIGN KEY
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)

class Users(db.Model):
    _id=db.Column(db.String(50), primary_key=True)
    username=db.Column(db.String(25), nullable=False)
    password=db.Column(db.String(25), nullable=False)
    admin_status=db.Column(db.Boolean, nullable=True, default=False)
    
    def __repr__(self) -> str:
        return f"{self._id} - {self.username}"

class Theatre(db.Model):
    _id=db.Column(db.String(50), primary_key=True)
    name=db.Column(db.String(25), nullable=False)
    place=db.Column(db.String(25), nullable=False)
    capacity=db.Column(db.String(25), nullable=False)

    def __repr__(self) -> str:
        return f"{self._id} - {self.name}"

class Show(db.Model):
    _id=db.Column(db.String(50), primary_key=True)
    name=db.Column(db.String(25), nullable=False)
    rating=db.Column(db.String(5), nullable=True)
    tags=db.Column(db.String(25), nullable=False)
    ticketPrice=db.Column(db.Integer, nullable=False)
    theatre_id=db.Column(db.String(50), db.ForeignKey('theatre._id'))
    theatre = db.relationship("Theatre", backref=db.backref("theatre", uselist=False))


@app.route('/')
def initialize():
    return "<p>API for BookIT.</p>"

@app.route(os.environ['COMMON_ADDR']+"/")
# @jwt_required()
def getAllShows():
    try:
        shows = Show.query.all()
        allShows = []
        
        for item in shows:
            # venueName = Theatre.query.filter_by(_id=item.theatre_id).first()
            allShows.append({'_id':item._id, 'name': item.name, 'rating': item.rating, 'tags': item.tags, 'ticketPrice': item.ticketPrice, 'theatre_id': item.theatre_id})

        return jsonify({"data": allShows}), status.HTTP_200_OK
    except Exception as e:
        print(e)
        return jsonify(error=True), status.HTTP_401_UNAUTHORIZED
    

@app.route(os.environ['COMMON_ADDR']+'/signup', methods=["POST"])
def signup():
    try:
        if request.method=="POST":
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            id = uuid.uuid4().hex
            user = Users(_id=id, username=username, password=generate_password_hash(password))
            refresh = create_refresh_token(identity=user._id)
            access = create_access_token(identity=user._id)
            db.session.add(user)
            db.session.commit()
            return jsonify({'user': {
                'refresh': refresh,
                'access': access,
                'username': username,
                'password': password
            }}), status.HTTP_200_OK
    except Exception as e:
        print(e)
        return jsonify(error=True), status.HTTP_401_UNAUTHORIZED

@app.route(os.environ['COMMON_ADDR']+'/login', methods=["POST"])
def login():
    if request.method=="POST":
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            user = Users.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                refresh = create_refresh_token(identity=user._id)
                access = create_access_token(identity=user._id)
                return jsonify({'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': username,
                    'password': password
                }})
            return jsonify(error="Invalid Credentials"), status.HTTP_401_UNAUTHORIZED
        except Exception as e:
            print(e)
            return jsonify(error=True)
        
@app.route(os.environ['COMMON_ADDR']+'/theatres', methods=["GET", "POST", "DELETE"])
def theatresCRUD():
    if request.method=="POST":
        try:
            data=request.get_json()
            name=data.get('name')
            place=data.get('place')
            capacity=data.get('capacity')
            record = Theatre(_id=uuid.uuid4().hex, name=name, place=place, capacity=capacity)
            db.session.add(record)
            db.session.commit()
            return jsonify({"data":[
                {
                    "_id":record._id,
                    "name":record.name,
                    "place": record.place,
                    "capacity": record.capacity
                }
            ]})
        except Exception as e:
            print(e)
            return jsonify(error=True)
    
    elif request.method=="GET":
        try:
            theatres = Theatre.query.all()
            allTheatres = []
            
            for item in theatres:
                allTheatres.append({'_id':item._id, 'name': item.name, 'place': item.place, 'capacity': item.capacity})
            
            return jsonify({"data": allTheatres})
        except Exception as e:
            print(e)    
            return jsonify(error=True)

    elif request.method=="DELETE":
        try:
            data=request.get_json()
            Theatre.query.filter_by(_id = data.get('_id')).delete()
            db.session.commit()
            return jsonify(error=False)
        except Exception as e:
            print(e)
            return jsonify(error=True)

@app.route(os.environ['COMMON_ADDR']+'/theatres/<string:_id>', methods=["GET", "PATCH"])
def getSingleTheatre(_id):
    if request.method=="GET":
        try:
            theatre = Theatre.query.filter_by(_id=_id).first()
            if (theatre):
                return jsonify(_id=theatre._id, name=theatre.name, place=theatre.place, capacity=theatre.capacity)
            else:
                return jsonify(error='No such id found')
        except Exception as e:
            print(e)
            return jsonify(error=True)
    elif request.method=="PATCH":
        try:
            data=request.get_json()
            theatre = Theatre.query.filter_by(_id=_id).first()
            if (data.get('name')):
                theatre.name=data.get('name')
            if (data.get('place')):
                theatre.place=data.get('place')
            if (data.get('capacity')):
                theatre.capacity=data.get('capacity')
            db.session.commit()
            return jsonify(_id=theatre._id, name=theatre.name, place=theatre.place, capacity=theatre.capacity)
        except Exception as e:
            print(e)
            return jsonify(error=True)
            
@app.route(os.environ['COMMON_ADDR']+'/theatres/<string:_id>/shows', methods=["GET", "POST", "DELETE"])
def showManagement(_id):
    if request.method=="POST":
        try:
            data=request.get_json()
            name=data.get('name')
            rating=data.get('rating')
            tags=data.get('tags')
            ticketPrice=data.get('ticketPrice')
            theatre_id=_id
            record = Show(_id=uuid.uuid4().hex, name=name, rating=rating, tags=tags, ticketPrice=ticketPrice, theatre_id=theatre_id)
            db.session.add(record)
            db.session.commit()
            return jsonify({"data":[
                {
                    "_id":record._id,
                    "name":record.name,
                    "tags": record.tags,
                    "ticketPrice": record.ticketPrice,
                    "theatre_id": record.theatre_id
                }
            ]})
        except Exception as e:
            print(e)
            return jsonify(error=True)
    
    elif request.method=="GET":
        try:
            shows = Show.query.filter_by(theatre_id=_id)
            allShows = []
            
            for item in shows:
                allShows.append({'_id':item._id, 'name': item.name, 'rating': item.rating, 'tags': item.tags, 'ticketPrice': item.ticketPrice, 'theatre_id': item.theatre_id})
            
            return jsonify({"data": allShows})
        except Exception as e:
            print(e)    
            return jsonify(error=True)        
    
    elif request.method=="DELETE":
        try:
            data=request.get_json()
            Show.query.filter_by(_id = data.get('_id')).delete()
            db.session.commit()
            return jsonify(error=False)
        except Exception as e:
            return jsonify(error=True)

@app.route(os.environ['COMMON_ADDR']+'/theatres/<string:TheatreId>/shows/<string:ShowId>', methods=["GET", "PATCH"])
def manageSingleShow(TheatreId, ShowId):
    if request.method=="GET":
        try:
            show = Show.query.filter_by(_id=ShowId).first()
            if (show):
                return jsonify(_id=show._id, name=show.name, rating=show.rating, tags=show.tags, theatre_id=show.theatre_id, ticketPrice=show.ticketPrice)
            else:
                return jsonify(error='No such id found')
        except Exception as e:
            print(e)
            return jsonify(error=True)
    elif request.method=="PATCH":
        try:
            data=request.get_json()
            show = Show.query.filter_by(_id=ShowId).first()
            if (data.get('name')):
                show.name=data.get('name')
            if (data.get('rating')):
                show.rating=data.get('rating')
            if (data.get('tags')):
                show.tags=data.get('tags')
            if (data.get('theatre_id')):
                show.theatre_id=data.get('theatre_id')
            if (data.get('ticketPrice')):
                show.ticketPrice=data.get('ticketPrice')
            db.session.commit()
            return jsonify(_id=show._id, name=show.name, rating=show.rating, tags=show.tags, theatre_id=show.theatre_id, ticketPrice=show.ticketPrice)
        except Exception as e:
            print(e)
            return jsonify(error=True)

if __name__=="__main__":
    app.run(debug=True, port=8000)
