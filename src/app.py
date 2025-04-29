from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from config import Config
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import noma_ee_dataset_generation, noma_se_dataset_generation, network_simulator
import json
from dotenv import load_dotenv
from llm_providers import get_llm_instance
import requests
import threading
from multiprocessing import Process

# Environment-based config for Ollama & OpenAI 
load_dotenv("../.env")  # Load .env if present

# -----------------------------
#   FLASK APP SETUP
# -----------------------------
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Hugging Face model cache
models_cache = {}
ollama_models_cache = {}
FINETUNING_COLAB_SERVER_URL = "https://a2ec-34-87-172-108.ngrok-free.app" 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
#   ROUTES
# -----------------------------
@app.route("/")
@login_required
def home():
    return render_template('home.html')

@app.route("/noma_ee_dataset_generation", methods=['GET', 'POST'])
@login_required
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
            json.dump(result, f, indent=4) # Changed from jsonfiy to json.dump

        # Pass the result to the template
        return render_template('NOMA_EE.html', result=result)

    return render_template('NOMA_EE.html')


@app.route('/NOMA_EE_dataset.json')
def serve_json_NOMA_EE():
    return send_from_directory('static', 'NOMA_EE_dataset.json')

@app.route("/noma_se_dataset_generation", methods=['GET', 'POST'])
@login_required
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
            json.dump(result, f, indent=4) 

        # Pass the result to the template
        return render_template('NOMA_SE.html', result=result)

    return render_template('NOMA_SE.html')


@app.route('/NOMA_SE_dataset.json')
def serve_json_NOMA_SE():
    return send_from_directory('static', 'NOMA_SE_dataset.json')

@app.route("/ee_dataset_generation", methods=['GET', 'POST'])
@login_required
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
@login_required
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
    session.clear()
    return redirect(url_for('login'))

@app.route("/dataset_generation", methods=['GET'])
@login_required
def dataset_generation():
    return render_template('dataset_generation.html')


@app.route("/telecom_agents")
@login_required
def telecom_agents():
    return render_template("telecom_agents.html")

@app.route("/about")
@login_required
def about():
    # Team members data
    team = [
        {
            "name": "Tayyib Ul Hassan",
            "position": "Chief Executive Officer",
            "bio": "Former research scientist with over 15 years of experience in telecommunications and AI systems. Led multiple R&D teams developing cutting-edge wireless communication solutions.",
            "image": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&q=80&w=687&ixlib=rb-4.0.3",
            "linkedin": "https://linkedin.com/",
            "twitter": "https://twitter.com/",
            "github": "https://github.com/"
        },
        {
            "name": "Attiya Waqar",
            "position": "Chief Technology Officer",
            "bio": "PhD in Wireless Communications with expertise in NOMA and resource allocation algorithms. Published over 30 research papers in top telecommunications journals.",
            "image": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=688&ixlib=rb-4.0.3",
            "linkedin": "https://linkedin.com/",
            "twitter": "https://twitter.com/"
        },
        {
            "name": "Aamina Binte Khurram",
            "position": "Head of AI Research",
            "bio": "Leading our research initiatives in applying machine learning to complex network optimization. Previously developed AI systems for predictive network maintenance.",
            "image": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&q=80&w=687&ixlib=rb-4.0.3",
            "linkedin": "https://linkedin.com/",
            "github": "https://github.com/"
        },
        {
            "name": "Zeeshan Ahmad",
            "position": "Solution Architect",
            "bio": "Telecom engineer with 8+ years experience in designing and implementing enterprise-scale telecommunication systems and network infrastructure.",
            "image": "https://images.unsplash.com/photo-1568602471122-7832951cc4c5?auto=format&fit=crop&q=80&w=870&ixlib=rb-4.0.3",
            "linkedin": "https://linkedin.com/",
            "github": "https://github.com/"
        },
        {
            "name": "Saira Khan",
            "position": "Product Manager",
            "bio": "Experienced in bringing AI products to market with a focus on telecommunications applications. Expert in translating technical capabilities into business value.",
            "image": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=761&ixlib=rb-4.0.3",
            "twitter": "https://twitter.com/"
        },
        {
            "name": "Ibrahim Malik",
            "position": "Data Science Lead",
            "bio": "Specializes in applying deep learning to analyze and optimize complex network data for improved performance and reliability.",
            "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?auto=format&fit=crop&q=80&w=876&ixlib=rb-4.0.3",
            "linkedin": "https://linkedin.com/",
            "github": "https://github.com/"
        }
    ]
    return render_template('about.html', team=team)

@app.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    if request.method == "POST":
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or store the contact request
        # For now, we'll just flash a success message
        flash(f"Thanks {name}! Your message has been received. We'll contact you shortly.", "success")
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get('action')
        
        if action == "update_profile":
            # Update username
            new_username = request.form.get('username')
            if new_username and new_username != current_user.username:
                # Check if username is already taken
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user and existing_user.id != current_user.id:
                    flash("Username already taken. Please choose another one.", "danger")
                else:
                    current_user.username = new_username
                    db.session.commit()
                    flash("Profile updated successfully!", "success")
            
            # Update email
            new_email = request.form.get('email')
            if new_email and new_email != current_user.email:
                # Check if email is already taken
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user and existing_user.id != current_user.id:
                    flash("Email already taken. Please choose another one.", "danger")
                else:
                    current_user.email = new_email
                    db.session.commit()
                    flash("Profile updated successfully!", "success")
        
        elif action == "change_password":
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Verify current password
            if not check_password_hash(current_user.password, current_password):
                flash("Current password is incorrect.", "danger")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "danger")
            else:
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash("Password changed successfully!", "success")
    
    return render_template('settings.html')

@app.route("/team")
@login_required
def team():
    return redirect(url_for('about'))

@app.route("/careers")
@login_required
def careers():
    # Placeholder for a careers page - redirecting to contact for now
    flash("We're always looking for talented individuals! Please contact us for current openings.", "info")
    return redirect(url_for('contact'))

@app.route("/partners")
@login_required
def partners():
    # Placeholder for a partners page - redirecting to about for now
    return redirect(url_for('about'))

@app.route("/blog")
@login_required
def blog():
    # Placeholder for a blog page - redirecting to home for now
    flash("Our blog is coming soon! Check back later for updates.", "info")
    return redirect(url_for('home'))

@app.route("/case-studies")
@login_required
def case_studies():
    # Placeholder for case studies - redirecting to home for now
    flash("Case studies are coming soon! Check back later for updates.", "info")
    return redirect(url_for('home'))

@app.route("/documentation")
@login_required
def documentation():
    # Placeholder for documentation - redirecting to dataset_generation for now
    return redirect(url_for('dataset_generation'))

@app.route("/research")
@login_required
def research():
    # Placeholder for research papers - redirecting to dataset_generation for now
    return redirect(url_for('dataset_generation'))

@app.route("/webinars")
@login_required
def webinars():
    # Placeholder for webinars - redirecting to home for now
    flash("Webinars are coming soon! Check back later for updates.", "info")
    return redirect(url_for('home'))

@app.route("/privacy")
def privacy():
    # Placeholder for privacy policy - could create a real page later
    return render_template('privacy.html')

@app.route("/terms")
def terms():
    # Placeholder for terms of service - could create a real page later
    return render_template('terms.html')

@app.route("/sitemap")
def sitemap():
    # Use our new sitemap template
    return render_template('sitemap.html')

# -----------------------------
#   Chat with Hugging Face
# -----------------------------
@app.route("/chat_hf", methods=["GET", "POST"])
@login_required
def chat_hf():
    """
    Replicates your current Hugging Face chat logic.
    """
    models = ["gpt2"]  # Extend as desired
    selected_model = session.get('selected_model_hf', None)
    model_loaded = session.get('model_loaded_hf', False)
    conversation_history = session.get('conversation_history_hf', [])
    response = None

    if request.method == "POST":
        action = request.form.get('action')

        if action == "load_model":
            new_selected_model = request.form['model']
            # If user picks a new model or it's not in cache, load it
            if (new_selected_model != selected_model) or (new_selected_model not in models_cache):
                loaded = load_hf_model(new_selected_model)
                session['selected_model_hf'] = new_selected_model
                session['model_loaded_hf'] = loaded
                session['conversation_history_hf'] = []
                selected_model = new_selected_model
                model_loaded = loaded
                conversation_history = []
            else:
                # If user re-selects the same model, just clear conversation
                session['conversation_history_hf'] = []
                conversation_history = []

        elif action == "chat":
            user_input = request.form['message']
            if model_loaded:
                response = chat_with_hf_model(selected_model, user_input)
                conversation_history.append({"user": user_input, "model": response})
                session['conversation_history_hf'] = conversation_history
            else:
                response = "Model not loaded yet. Please load the model first."

        return render_template(
            "chat_hf.html",
            response=response,
            models=models,
            selected_model=selected_model,
            model_loaded=model_loaded,
            conversation_history=conversation_history
        )

    # GET request
    return render_template(
        "chat_hf.html",
        models=models,
        selected_model=selected_model,
        model_loaded=model_loaded,
        conversation_history=conversation_history
    )


def load_hf_model(model_name):
    """
    Load a Hugging Face model and store in models_cache.
    """
    if model_name not in models_cache:
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
        models_cache[model_name] = generator
        return True
    return True  # It's already loaded


def chat_with_hf_model(model_name, user_input):
    """
    Use the loaded Hugging Face pipeline to generate text.
    """
    if model_name in models_cache:
        generator = models_cache[model_name]
        result = generator(user_input, max_length=50, num_return_sequences=1)
        return result[0]['generated_text']
    else:
        return "Error: Model not loaded."


# -----------------------------
#   Chat with Ollama (No Load)
# -----------------------------
@app.route("/chat_ollama", methods=["GET", "POST"])
@login_required
def chat_ollama():
    """
    No separate 'load' step needed. 
    Optionally let user select from a list of local models, 
    or just use a single default. 
    """
    ollama_models = ["deepseek-r1:7b"]
    selected_model = session.get('selected_model_ollama', ollama_models[0])  
    conversation_history = session.get('conversation_history_ollama', [])

    response_text = None
    if request.method == "POST":
        # On POST, user might pick a model from dropdown (optional)
        user_input = request.form.get('message', '')
        model_choice = request.form.get('model', selected_model)

        # Save model choice in the session
        session['selected_model_ollama'] = model_choice
        selected_model = model_choice

        # Invoke the Ollama LLM with user's input
        ollama_llm = get_llm_instance(selected_model, service='ollama')
        system_prompt = "Imagine you are a specialist in telecommunications, wireless communications, NOMA and resource allocation. Answer the following user querry: \n\n" 
        prompt = system_prompt + user_input
        response_text = ollama_llm.invoke(prompt)

        # Store conversation
        conversation_history.append({"user": user_input, "model": response_text})
        session['conversation_history_ollama'] = conversation_history

    return render_template(
        "chat_ollama.html",
        response=response_text,
        models=ollama_models,
        selected_model=selected_model,
        conversation_history=conversation_history
    )

# -----------------------------
#   Chat with OpenAI (No Load)
# -----------------------------
@app.route("/chat_openai", methods=["GET", "POST"])
@login_required
def chat_openai():
    """
    No separate 'load' step needed. 
    Optionally let user select from a list of OpenAI models,
    or just use a single default.
    """
    openai_models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4.5-preview"]
    selected_model = session.get('selected_model_openai', openai_models[0])
    conversation_history = session.get('conversation_history_openai', [])

    response_text = None
    if request.method == "POST":
        user_input = request.form.get('message', '')
        model_choice = request.form.get('model', selected_model)

        # Save model choice to session
        session['selected_model_openai'] = model_choice
        selected_model = model_choice

        # Call the OpenAILLM from llm_providers
        openai_llm = get_llm_instance(selected_model, service='openai')
        system_prompt = "Imagine you are a specialist in telecommunications, wireless communications, NOMA and resource allocation. Answer the following user querry: \n\n" 
        prompt = system_prompt + user_input
        response_text = openai_llm.invoke(prompt)

        conversation_history.append({"user": user_input, "model": response_text})
        session['conversation_history_openai'] = conversation_history

    return render_template(
        "chat_openai.html",
        response=response_text,
        models=openai_models,
        selected_model=selected_model,
        conversation_history=conversation_history
    )

# -----------------------------
#   Chat with Gradio (No Load)
# -----------------------------
@app.route("/chat_gradio", methods=["GET"])
@login_required
def chat_gradio():
    """
    Just links to external Gradio apps. No 'load' logic needed.
    """
    return render_template("chat_gradio.html")


# -----------------------------
#   Create DB tables if needed
# -----------------------------
with app.app_context():
    db.create_all()


# -----------------------------
#   Run the app
# -----------------------------
if __name__ == "__main__":
    app.run(port=8001, debug=True)
