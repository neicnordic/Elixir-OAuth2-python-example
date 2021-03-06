#!/usr/bin/env python
from flask import Flask, abort, request
from uuid import uuid4
import requests
import requests.auth
import urllib
CLIENT_ID = 'client' # Fill this in with your client ID
CLIENT_SECRET = 'secret' # Fill this in with your client secret
REDIRECT_URI = "http://localhost:8080"


def user_agent():
    return "what should I return here?"

def base_headers():
    return {"User-Agent": user_agent()}


app = Flask(__name__)
@app.route('/app')
def homepage():
    text = '<a href="%s">Authenticate with elixir</a>'
    return text % make_authorization_url()


def make_authorization_url():
    # Generate a random string for the state parameter
    # Save it for use later to prevent xsrf attacks
    state = str(uuid4())
    save_created_state(state)
    params = {"client_id": CLIENT_ID,
              "response_type": "code",
              "state": state,
              "redirect_uri": REDIRECT_URI,
              "duration": "temporary",
              "scope": 'profile email'}
    url = "https://perun.elixir-czech.cz/oidc/authorize?" + urllib.urlencode(params)
    return url


# You may want to store valid states in a database or memcache.
# But that is beyond this small test
def save_created_state(state):
    pass
def is_valid_state(state):
    return True

@app.route('/')
def elixir_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        # Uh-oh, this request wasn't started by us!
        abort(403)
    code = request.args.get('code')
    access_token = get_token(code)
    # Note: In most cases, you'll want to store the access token, in, say,
    # a session for use in other parts of your web app.
    return "Your elixir data is: %s" % get_userdetails(access_token)

def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": REDIRECT_URI}
    headers = base_headers()
    response = requests.post("https://perun.elixir-czech.cz/oidc/token",
                             auth=client_auth,
                             headers=headers,
                             data=post_data)
    token_json = response.json()
    return token_json["access_token"]


def get_userdetails(access_token):
    headers = base_headers()
    headers.update({"Authorization": "bearer " + access_token})
    response = requests.get("https://perun.elixir-czech.cz/oauth/rpc/json/oidcManager/userinfo",
                            headers=headers)
    me_json = response.json()
    return me_json['name'] + ', ' + me_json['email']


if __name__ == '__main__':
    app.run(debug=True, port=8080)
