#from ansible_runner import Runner, RunnerConfig

# flask includes/http/jwt includes
import jwt
from flask_swagger_ui import get_swaggerui_blueprint
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import Flask, request, jsonify

import datetime
import yaml

import ansible_runner

app = Flask(__name__)

auth = HTTPBasicAuth()
users = {
        "foo":  generate_password_hash("foobar"),
        "bar": generate_password_hash("foobar") }


app.config["DEBUG"] = True

#parser = reqparse.RequestParser()
#parser.add_argument('name', help='Specify your name')


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/api/v1/whoami", methods = ['GET'])
def test1():
    """ get a username from a get request and return the username
        as a json structure """
    user = request.args.get('user')
    return jsonify({"username": user})


@app.route('/api/v1/version', methods=['GET'])
def get_test2():

    hostname = 'localhost'
    if request.args.get('hostname'):
        hostname = request.args.get('hostname')

    rc = ansible_runner.RunnerConfig(private_data_dir='./',
            inventory='hosts', # inventory file
            playbook='get_version.yml', # playbook to run
            rotate_artifacts=5,  # number of artificat runs to keep on disk
            extravars={"device": hostname}) # extra vars, similar to passing -e on the command line
                                            # in json format

    rc.prepare()
    r = ansible_runner.Runner(config=rc)
    r.run()

    # get return data from the ansible run
    returndata = r.get_fact_cache(hostname)["returnvar"]
    return jsonify({hostname: {'version': returndata}})


def token_required(f):
    """ this is the wrapper to make a function require a token. I have updates this
        function so that it should take either a regular "get" or accept the token
        in the body like swagger will send it. Any function that requires a token
        should have this decorator applied to it"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        client_ip = flask.request.environ['REMOTE_ADDR']

        #print(flask.request.headers)

        if 'Authorization' in flask.request.headers:
            headers = flask.request.headers
            bearer = headers.get('Authorization')
            if "Bearer" in bearer:
                token = bearer.split()[1]

        if token == None:
            token = flask.request.args.get('token')

        if not token:
            message = "Token is missing !!"
            error_message = """Token is missing {} {} {}""".format(f.__name__, "unknown", client_ip)
            logging.error(error_message)
            return flask.jsonify({'message' : error_message}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms=['HS256', ])

        except Exception as e:
            error_message = """Token is invalid {} {} {}""".format(f.__name__, "unknown", client_ip)
            logging.error(error_message)

            return flask.jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the original function
        error_message = """AUTH success {} {} {}""".format(f.__name__, data["user"], client_ip)
        logging.info(error_message)


        return  f(*args, **kwargs)

    return decorated



# validate password
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username



@app.route('/login')
@auth.login_required
def login():

    token = jwt.encode({'user': auth.current_user(), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=datahash["jwt_timeout"])}, str(app.config['SECRET_KEY']))
    client_ip = request.environ['REMOTE_ADDR']
    error_message = """login/auth {} {}""".format(auth.current_user(), client_ip)
    #logging.info(error_message)

    return jsonify({'token': token})




def getdatahash():
    """ this function laods in key/value pairs from a file
        notably the username/password for the database """

    #passfile=os.path.expanduser('~/.ansiblesecrets_api')
    #fileIN = open(passfile, "r")
    #vaultpassword = fileIN.readline().rstrip()

    cfgfile = "arguments.yml"
    #loader = DataLoader()

    #default_vault_ids = C.DEFAULT_VAULT_IDENTITY_LIST
    #vault_ids = default_vault_ids
    #loader.set_vault_secrets([('default',VaultSecret(vaultpassword.encode('utf-8')))])
    #data = loader.load_from_file(cfgfile)
    with open(cfgfile, 'r') as file:
        data = yaml.safe_load(file)
    return data



datahash = getdatahash()
print(datahash)

app.config['SECRET_KEY'] = datahash["jwt_secret"]

SWAGGER_URL = "/swagger" 
API_URL = "/static/swagger.yml"
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "mysuperrunner"
    }
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
