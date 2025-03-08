from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from config import Config
import requests  # To interact with Hugging Face's API
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # For local inference
from dotenv import load_dotenv

load_dotenv()  # load .env

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Model Storage
models_cache = {}

# Login Manager Setup
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@login_required
def home():
    return render_template("home.html")


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


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    models = ["gpt2", "distilbert-base-uncased"]  # You can add more models here
    selected_model = session.get('selected_model', "gpt2")  # Use session to remember the model
    model_loaded = session.get('model_loaded', False)
    conversation_history = session.get('conversation_history', [])

    if request.method == "POST":
        action = request.form.get('action')

        if action == "load_model":
            selected_model = request.form['model']
            model_loaded = load_model(selected_model)
            session['selected_model'] = selected_model
            session['model_loaded'] = model_loaded

        elif action == "chat":
            user_input = request.form['message']
            if model_loaded:
                response = chat_with_model(selected_model, user_input)
                conversation_history.append({"user": user_input, "model": response})
                session['conversation_history'] = conversation_history
            else:
                response = "Model not loaded yet. Please load the model first."

        return render_template("chat.html", response=response, models=models, selected_model=selected_model,
                               model_loaded=model_loaded, conversation_history=conversation_history)

    return render_template("chat.html", models=models, selected_model=selected_model, model_loaded=model_loaded,
                           conversation_history=conversation_history)


def load_model(model_name):
    """
    Load the model into the server and store it in cache for reuse.
    """
    if model_name not in models_cache:
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
        models_cache[model_name] = generator
        return True
    return False


def chat_with_model(model_name, user_input):
    """
    Chat with the loaded model.
    """
    if model_name in models_cache:
        generator = models_cache[model_name]
        result = generator(user_input, max_length=50, num_return_sequences=1)
        return result[0]['generated_text']
    else:
        return "Error: Model not loaded."


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
