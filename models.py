from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_login import UserMixin # Import this
from werkzeug.security import generate_password_hash, check_password_hash # Import these

db = SQLAlchemy()

# Add UserMixin to the User class
class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False) # Increased length for stronger hash
    role = Column(String(20), nullable=False, default='Captain') # 'Super Admin', 'Admin', 'Captain'
    
    # This links a Captain to their team
    team_id = Column(Integer, ForeignKey('team.id'), nullable=True)
    team = relationship('Team', back_populates='captain')

    # New methods for password management
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Team(db.Model):
    id = Column(Integer, primary_key=True)
    team_name = Column(String(100), unique=True, nullable=False)
    captain_name = Column(String(100), nullable=False)
    purse = Column(Integer, default=10000)
    purse_spent = Column(Integer, default=0)
    
    players_taken_count = Column(Integer, default=0)
    slots_remaining = Column(Integer, default=15)
    
    captain = relationship('User', uselist=False, back_populates='team')
    players = relationship('Player', back_populates='team')

class Player(db.Model):
    id = Column(Integer, primary_key=True)
    player_name = Column(String(100), nullable=False)
    # ... other fields ...
    image_filename = Column(String(100), nullable=True, default='default_player.png') # Add this line
    # ... rest of the model ...
    
    # CPL 2024 Stats
    cpl_2024_team = Column(String(100))
    cpl_2024_innings = Column(Integer)
    cpl_2024_runs = Column(Integer)
    cpl_2024_average = Column(Float)
    cpl_2024_sr = Column(Float)
    cpl_2024_hs = Column(Integer)
    
    # Overall Records
    overall_matches = Column(Integer)
    overall_runs = Column(Integer)
    overall_wickets = Column(Integer)
    overall_bat_avg = Column(Float)
    overall_bowl_avg = Column(Float)
    
    # Auction Status
    status = Column(String(20), default='Unsold') # 'Unsold', 'Sold'
    sold_price = Column(Integer, default=0)
    
    team_id = Column(Integer, ForeignKey('team.id'), nullable=True)
    team = relationship('Team', back_populates='players')