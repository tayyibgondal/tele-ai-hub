from flask import Flask, render_template, redirect, send_from_directory, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from config import Config
import noma_ee_dataset_generation, noma_se_dataset_generation, network_simulator
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Page
@app.route("/")
# @login_required
def home():
    return render_template('home.html')

# @app.route("/noma_ee_dataset_generation", methods=['GET', 'POST'])
# # @login_required 
# def NOMA_EE():
#     if request.method == 'POST':
#         # Get user inputs from the form
#         rows_of_data = request.form['rows_of_data']
#         temperature = request.form['temperature']
#         bandwidth = request.form['bandwidth']
#         simulation_area_size = request.form['simulation_area_size']
#         n_antennas = request.form['n_antennas']
#         mc = request.form['mc']

#         # Call the function from your notebook
#         result = noma_ee_dataset_generation.main(rows_of_data, temperature, bandwidth, simulation_area_size, n_antennas, mc)

#         # Pass the result to the template
#         return render_template('NOMA_EE.html', result=result)
#     return render_template('NOMA_EE.html')

@app.route("/noma_ee_dataset_generation", methods=['GET', 'POST'])
# @login_required
def NOMA_EE():
    if request.method == 'POST':
        # Get user inputs from the form
        rows_of_data = request.form['rows_of_data']
        temperature = request.form['temperature']
        bandwidth = request.form['bandwidth']
        simulation_area_size = request.form['simulation_area_size']
        n_antennas = request.form['n_antennas']
        mc = request.form['mc']

        # Call the function from your notebook
        result = noma_ee_dataset_generation.main(rows_of_data, temperature, bandwidth, simulation_area_size, n_antennas, mc)

        # Save the result as a JSON file in the static directory
        filename = "NOMA_EE_dataset.json"
        filepath = "static/" + filename  # Path to the static directory
        with open(filepath, 'w') as f:
            json.dump(result, f) # Changed from jsonfiy to json.dump

        # Pass the result to the template
        return render_template('NOMA_EE.html', result=result)

    return render_template('NOMA_EE.html')


@app.route('/NOMA_EE_dataset.json')
def serve_json_NOMA_EE():
    return send_from_directory('static', 'NOMA_EE_dataset.json')


# @app.route("/noma_se_dataset_generation", methods=['GET', 'POST'])
# # @login_required 
# def NOMA_SE():
#     if request.method == 'POST':
#         # Get user inputs from the form
#         rows_of_data = request.form['rows_of_data']
#         temperature = request.form['temperature']
#         bandwidth = request.form['bandwidth']
#         simulation_area_size = request.form['simulation_area_size']
#         n_antennas = request.form['n_antennas']
#         mc = request.form['mc']

#         # Call the function from your notebook
#         result = noma_se_dataset_generation.main(rows_of_data, temperature, bandwidth, simulation_area_size, n_antennas, mc)

#         # Pass the result to the template
#         return render_template('NOMA_SE.html', result=result)
#     return render_template('NOMA_SE.html')

@app.route("/noma_se_dataset_generation", methods=['GET', 'POST'])
# @login_required
def NOMA_SE():
    if request.method == 'POST':
        # Get user inputs from the form
        rows_of_data = request.form['rows_of_data']
        temperature = request.form['temperature']
        bandwidth = request.form['bandwidth']
        simulation_area_size = request.form['simulation_area_size']
        n_antennas = request.form['n_antennas']
        mc = request.form['mc']

#         # Call the function from your notebook
        result = noma_se_dataset_generation.main(rows_of_data, temperature, bandwidth, simulation_area_size, n_antennas, mc)

        # Save the result as a JSON file in the static directory
        filename = "NOMA_SE_dataset.json"
        filepath = "static/" + filename  # Path to the static directory
        with open(filepath, 'w') as f:
            json.dump(result, f) # Changed from jsonfiy to json.dump

        # Pass the result to the template
        return render_template('NOMA_SE.html', result=result)

    return render_template('NOMA_SE.html')


@app.route('/NOMA_SE_dataset.json')
def serve_json_NOMA_SE():
    return send_from_directory('static', 'NOMA_SE_dataset.json')

@app.route("/ee_dataset_generation", methods=['GET', 'POST'])
# @login_required
def EE():
    if request.method == 'POST':
        # Get user inputs from the form
        Num_sample = request.form['Num_sample']
        Size_area = request.form['Size_area']
        Num_user = request.form['Num_user']
        Num_channel = request.form['Num_channel']
        mode = "EE"

        # Call the function from your notebook
        result = network_simulator.generate_data(Num_sample, Size_area, Num_user, Num_channel, mode)

        # Save the result as a JSON file in the static directory
        filename = "EE_dataset.json"
        filepath = "static/" + filename  # Path to the static directory
        with open(filepath, 'w') as f:
            json.dump(result, f) # Changed from jsonfiy to json.dump

        # Pass the result to the template
        return render_template('EE.html', result=result)

    return render_template('EE.html')


@app.route('/EE_dataset.json')
def serve_json_EE():
    return send_from_directory('static', 'EE_dataset.json')


@app.route("/se_dataset_generation", methods=['GET', 'POST'])
# @login_required
def SE():
    if request.method == 'POST':
        # Get user inputs from the form
        Num_sample = request.form['Num_sample']
        Size_area = request.form['Size_area']
        Num_user = request.form['Num_user']
        Num_channel = request.form['Num_channel']
        mode = "SE"

        # Call the function from your notebook
        result = network_simulator.generate_data(Num_sample, Size_area, Num_user, Num_channel, mode)

        # Save the result as a JSON file in the static directory
        filename = "SE_dataset.json"
        filepath = "static/" + filename  # Path to the static directory
        with open(filepath, 'w') as f:
            json.dump(result, f) # Changed from jsonfiy to json.dump

        # Pass the result to the template
        return render_template('SE.html', result=result)

    return render_template('SE.html')


@app.route('/SE_dataset.json')
def serve_json_SE():
    return send_from_directory('static', 'SE_dataset.json')


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Login failed. Check your email and/or password", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Your account has been created!", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
 
