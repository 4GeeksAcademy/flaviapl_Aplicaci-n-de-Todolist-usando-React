"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
# from models import Person

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

# Add all endpoints form the API with a "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object

app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response



@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)         #valore = request.json.get("chiave" della richiesta HTTP che vuoi estrarre, valore_default, Se la chiave non esiste, restituisce questo valore invece di dare errore (di default è None )
    password = request.json.get("password", None)   
    user = User.query.filter_by(email = email).first()      #cerca un utente nel database che abbia l'email fornita
    print(user)
    if user is None :                                             #se l'email non esiste nel database, si verifica un errore con user.password.
        return jsonify({"msg": "Bad email or password"}), 401
    if password != user.password :                              #se la pwd inserita dall'utente è diversa dalla pwd nel database di User da errore(lo user deve essere giusto sennó non trova niente)
        return jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=email)   #se l'email e la password ok, si genera un token JWT che conterrà l'identità dell'utente (l'email in questo caso)
    return jsonify(access_token=access_token)


@app.route("/private", methods=["GET"])
@jwt_required()                              #protegge la rotta, solo chi ha un token valido accede
def private_route():
    current_user = get_jwt_identity()       #recupera l'identità dell'utente che è stata salvata nel token JWT al momento del login
    return jsonify(logged_in_as = current_user), 200    #resituisce loggato come e la mail dell'utente



@app.route("/signup", methods=["POST"])
def signup():
    email = request.json.get ("email", None )          #accedo alla mail proveniente dalla richiesta 
    password = request.json.get ("password", None)      #accedo alla pwd proveniente dalla richiesta
    print(email and password)

    if not email or not password :
        return jsonify({"message": "email and password required"}), 400

    new_user = User(email = email, password = password, is_active = True )     # crea nuovo utente in User e l'email e = alla email inserita nel POST e la PWD anche, devo definite is_active perchè il modello User lo richiede.
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "user succesfully created"}), 201               #201 = Created






# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
