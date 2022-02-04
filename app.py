from flask import Flask, jsonify, request

#importing sqlalchemy ORM
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float

from flask_marshmallow import Marshmallow

from flask_jwt_extended import JWTManager, jwt_required, create_access_token

from flask_mail import Mail, Message

import os




# app configs
app = Flask(__name__) # instantiating app, this app will take its name from the script.
basedir = os.path.abspath(os.path.dirname(__file__)) # path of application file, need for putting the db file in the same folder as application

db_name = 'planets.db'
db_path = os.path.join(basedir, db_name)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{ db_path }" # config for setting db uri

app.config['JWT_SECRET_KEY'] = 'super-secret' # change this IRL

app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'ac721d4f4ba3d2'#os.environ['MAIL_USERNAME'] #
app.config['MAIL_PASSWORD'] = 'c33a80154568b4'#os.environ['MAIL_PASSWORD'] #
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

#init db before using it

db = SQLAlchemy(app)

# init marshmallow
marshmallow = Marshmallow(app)

jwt = JWTManager(app)

mail = Mail(app)

# flask cli, allows you to run arbitrary command against your app

@app.cli.command('db_create') # name of command
def db_create():
    db.create_all() # create the db
    print('Databse created')

@app.cli.command('db_seed') # name of command
def db_seed():
    
    mercury = Planet(planet_name='Mercury',
                    planet_type='Class D',
                    home_star='Sun',
                    mass=3.25e23,
                    radius=1516,
                    distance=35.98e6)

    venus = Planet(planet_name='venus',
                    planet_type='Class E',
                    home_star='Sun',
                    mass=3.25e23,
                    radius=1516,
                    distance=35.98e6)

    earth = Planet(planet_name='earth',
                    planet_type='Class M',
                    home_star='Sun',
                    mass=3.25e23,
                    radius=1516,
                    distance=35.98e6)

    db.session.add(mercury) # adding to db as records
    db.session.add(venus) # adding to db as records
    db.session.add(earth) # adding to db as records

    test_user = User(first_name='William', last_name='Herschel', email='test@test.com', password='123')
    db.session.add(test_user)

    db.session.commit() # save your changes

    print('Databse seed')


@app.cli.command('db_drop') # name of command
def db_drop():
    db.drop_all() # getting rid of the db file
    print('Databse droped')






# using endpoints
"""
 An endpoint is really just a URL,
 that's going to be processed by your application
"""

@app.route('/') # root path of our app
def hello_world():
    return 'Hello World!'

#returning json
@app.route('/json_test')
def test_json():
    res = {
        'app' : __name__,
        'filename': __file__,
        'basedir': basedir,
        'project': 'The Planetary API',
        'author' : 'Vaibhav Kumar',
        'endpoints': 3,
        'db_uri': f"sqlite:///{ db_path }"
    }

    # return jsonify(res)
    return res # same as above statement

@app.route('/simple')
def simple():
    # return '/simple endpoint'
    return jsonify(message='This is a simple endpoint', endpoint='/simple')

# respnse with status code
@app.route('/not-found')
def not_found():
    """
    returns a 404 status
    """
    return {'msg': 'This is a not found endpoint'}, 404
    # return jsonify(msg = 'This is a not found endpoint'), 404

# url parameters
@app.route('/params')
def parameters():
    """
    using query string params
    """
    name = request.args.get('name') # name of parameter passed
    # name = request.args['name'] # name of parameter passed
    age = request.args.get('age')

    if name and age:
        if int(age) < 18:
            return {"msg": f"Sorry {name}, you are not old enough"}, 401 # Not authorized
            # return jsonify(msg= f"Sorry {name}, you are not old enough"), 401
        else:
            return {"msg": f"Welcome {name}!"}
            # return jsonify(msg= f"Welcome {name}!")
    else:
        return {'msg': "Please provide name and age"}, 400


@app.route('/urlvars/<string:name>/<int:age>') # endpoints with vars, missing vars will return 404 by default
def urlvars(name: str, age: int): # variable rule matching
    if age < 18:
        return {"msg": f"Sorry {name}, you are not old enough"}, 401 # Not authorized
        # return jsonify(msg= f"Sorry {name}, you are not old enough"), 401
    else:
        return {"msg": f"Welcome {name}!"}
        # return jsonify(msg= f"Welcome {name}!")

@app.route('/planets', methods=['GET']) # responds only to GET reqs
def planets():
    planets_list = Planet.query.all() # list of all planets

    # return {'planets' : planets_list} # error: Object of type Planet is not JSON serializable

    """
    The process of converting an object into a textual representation
    of that object is called serialization.
    'flask-marshmallow' - serialize a collection of SQLAlchemy data rows
    """

    result = planets_schema.dump(planets_list) # serializing planet_list
    
    # result is a list of dictionary containing field: field_value

    # following all are valid response but in different format.

    return jsonify(result)
    # return str(result) # return text response
    # return {'planets': result}


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first() # no need to serialize
    if test:
        return jsonify(msg='email already exists'), 409 # conflict
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return jsonify(msg = 'User registered successfully.'), 201 # created a new record


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()

    if test: # login successful
        # send jwt_token
        access_token = create_access_token(identity=email) # unique indentifier of ther user

        return jsonify(msg="login successful!", access_token=access_token)
    else:
        return jsonify(msg='Bad email or password'), 401 # access denied


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your planetary API password is " + user.password, sender="vk@planetary-api.com", recipients=[email])
        mail.send(msg)
        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message="That email doesn't exist"), 401 # unauthorized


@app.route('/planet/<int:planet_id>', methods=['GET'])
def planet_details(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        # return jsonify(result)
        return result # as a single planet is serialized as a dict
    else:
        return jsonify(message="That planet doesn't exist"), 404

# CRUD endpoints

@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message='There already a planet by that name'), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']

        new_planet = Planet(planet_name = planet_name,
            planet_type=planet_type,
            home_star=home_star,
            mass=mass,
            radius=radius,
            distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You added a planet", details=planet_schema.dump(new_planet)), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    planet_id = int(request.form.get('planet_id'))
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        if request.form.get('planet_name'):
            planet.planet_name = request.form.get('planet_name')
        
        if request.form.get('planet_type'):
            planet.planet_type = request.form.get('planet_type')
        
        if request.form.get('home_star'):
            planet.home_star = request.form.get('home_star')
        
        if request.form.get('mass'):
            planet.mass = float(request.form.get('mass'))

        if request.form.get('radius'):
            planet.radius = float(request.form.get('radius'))
        
        if request.form.get('distance'):
            planet.distance = float(request.form.get('distance'))
        db.session.commit() # for saving changes
        return jsonify(message="Planet details updated"), 202
    else:
        return jsonify(message="Planet Not Found"), 404

@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required
def remove_planet(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message='Planet deleted'), 202
    else:
        return jsonify(message='No planet by that id!'), 404


# db models

class User(db.Model):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

# class for marshmallow

class UserSchema(marshmallow.Schema):
    class Meta:
        fields = ('user_id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(marshmallow.Schema):
    class Meta:
        fields = ('planet_id',
        'planet_name',
        'planet_type',
        'home_star',
        'mass',
        'radius',
        'distance')

user_schema = UserSchema() # for one record
users_schema = UserSchema(many=True) # for a collection of records

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)







# driver code

if __name__ == "__main__":
    app.run(debug=True)