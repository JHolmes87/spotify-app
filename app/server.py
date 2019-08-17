from flask import Flask, render_template, request, url_for, redirect, session
import spotify.authenticator
import spotify.api
import requests
import os
from user import User

app = Flask(__name__)
app.secret_key = os.urandom(16)

def dict_to_string(dic):
    string = ''
    for key, val in dic.items():
        string += "{}: {}\n".format(key, val)
    return string

# Checks if request was successful
def successful_request(json_response):
    if json_response.get('error'):
        return False
    else:
        return True

# Finds current user based on browser session
# Returns current User (User) or None if the session hash is empty
def current_user():
    return User(id = session['user_id']).find()

@app.route('/')
def index():
    return render_template('index.html', title='Spotify App')

@app.route('/launch_spotify_authentication')
def launch_spotify_authentication():
    client_id = os.environ['SPOTIFY_CLIENT_ID']
    redirect_uri = url_for('spotify_auth_landing', _external = True)
    scope = 'user-read-private user-read-email'
    state = 'dumm'
    return redirect(spotify.authenticator.user_login_url(client_id, redirect_uri, scope, state))

@app.route('/spotify_auth_landing/')
def spotify_auth_landing():
    if request.args.get('state') == 'dumm':
        authorization_code = request.args.get('code')

        # Get refresh and access tokens
        redirect_uri = url_for('spotify_auth_landing', _external = True)
        response = spotify.authenticator \
            .get_access_credentials(authorization_code, redirect_uri, os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET'])
        access_token = response.get('access_token')
        # Get user profile
        profile_info = spotify.api.get_current_profile(access_token).json()
        if successful_request(profile_info):
            # Find user in database with this profile info
            user_instance = User({'display_name': profile_info.get('display_name'), 'spotify_id': profile_info.get('id'), 'email': profile_info.get('email')})
            user = user_instance.find()
            # if not found, set as a new user
            if not user:
                user = user_instance
                user.save()
            # Update the access credentials
            user.save_access_credentials(response)
            # store user id in session
            session['user_id'] = user.id
            return render_template('index.html', title='Success', response_content=dict_to_string(user.params))
        else:
            return render_template('index.html', title='Fail', response_content=dict_to_string(profile_info))
    else:
        print('Wrong state!! error; state= ' + request.args.get('state') )
        return render_template('index.html', title='Failure :(', response_content=str(request.args))

@app.route('/my_profile')
def my_profile():
    # Find user
    user = current_user()
    if not user:
        return render_template('index.html', title='Failed Again :(', response_content='im hungry. also, session is => {}'.format(session['user_id']))

    # send request to spotify to get current profile information
    response = spotify.api.get_current_profile(user.get_access_token()).json()

    return render_template('index.html', title='My Profile', response_content=dict_to_string(response))

@app.route('/song_info')
def song_info(song_title):


# Launch App
if __name__ == "__main__":
	try:
		app.run(host='0.0.0.0', port=8080, debug=True)
	except:
		print("Server Crashed :(")