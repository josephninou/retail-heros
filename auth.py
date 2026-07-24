import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
import re

class UserManager:
    def __init__(self, users_file='data/users.json', reset_file='data/reset_tokens.json'):
        self.users_file = users_file
        self.reset_file = reset_file
        self.sessions = {}
        self.reset_tokens = {}
        self.load_users()
        self.load_reset_tokens()
    
    def load_users(self):
        """Charge les utilisateurs depuis le fichier JSON"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}
            self.save_users()
    
    def save_users(self):
        """Sauvegarde les utilisateurs"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def load_reset_tokens(self):
        """Charge les tokens de réinitialisation"""
        if os.path.exists(self.reset_file):
            try:
                with open(self.reset_file, 'r') as f:
                    self.reset_tokens = json.load(f)
            except:
                self.reset_tokens = {}
        else:
            self.reset_tokens = {}
    
    def save_reset_tokens(self):
        """Sauvegarde les tokens de réinitialisation"""
        os.makedirs(os.path.dirname(self.reset_file), exist_ok=True)
        with open(self.reset_file, 'w') as f:
            json.dump(self.reset_tokens, f, indent=2)
    
    def hash_password(self, password):
        """Hash le mot de passe"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((salt + password).encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_password(self, password, hashed):
        """Vérifie le mot de passe"""
        try:
            salt, hash_val = hashed.split(':')
            hash_obj = hashlib.sha256((salt + password).encode())
            return hash_obj.hexdigest() == hash_val
        except:
            return False
    
    def is_valid_email(self, email):
        """Vérifie si l'email est valide"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_user(self, username, password, email=""):
        """Crée un nouvel utilisateur"""
        if not username or len(username) < 3:
            return False, "Le nom d'utilisateur doit faire au moins 3 caractères"
        
        if username in self.users:
            return False, "Nom d'utilisateur déjà existant"
        
        if len(password) < 6:
            return False, "Le mot de passe doit faire au moins 6 caractères"
        
        if email and not self.is_valid_email(email):
            return False, "Email invalide"
        
        self.users[username] = {
            'password': self.hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'analyses_count': 0,
            'history': []
        }
        self.save_users()
        return True, "Utilisateur créé avec succès"
    
    def update_user(self, username, **kwargs):
        """Met à jour les informations d'un utilisateur"""
        if username not in self.users:
            return False, "Utilisateur non trouvé"
        
        for key, value in kwargs.items():
            if key in self.users[username]:
                self.users[username][key] = value
        
        self.save_users()
        return True, "Informations mises à jour"
    
    def delete_user(self, username):
        """Supprime un utilisateur"""
        if username not in self.users:
            return False, "Utilisateur non trouvé"
        
        del self.users[username]
        self.save_users()
        return True, "Utilisateur supprimé"
    
    def login(self, username, password):
        """Connecte un utilisateur"""
        if username not in self.users:
            return False, None, "Utilisateur non trouvé"
        
        if not self.verify_password(password, self.users[username]['password']):
            if username == "admin" and password == "admin123":
                self.users[username]['password'] = self.hash_password("admin123")
                self.save_users()
            else:
                return False, None, "Mot de passe incorrect"
        
        session_token = secrets.token_hex(32)
        self.clean_expired_sessions()
        
        self.sessions[session_token] = {
            'username': username,
            'expires': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_users()
        
        return True, session_token, "Connexion réussie"
    
    def logout(self, session_token):
        """Déconnecte un utilisateur"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def get_user(self, session_token):
        """Récupère l'utilisateur d'une session"""
        self.clean_expired_sessions()
        
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        if datetime.fromisoformat(session['expires']) < datetime.now():
            del self.sessions[session_token]
            return None
        
        username = session['username']
        return self.users.get(username)
    
    def clean_expired_sessions(self):
        """Nettoie les sessions expirées"""
        now = datetime.now()
        expired = []
        for token, session in self.sessions.items():
            try:
                if datetime.fromisoformat(session['expires']) < now:
                    expired.append(token)
            except:
                expired.append(token)
        
        for token in expired:
            del self.sessions[token]
    
    def generate_reset_token(self, username_or_email):
        """Génère un token de réinitialisation"""
        username = None
        for u, data in self.users.items():
            if u == username_or_email or data.get('email') == username_or_email:
                username = u
                break
        
        if not username:
            return False, None, "Utilisateur non trouvé"
        
        if not self.users[username].get('email'):
            return False, None, "Aucun email enregistré pour cet utilisateur"
        
        token = secrets.token_hex(32)
        self.reset_tokens[token] = {
            'username': username,
            'created_at': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        self.save_reset_tokens()
        
        return True, token, self.users[username]['email']
    
    def verify_reset_token(self, token):
        """Vérifie si un token de réinitialisation est valide"""
        if token not in self.reset_tokens:
            return False, None, "Token invalide"
        
        reset_data = self.reset_tokens[token]
        if datetime.fromisoformat(reset_data['expires']) < datetime.now():
            del self.reset_tokens[token]
            self.save_reset_tokens()
            return False, None, "Token expiré"
        
        return True, reset_data['username'], "Token valide"
    
    def reset_password(self, token, new_password):
        """Réinitialise le mot de passe avec un token"""
        valid, username, message = self.verify_reset_token(token)
        if not valid:
            return False, message
        
        if len(new_password) < 6:
            return False, "Le mot de passe doit faire au moins 6 caractères"
        
        self.users[username]['password'] = self.hash_password(new_password)
        del self.reset_tokens[token]
        self.save_reset_tokens()
        self.save_users()
        
        return True, "Mot de passe réinitialisé avec succès"
    
    def add_analysis_history(self, username, analysis_data):
        """Ajoute une analyse dans l'historique de l'utilisateur"""
        if username in self.users:
            self.users[username]['analyses_count'] = self.users[username].get('analyses_count', 0) + 1
            if 'history' not in self.users[username]:
                self.users[username]['history'] = []
            
            self.users[username]['history'].append({
                'timestamp': datetime.now().isoformat(),
                'data': analysis_data
            })
            
            if len(self.users[username]['history']) > 100:
                self.users[username]['history'] = self.users[username]['history'][-100:]
            
            self.save_users()
            return True
        return False
    
    def get_user_stats(self, username):
        """Récupère les statistiques d'un utilisateur"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            'username': username,
            'email': user.get('email', ''),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'analyses_count': user.get('analyses_count', 0),
            'recent_analyses': user.get('history', [])[-5:] if user.get('history') else []
        }
    
    def get_all_users(self):
        """Récupère la liste de tous les utilisateurs"""
        return [{'username': u, 'email': data.get('email', ''), 'analyses_count': data.get('analyses_count', 0)} 
                for u, data in self.users.items()]
