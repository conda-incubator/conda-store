from flask import Blueprint, render_template, request

app_auth = Blueprint("auth", __name__, template_folder="templates")


@app_auth.route('/login/', methods=['GET'])
def get_login():
    return render_template('login.html')


@app_auth.route('/login/', methods=['POST'])
def post_login():
    username = request.form['username']
    password = request.form['password']
    return f'username={username} password={password}'
