from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from flask import Flask, request, jsonify

import ansible_runner

app = Flask(__name__)


app.config["DEBUG"] = True


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




#app.config['SECRET_KEY'] = "supersecret"

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
