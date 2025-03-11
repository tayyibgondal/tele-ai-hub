import pytest
import os
import json
from unittest.mock import patch, MagicMock
from flask import session
from src.app import app, db, User, check_password_hash

@pytest.fixture
def client():
    """
    Pytest fixture to create a Flask test client.
    This also sets up the app in TESTING mode and uses an in-memory database.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['WTF_CSRF_ENABLED'] = False  # so we can post forms without CSRF token in tests
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        # Teardown
        with app.app_context():
            db.drop_all()


def create_user(username="testuser", email="test@example.com", password="testpass"):
    """
    Helper to create a user directly in the test database.
    Returns the user object.
    """
    hashed_password = User(password=password).password  # or do generate_password_hash
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client):
    """
    Creates a user and logs them in before returning the test client.
    """
    with client:
        user = create_user()
        # Actually log in by posting to /login
        res = client.post("/login", data={
            "email": user.email,
            "password": "testpass"  # matches the created user's password
        }, follow_redirects=True)
        assert res.status_code == 200
        yield client


# -----------------------------
#   LOGIN / REGISTER / LOGOUT
# -----------------------------
def test_register_get(client):
    """
    GET /register should return 200.
    """
    res = client.get("/register")
    assert res.status_code == 200
    assert b"Register" in res.data  # or check template content

def test_register_post(client):
    """
    POST /register with valid data should create a new user and redirect to /login
    """
    res = client.post("/register", data={
        "username": "myuser",
        "email": "myuser@example.com",
        "password": "mypassword",
    }, follow_redirects=True)
    assert res.status_code == 200
    user = User.query.filter_by(email="myuser@example.com").first()
    assert user is not None
    # We used 'mypassword', but the DB should store a hashed version
    assert check_password_hash(user.password, "mypassword")

def test_login_get(client):
    """
    GET /login should return 200
    """
    res = client.get("/login")
    assert res.status_code == 200
    assert b"Login" in res.data

def test_login_post_valid(client):
    """
    POST /login with valid creds should redirect to /home
    """
    # create user
    user = create_user(email="login@example.com", password="supersecret")

    res = client.post("/login", data={
        "email": "login@example.com",
        "password": "supersecret"
    }, follow_redirects=False)
    # By default, it should redirect to /home
    assert res.status_code == 302
    assert "/home" in res.location

def test_login_post_invalid(client):
    """
    POST /login with invalid creds should show error message.
    """
    res = client.post("/login", data={
        "email": "notexist@example.com",
        "password": "wrong"
    }, follow_redirects=True)
    assert res.status_code == 200
    # We expect a flash message or something
    assert b"Login failed" in res.data

def test_logout(logged_in_client):
    """
    GET /logout should log the user out, clearing the session, and redirect to /login.
    """
    res = logged_in_client.get("/logout", follow_redirects=False)
    assert res.status_code == 302
    # After logout, check that session is cleared
    with logged_in_client.session_transaction() as sess:
        assert sess.get('_user_id') is None
    # We expect a redirect to /login
    assert "/login" in res.location


# -----------------------------
#   PROTECTED ROUTES
# -----------------------------
def test_home_requires_login(client):
    """
    GET / should redirect to login if not logged in.
    """
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.location

def test_home_ok_when_logged_in(logged_in_client):
    """
    GET / should return 200 for logged in user.
    """
    res = logged_in_client.get("/")
    assert res.status_code == 200
    assert b"home" in res.data  # or check some text from your home.html


# -----------------------------
#   NOMA EE DATASET GENERATION
# -----------------------------
@patch("src.app.noma_ee_dataset_generation.main")
def test_noma_ee_post(mock_noma_ee_main, logged_in_client):
    """
    POST /noma_ee_dataset_generation 
    Should call noma_ee_dataset_generation.main(...) 
    and create JSON file in static.
    """
    mock_noma_ee_main.return_value = [{"sample_index": 0, "dummy": "val"}]

    data = {
        "rows_of_data": "5",
        "temperature": "300",
        "bandwidth": "1e7",
        "simulation_area_size": "60",
        "n_antennas": "2",
        "mc": "1"
    }
    res = logged_in_client.post("/noma_ee_dataset_generation", data=data, follow_redirects=True)
    assert res.status_code == 200
    mock_noma_ee_main.assert_called_once_with("5", "300", "1e7", "60", "2", "1")

    # Check that the JSON file was (in theory) created in static/
    with open("static/NOMA_EE_dataset.json", "r") as f:
        content = json.load(f)
    assert content == [{"sample_index": 0, "dummy": "val"}]
    assert b"NOMA_EE" in res.data  # The template might have "NOMA_EE"

def test_noma_ee_get(logged_in_client):
    """
    GET /noma_ee_dataset_generation should just return the form/template, no call to main.
    """
    res = logged_in_client.get("/noma_ee_dataset_generation")
    assert res.status_code == 200
    # Likely you have "NOMA_EE.html" which includes a form
    assert b"NOMA EE Dataset Generation" in res.data

def test_serve_json_noma_ee(logged_in_client):
    """
    GET /NOMA_EE_dataset.json 
    Should serve the file from static dir if it exists.
    """
    # Create a dummy file
    filepath = "static/NOMA_EE_dataset.json"
    with open(filepath, "w") as f:
        json.dump({"test": "value"}, f)

    res = logged_in_client.get("/NOMA_EE_dataset.json")
    assert res.status_code == 200
    assert res.is_json
    assert res.json == {"test": "value"}


# -----------------------------
#   NOMA SE DATASET GENERATION
# -----------------------------
@patch("src.app.noma_se_dataset_generation.main")
def test_noma_se_post(mock_noma_se_main, logged_in_client):
    mock_noma_se_main.return_value = [{"sample_index": 0, "dummy": "val_se"}]

    data = {
        "rows_of_data": "10",
        "temperature": "300",
        "bandwidth": "1e7",
        "simulation_area_size": "80",
        "n_antennas": "2",
        "mc": "2"
    }
    res = logged_in_client.post("/noma_se_dataset_generation", data=data, follow_redirects=True)
    assert res.status_code == 200
    mock_noma_se_main.assert_called_once_with("10", "300", "1e7", "80", "2", "2")

    with open("static/NOMA_SE_dataset.json", "r") as f:
        content = json.load(f)
    assert content == [{"sample_index": 0, "dummy": "val_se"}]
    assert b"NOMA_SE" in res.data


# -----------------------------
#   "EE" & "SE" from network_simulator
# -----------------------------
@patch("src.app.network_simulator.generate_data")
def test_ee_post(mock_gen_data, logged_in_client):
    mock_gen_data.return_value = [{"index": 1, "type": "EE"}]

    form_data = {
        "Num_sample": "2",
        "Size_area": "60",
        "Num_user": "3",
        "Num_channel": "1"
    }
    res = logged_in_client.post("/ee_dataset_generation", data=form_data, follow_redirects=True)
    assert res.status_code == 200
    mock_gen_data.assert_called_once_with("2", "60", "3", "1", "EE")

    with open("static/EE_dataset.json", "r") as f:
        content = json.load(f)
    assert content == [{"index": 1, "type": "EE"}]

@patch("src.app.network_simulator.generate_data")
def test_se_post(mock_gen_data, logged_in_client):
    mock_gen_data.return_value = [{"index": 1, "type": "SE"}]

    form_data = {
        "Num_sample": "3",
        "Size_area": "50",
        "Num_user": "2",
        "Num_channel": "1"
    }
    res = logged_in_client.post("/se_dataset_generation", data=form_data, follow_redirects=True)
    assert res.status_code == 200
    mock_gen_data.assert_called_once_with("3", "50", "2", "1", "SE")

    with open("static/SE_dataset.json", "r") as f:
        content = json.load(f)
    assert content == [{"index": 1, "type": "SE"}]


# -----------------------------
#   FINETUNE
# -----------------------------
@patch("requests.post")
def test_finetune_post(mock_requests, logged_in_client):
    """
    POST /finetune should send data to the remote server, 
    then render finetuning_complete.html on success.
    """
    # Mock a successful response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": "Finetuning started!"}
    mock_requests.return_value = mock_resp

    data = {
        "model": "unsloth/Phi-3.5-mini-instruct",
        "batch_size": "4",
        "learning_rate": "1e-5",
        "epochs": "1",
        "grad_step": "2",
        "metric": "Energy Efficiency"
    }
    res = logged_in_client.post("/finetune", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Finetuning started!" in res.data

    # Check that the request was called with the correct JSON payload
    expected_payload = {
        "model": "unsloth/Phi-3.5-mini-instruct",
        "batch_size": "4",
        "grad_steps": "2",
        "learning_rate": "1e-5",
        "epochs": "1",
        "dataset": "Energy Efficiency",
        "user": "testuser"  # from create_user fixture default
    }
    mock_requests.assert_called_once()
    actual_args, actual_kwargs = mock_requests.call_args
    assert expected_payload == actual_kwargs['json']


# -----------------------------
#   CHATS
# -----------------------------
@patch("src.app.load_hf_model", return_value=True)
@patch("src.app.chat_with_hf_model", return_value="HF model says hello")
def test_chat_hf(mock_chat_hf, mock_load_hf, logged_in_client):
    """
    Ensure that chat_hf route loads a model and then chats properly.
    """
    # 1) load_model action
    res = logged_in_client.post("/chat_hf", data={"action": "load_model", "model": "gpt2"})
    assert res.status_code == 200
    # Session should have selected_model_hf = "gpt2"

    # 2) chat action
    res = logged_in_client.post("/chat_hf", data={"action": "chat", "message": "Hello model!"})
    assert res.status_code == 200
    # chat_with_hf_model was called
    mock_chat_hf.assert_called_once_with("gpt2", "Hello model!")
    assert b"HF model says hello" in res.data

@patch("src.app.get_llm_instance")
def test_chat_ollama(mock_llm, logged_in_client):
    """
    Test chat with Ollama route 
    using a mock LLM instance.
    """
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = "Ollama says hi"
    mock_llm.return_value = mock_instance

    data = {
        "message": "Your query for Ollama",
        "model": "deepseek-r1:7b"
    }
    res = logged_in_client.post("/chat_ollama", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Ollama says hi" in res.data
    # Check that get_llm_instance was called with the model name and service='ollama'
    mock_llm.assert_called_once_with("deepseek-r1:7b", service='ollama')

@patch("src.app.get_llm_instance")
def test_chat_openai(mock_llm, logged_in_client):
    """
    Test chat with OpenAI route using a mock.
    """
    mock_openai_llm = MagicMock()
    mock_openai_llm.invoke.return_value = "OpenAI says hello"
    mock_llm.return_value = mock_openai_llm

    data = {
        "message": "OpenAI prompt",
        "model": "gpt-3.5-turbo"
    }
    res = logged_in_client.post("/chat_openai", data=data, follow_redirects=True)
    assert res.status_code == 200
    assert b"OpenAI says hello" in res.data
    mock_llm.assert_called_once_with("gpt-3.5-turbo", service='openai')


def test_chat_gradio_get(logged_in_client):
    """
    GET /chat_gradio returns the chat_gradio.html template.
    """
    res = logged_in_client.get("/chat_gradio")
    assert res.status_code == 200
    assert b"Gradio" in res.data  # or check specific text
