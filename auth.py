import json
import os
import hashlib
import secrets
from datetime import datetime

class UserManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.sessions = {}
        self.load_users()
    
    def load_users(self):
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
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password):
        salt = secrets.token_hex(8)
        return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        if ":" not in hashed:
            return password == hashed
        try:
            salt, hash_val = hashed.split(":")
            return hash_val == hashlib.sha256((salt + password).encode()).hexdigest()
        except:
            return False
    
    def create_user(self, username, password, email=""):
        if username in self.users:
            return False, "Nom d'utilisateur déjà existant"
        if len(password) < 4:
            return False, "Mot de passe trop court (min 4)"
        self.users[username] = {
            'password': self.hash_password(password),
            'email': email,
            'created_at': str(datetime.now()),
            'last_login': None,
            'analyses_count': 0,
            'history': []
        }
        self.save_users()
        return True, "Utilisateur créé avec succès"
    
    def login(self, username, password):
        if username not in self.users:
            return False, None, "Utilisateur non trouvé"
        if not self.verify_password(password, self.users[username]['password']):
            return False, None, "Mot de passe incorrect"
        
        session_token = secrets.token_hex(32)
        self.sessions[session_token] = {
            'username': username,
            'expires': (datetime.now() + timedelta(days=7)).isoformat()
        }
        self.users[username]['last_login'] = str(datetime.now())
        self.save_users()
        
        return True, session_token, "Connexion réussie"
    
    def logout(self, session_token):
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def get_user(self, session_token):
        if session_token not in self.sessions:
            return None
        session = self.sessions[session_token]
        username = session['username']
        return self.users.get(username)
    
    def add_analysis_history(self, username, analysis_data):
        if username in self.users:
            self.users[username]['analyses_count'] = self.users[username].get('analyses_count', 0) + 1
            if 'history' not in self.users[username]:
                self.users[username]['history'] = []
            self.users[username]['history'].append({
                'timestamp': str(datetime.now()),
                'data': analysis_data
            })
            self.save_users()
            return True
        return False
    
    def get_user_stats(self, username):
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

from datetime import timedelta
