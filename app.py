import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from models import db, User, Team, Player # Keep your existing models import
from dotenv import load_dotenv
import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import random
import pandas as pd
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///project.db')
app.config['SECRET_KEY'] = 'a_very_secret_key_to_change_later_98765' # Change this!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- LOGIN MANAGER SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'You must be logged in to view this page.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE CREATION & SEEDING ---
@app.before_request
def create_tables():
    # ... (db.create_all() and seeding for User and Team) ...

        # --- Seed Players ---
        # TEMPORARILY COMMENT OUT THIS CHECK:
        # if Player.query.count() == 0:

        # --- This block will now run on Render again ---
        print("Attempting to seed players...") # Add a print statement
        players_to_seed = [ # Define the list outside the potential old 'if'
            Player(player_name="Vasanth Ab", image_filename="vasanth_ab.png", ...), # Add all player details
            Player(player_name="Mukil Hitman", image_filename="mukil_hitman.jpg", ...),
            # ... ADD ALL 10 PLAYERS HERE with their image_filename ...
            Player(player_name="Ramesh G", ...),
        ]

        # Optional: Check if players *already* exist by name to avoid duplicates if needed
        existing_player_names = {p.player_name for p in Player.query.all()}
        new_players = [p for p in players_to_seed if p.player_name not in existing_player_names]

        if new_players:
            db.session.bulk_save_objects(new_players)
            db.session.commit()
            print(f"{len(new_players)} new players seeded.")
        else:
             print("All players already seem to exist in the database.")
        # END OF FORCED BLOCK

        # REMEMBER TO UNCOMMENT THE 'if' LATER

# --- CUSTOM DECORATORS for security ---
def role_required(role_names):
    if not isinstance(role_names, list): role_names = [role_names]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated: return login_manager.unauthorized()
            if current_user.role != 'Super Admin' and current_user.role not in role_names:
                flash('You do not have permission to access this page.', 'error'); return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Utility Function for Password Check ---
def check_admin_password(username, password):
    user = User.query.filter_by(username=username).first()
    # Check if user exists, is Admin/SuperAdmin, and password matches
    if user and (user.role == 'Admin' or user.role == 'Super Admin') and user.check_password(password):
        return True
    return False

# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    player_count = Player.query.count()
    team_count = Team.query.count()
    slots_remaining = 120 - player_count
    try:
        auction_date_str = "2025-12-20"; auction_date = datetime.datetime.strptime(auction_date_str, "%Y-%m-%d").date(); today = datetime.date.today(); days_to_go = (auction_date - today).days
        if days_to_go < 0: days_to_go = 0
    except ValueError: days_to_go = 60
    return render_template('index.html', active_page='home', player_count=player_count, team_count=team_count, slots_remaining=slots_remaining, days_to_go=days_to_go)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username'); password = request.form.get('password'); user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user); flash('Logged in successfully!', 'success'); return redirect(url_for('dashboard'))
        else: flash('Invalid username or password.', 'error')
    return render_template('login.html', active_page='login')

@app.route('/logout')
@login_required
def logout():
    logout_user(); session.pop('auction_started', None); session.pop('current_player_id', None); session.pop('auction_round', None); session.pop('round_complete', None); session.pop('auction_complete', None); session.pop('auction_paused', None)
    flash('You have been logged out.', 'success'); return redirect(url_for('home'))

# --- PROTECTED ROUTES ---
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/players')
@login_required
def players():
    all_players = Player.query.all()
    return render_template('players.html', active_page='players', players=all_players)

@app.route('/teams')
@login_required
def teams():
    all_teams = Team.query.options(db.joinedload(Team.players)).all()
    return render_template('teams.html', active_page='teams', teams=all_teams)

# --- AUCTION ROUTES (MULTI-ROUND + PAUSE/RESUME) ---

@app.route('/auctions')
@login_required
def auctions():
    all_teams = Team.query.all()
    auction_started = session.get('auction_started', False)
    auction_round = session.get('auction_round', 1)
    round_complete = session.get('round_complete', False)
    auction_complete = session.get('auction_complete', False)
    auction_paused = session.get('auction_paused', False) # NEW Paused state
    current_player = None
    next_round_players_count = 0

    if auction_started and not round_complete and not auction_complete and not auction_paused:
        player_id = session.get('current_player_id')
        if player_id:
            current_player = Player.query.get(player_id)
            # If the current player somehow got sold/processed, clear them and try next
            if current_player and current_player.status != 'Unsold':
                 session.pop('current_player_id', None)
                 # Redirect immediately to avoid showing an invalid player
                 return redirect(url_for('next_player'))


    # Calculate players for next round ONLY if the current round is marked complete
    if round_complete:
        next_round_status = f'Round {auction_round} Unsold'
        next_round_players_count = Player.query.filter_by(status=next_round_status).count()
        # If round complete flag is set, but no players found for next round, then auction is truly over
        if next_round_players_count == 0:
             auction_complete = True
             auction_started = False # Ensure auction stops if it somehow wasn't already
             session['auction_complete'] = True
             session['auction_started'] = False


    return render_template('auctions.html',
                           active_page='auctions', all_teams=all_teams,
                           auction_started=auction_started, round_complete=round_complete,
                           auction_complete=auction_complete, auction_paused=auction_paused, # Pass paused state
                           next_round_players_count=next_round_players_count,
                           auction_round=auction_round, player=current_player)

@app.route('/next_player')
@login_required
@role_required(['Admin'])
def next_player():
    if session.get('auction_paused'): # Prevent action if paused
        flash('Auction is paused. Resume before proceeding.', 'warning')
        return redirect(url_for('auctions'))

    auction_round = session.get('auction_round', 1)
    current_round_status = 'Unsold'
    next_round_status_check = f'Round {auction_round} Unsold'

    # Players available RIGHT NOW for auction in the current pool
    unsold_players = Player.query.filter_by(status=current_round_status).all()

    if not unsold_players:
        # Current pool is empty. Check if there are players marked unsold from this round.
        players_for_next_round_count = Player.query.filter_by(status=next_round_status_check).count()

        if players_for_next_round_count > 0:
            # End of the current round, prepare for the next
            flash(f'Round {auction_round} complete. Ready for Round {auction_round + 1}.', 'info')
            session['round_complete'] = True
            session['auction_started'] = False # Pause auction
            session.pop('current_player_id', None) # Clear current player ID
        else:
            # No players in current pool AND no players waiting for next round = Auction finished
            flash(f'Auction complete after Round {auction_round}! All players have been processed.', 'success')
            session['auction_started'] = False
            session['auction_complete'] = True
            session.pop('current_player_id', None)
            # Keep auction_round to display the final round number

        return redirect(url_for('auctions'))

    # --- If players are available for the current round ---
    random_player = random.choice(unsold_players)

    session['auction_started'] = True
    session['current_player_id'] = random_player.id
    session['round_complete'] = False # Actively auctioning
    session['auction_complete'] = False # Not complete yet

    return redirect(url_for('auctions'))

@app.route('/start_next_round')
@login_required
@role_required(['Admin'])
def start_next_round():
    # Allow starting next round even if paused (will auto-resume)
    auction_round = session.get('auction_round', 1)
    round_complete = session.get('round_complete', False)

    if not round_complete:
        flash('Cannot start next round until the current one is complete.', 'warning')
        return redirect(url_for('auctions'))

    # Find players marked as unsold in the completed round
    completed_round_status = f'Round {auction_round} Unsold'
    players_for_next_round = Player.query.filter_by(status=completed_round_status).all()

    if not players_for_next_round:
        flash('No players available for the next round.', 'info')
        # Mark auction as complete if trying to start next round with no players
        session['auction_complete'] = True
        session['auction_started'] = False
        session['round_complete'] = False # No longer in the 'waiting' state
        return redirect(url_for('auctions'))

    # Reset their status to 'Unsold' so they can be picked in the new round
    for player in players_for_next_round:
        player.status = 'Unsold'
    db.session.commit()

    # Update session state for the NEW round
    next_round_number = auction_round + 1
    session['auction_round'] = next_round_number
    session['round_complete'] = False # New round is starting, not complete yet
    session['auction_started'] = True # Auction becomes active again
    session['auction_paused'] = False # Ensure auction is not paused when starting next round

    flash(f'Starting Round {next_round_number}!', 'success')
    # Immediately go to the first player of the new round
    return redirect(url_for('next_player'))


@app.route('/sold/<int:player_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def mark_sold(player_id):
    if session.get('auction_paused'): # Prevent action if paused
        flash('Auction is paused. Resume before marking player sold.', 'warning')
        return redirect(url_for('auctions'))
    player = Player.query.get_or_404(player_id);
    if player.status != 'Unsold' or not session.get('auction_started') or session.get('current_player_id') != player_id:
        flash('This player is not currently up for auction or action already taken.', 'error'); return redirect(url_for('auctions'))
    try: team_id = int(request.form.get('team_id')); sold_price = int(request.form.get('sold_price'))
    except (ValueError, TypeError): flash('Invalid team or price.', 'error'); return redirect(url_for('auctions'))
    team = Team.query.get_or_404(team_id)
    if team.slots_remaining <= 0: flash(f'{team.team_name} has no remaining slots!', 'error'); return redirect(url_for('auctions'))
    if team.purse < sold_price: flash(f'{team.team_name} does not have enough purse (Remaining: {team.purse})!', 'error'); return redirect(url_for('auctions'))
    player.status = 'Sold'; player.sold_price = sold_price; player.team_id = team.id
    team.purse -= sold_price; team.purse_spent += sold_price; team.players_taken_count += 1; team.slots_remaining -= 1
    db.session.commit(); flash(f'{player.player_name} sold to {team.team_name} for {sold_price} points!', 'success')
    session.pop('current_player_id', None); return redirect(url_for('next_player'))


@app.route('/unsold/<int:player_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def mark_unsold(player_id):
    if session.get('auction_paused'): # Prevent action if paused
        flash('Auction is paused. Resume before marking player unsold.', 'warning')
        return redirect(url_for('auctions'))
    player = Player.query.get_or_404(player_id);
    if player.status != 'Unsold' or not session.get('auction_started') or session.get('current_player_id') != player_id:
        flash('This player is not currently up for auction or action already taken.', 'error'); return redirect(url_for('auctions'))
    auction_round = session.get('auction_round', 1); player.status = f'Round {auction_round} Unsold'
    flash_msg = f'{player.player_name} marked as unsold for Round {auction_round}. Available in next round.'
    db.session.commit(); flash(flash_msg, 'info'); session.pop('current_player_id', None)
    return redirect(url_for('next_player'))


@app.route('/restart_auction', methods=['GET', 'POST']) # Handles GET now too
@login_required
@role_required(['Admin'])
def restart_auction():
    if request.method == 'POST':
        # Check password confirmation
        if not current_user.is_authenticated:
             flash('Authentication error. Please log in again.', 'error')
             return redirect(url_for('login'))

        # Get password from the form
        password = request.form.get('password')

        # Check against the *currently logged-in* admin's password
        # Also ensure password was actually entered
        if not password or not current_user.check_password(password):
            flash('Invalid admin password. Auction not reset.', 'error')
            # Stay on the confirmation page if password fails
            return render_template('restart_confirm.html', active_page='auctions')

        # --- Proceed with Reset ---
        try: # Add error handling for database operations
            players_to_reset = Player.query.all()
            for player in players_to_reset:
                player.status = 'Unsold'; player.sold_price = 0; player.team_id = None
            teams_to_reset = Team.query.all()
            for team in teams_to_reset:
                team.purse = 10000; team.purse_spent = 0; team.players_taken_count = 0; team.slots_remaining = 15
            db.session.commit() # Commit all changes together

            # Clear session variables related to auction state
            session.pop('auction_started', None); session.pop('current_player_id', None)
            session.pop('auction_round', None); session.pop('round_complete', None)
            session.pop('auction_complete', None); session.pop('auction_paused', None)

            flash('Auction has been reset!', 'success')
            return redirect(url_for('auctions'))

        except Exception as e:
            db.session.rollback() # Rollback changes if an error occurred
            flash(f'An error occurred while resetting the auction: {e}', 'error')
            return redirect(url_for('auctions'))


    # If GET request, show confirmation page
    return render_template('restart_confirm.html', active_page='auctions')


@app.route('/pause_auction', methods=['POST'])
@login_required
@role_required(['Admin'])
def pause_auction():
    if not session.get('auction_started', False) or session.get('auction_complete', False):
        flash('Auction is not currently running or is already complete.', 'warning')
        return redirect(url_for('auctions'))

    session['auction_paused'] = True
    flash('Auction paused.', 'info')
    return redirect(url_for('auctions'))

@app.route('/resume_auction', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def resume_auction():
    if not session.get('auction_paused', False):
        flash('Auction is not paused.', 'warning')
        return redirect(url_for('auctions'))

    if request.method == 'POST':
        # Check password confirmation
        if not current_user.is_authenticated:
             flash('Authentication error. Please log in again.', 'error')
             return redirect(url_for('login'))

        password = request.form.get('password')

        # Check against the *currently logged-in* admin's password
        if not password or not current_user.check_password(password):
            flash('Invalid admin credentials. Auction not resumed.', 'error')
            # Stay on the confirmation page
            return render_template('resume_confirm.html', active_page='auctions')

        # --- Proceed with Resume ---
        session['auction_paused'] = False
        flash('Auction resumed.', 'success')
        # If a player was active when paused, stay on auction page
        if session.get('current_player_id'):
             return redirect(url_for('auctions'))
        else: # If paused between players or rounds, trigger next player/round logic
             return redirect(url_for('next_player'))

    # If GET request, show confirmation page
    return render_template('resume_confirm.html', active_page='auctions')


# --- ADMIN & SUPER ADMIN ROUTES ---
@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@role_required(['Admin']) # Only Admins and Super Admins
def create_user():
    teams = Team.query.all() # Get teams for dropdown
    if request.method == 'POST':
        full_name = request.form.get('full_name'); username = request.form.get('username'); password = request.form.get('password'); role = request.form.get('role'); team_id = request.form.get('team_id')
        if current_user.role == 'Admin' and role == 'Super Admin': flash('You do not have permission to create a Super Admin.', 'error'); return redirect(url_for('create_user'))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user: flash(f'Username "{username}" already exists.', 'error'); return redirect(url_for('create_user'))
        new_user = User(full_name=full_name, username=username, role=role, team_id=int(team_id) if team_id and role == 'Captain' else None)
        new_user.set_password(password); db.session.add(new_user); db.session.commit()
        flash(f'Login created for {full_name}!', 'success'); return redirect(url_for('dashboard'))
    return render_template('create_user.html', active_page='create_user', teams=teams)

# --- EXPORT ROUTE ---
@app.route('/export_team_excel/<int:team_id>')
@login_required # User must be logged in
def export_team_excel(team_id):
    team = Team.query.get_or_404(team_id)
    players_data = [{'Player Name': p.player_name, 'Sold Price': p.sold_price, 'Overall Matches': p.overall_matches, 'Overall Runs': p.overall_runs, 'Overall Wickets': p.overall_wickets, 'Overall Bat Avg': p.overall_bat_avg, 'Overall Bowl Avg': p.overall_bowl_avg} for p in team.players]
    if not players_data: flash(f"{team.team_name} has no players to export.", "info"); return redirect(url_for('teams'))
    df = pd.DataFrame(players_data); output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name=team.team_name)
    output.seek(0); return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=f'{team.team_name}_players.xlsx', as_attachment=True)


# --- RUN THE APP ---
if __name__ == '__main__':

    app.run(debug=True) # Run in debug mode for development

