import json
from time import sleep

import incoming_message_handler
from flask import Flask, abort, request
from flask.wrappers import Response
from postgres_api import Fetchpostgres
from postgresconf.config import config as pconfig

params = pconfig()
print("Trying to connect to the postgres backend.", end="")
for _ in range(100):
    try:
        print(".", end=".")
        fetcher = Fetchpostgres(params)
        print()
        print("Postgres connection established.")
        break
    except:
        pass
        print()
        print("Waiting for the postgres to load!")
    sleep(3)

incoming_message_handler.fetcher = fetcher

app = Flask(__name__)


@app.before_request
def abortion_method():
    # use the ip for future patches
    ip = str(request.environ.get("HTTP_X_REAL_IP", request.remote_addr))
    if (request.method == "GET") or (request.args != {}):
        abort(403)


@app.route("/", methods=["POST"])
def index():
    msg = request.get_json(force=True)
    msg_str = json.dumps(msg)
    msg_http_code = str(msg)
    print(msg_str)
    print(msg_http_code)
    incoming_message_handler.manage_messages(msg)
    return Response("Ok", status=200)


def main():
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
