import gradio as gr
import os
import json
import hashlib
import secrets
from datetime import datetime

# ===== GESTION DES UTILISATEURS =====
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"admin": {"password": hash_password("admin123"), "created_at": str(datetime.now())}}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    salt = secrets.token_hex(8)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(password, hashed):
    salt, hash_val = hashed.split(":")
    return hash_val == hashlib.sha256((salt + password).encode()).hexdigest()

# ===== INTERFACE =====
current_user = None

def login(username, password):
    global current_user
    users = load_users()
    if username in users and verify_password(password, users[username]["password"]):
        current_user = username
        return f"✅ Bienvenue {username} !", gr.update(visible=False), gr.update(visible=True)
    return "❌ Identifiants incorrects", gr.update(visible=True), gr.update(visible=False)

def logout():
    global current_user
    current_user = None
    return "👋 Déconnecté", gr.update(visible=True), gr.update(visible=False)

def register(username, password):
    users = load_users()
    if username in users:
        return "❌ Nom déjà utilisé"
    if len(password) < 4:
        return "❌ Mot de passe trop court (min 4)"
    users[username] = {"password": hash_password(password), "created_at": str(datetime.now())}
    save_users(users)
    return "✅ Compte créé ! Connectez-vous."

# ===== INTERFACE GRADIO =====
with gr.Blocks(title="Retail-Heros", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏪 Retail-Heros - Analyse de Rayons")
    
    # Section authentification
    with gr.Row():
        with gr.Column(scale=1, visible=True) as login_col:
            with gr.Tab("🔐 Connexion"):
                login_user = gr.Textbox(label="Nom")
                login_pass = gr.Textbox(label="Mot de passe", type="password")
                login_btn = gr.Button("Se connecter")
                login_msg = gr.Markdown("")
            
            with gr.Tab("📝 Inscription"):
                reg_user = gr.Textbox(label="Nom")
                reg_pass = gr.Textbox(label="Mot de passe", type="password")
                reg_btn = gr.Button("Créer un compte")
                reg_msg = gr.Markdown("")
            
            logout_btn = gr.Button("🚪 Déconnexion", visible=False)
        
        with gr.Column(scale=2, visible=False) as app_col:
            gr.Markdown("### 👤 Zone utilisateur")
            welcome = gr.Markdown("")
            name_input = gr.Textbox(label="Entrez votre nom")
            greet_btn = gr.Button("Dire bonjour")
            greet_output = gr.Textbox(label="Réponse")
            greet_btn.click(fn=lambda name: f"Bonjour {name} !", inputs=name_input, outputs=greet_output)
    
    # Connexions des événements
    login_btn.click(login, [login_user, login_pass], [login_msg, login_col, app_col])
    logout_btn.click(logout, None, [login_msg, login_col, app_col])
    reg_btn.click(register, [reg_user, reg_pass], reg_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)
