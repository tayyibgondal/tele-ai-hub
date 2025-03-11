from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from config import Config
import requests
import threading
from multiprocessing import Process


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

FINETUNING_COLAB_SERVER_URL = "https://7768-34-145-93-8.ngrok-free.app"  # replace with ngrok tunnel URL

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def home():
    return render_template("home.html")

@app.route('/finetune', methods=['GET', 'POST'])
@login_required
def finetune():
    print("in finetune")
    models = ["unsloth/Phi-3.5-mini-instruct", "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit", "unsloth/mistral-7b-v0.3-bnb-4bit", "unsloth/gemma-2-9b-bnb-4bit"]
    batch_sizes = [4, 6, 8, 12]
    learning_rates = ["1e-5", "2e-5", "5e-5"]
    epochs = [1, 2, 3, 5]
    grad_steps = [2, 4, 6, 8]
    datasets = ["Energy Efficiency", "Spectral Efficiency"]
    
    if request.method == 'POST':
        print("in post")
        selected_model = request.form['model']
        batch_size = request.form['batch_size']
        learning_rate = request.form['learning_rate']
        num_epochs = request.form['epochs']
        grad_step = request.form['grad_step']
        dataset = request.form['metric']
        
        # Send parameters to Google Colab API
        payload = {
            "model": selected_model,
            "batch_size": batch_size,
            "grad_steps": grad_step,
            "learning_rate": learning_rate,
            "epochs": num_epochs,
            "dataset": dataset,
            "user": current_user.username
        }
        print(payload)

        response = requests.post(f"{FINETUNING_COLAB_SERVER_URL}/start_finetuning", json=payload, timeout=1200)

        print("request sent")
        # if not response:
        #     print("no response")
        if response.status_code == 200:
            print(response)
            try:
                data = response.json()  # This is where the error occurs
                print(f"Received JSON: {data}")
                message = data.get("message")

            except requests.exceptions.JSONDecodeError:
                print("Error: Response is not valid JSON!")
                message = None
            return render_template("finetuning_complete.html", completion_message=message)
        else:
            return f"Error in finetuning. Please try again. Response code: {response.status_code}"

    return render_template('finetune.html', models=models, batch_sizes=batch_sizes, learning_rates=learning_rates, epochs=epochs, grad_steps=grad_steps, datasets=datasets)

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
    app.run(debug=True, threaded=True)
