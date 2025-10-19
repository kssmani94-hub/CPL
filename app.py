import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from models import db, User, Team, Player # Keep your existing models import
from dotenv import load_dotenv
import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import random
from flask import send_file # Add or ensure this is present
import pandas as pd
import io
from sqlalchemy import inspect # Needed for checking if tables exist

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///project.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_to_change_later_98765') # Use environment variable or fallback
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
    # Only run table creation/seeding logic once per app startup
    if not hasattr(app, 'tables_created'):
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables_exist = inspector.has_table("user") # Check just one table

            if not tables_exist:
                db.create_all()
                print("Database tables created.")
                # --- Seed Super Admin ---
                if User.query.count() == 0:
                    print("Creating Super Admin...")
                    super_admin = User( full_name="Super Admin", username="superadmin", role="Super Admin")
                    super_admin.set_password("admin123")
                    db.session.add(super_admin)
                    db.session.commit()
                    print("Super Admin created...")
                # --- Seed Teams ---
                if Team.query.count() == 0:
                     teams = [ Team(team_name="Puthiya Sirakukal", captain_name="Govindaraj"), Team(team_name="APJ Tamizhan Youngstars", captain_name="Silambu R"), Team(team_name="Mighty Cricket Club", captain_name="Barathi K"), Team(team_name="SPARTAN ROCKERZ", captain_name="Barathi K"), Team(team_name="Crazy-11", captain_name="Nithyaraj"), Team(team_name="Jolly Players", captain_name="Vinoth"), Team(team_name="Dada Warriors", captain_name="Praveen prabhakaran"), Team(team_name="Thunder Strikers", captain_name="Gurunathan S") ]
                     db.session.bulk_save_objects(teams); db.session.commit(); print(f"{len(teams)} teams seeded.")
                # --- Seed Players (Corrected Indentation & Filenames) ---
                if Player.query.count() == 0: # Only seed if player table is empty
                    print("Attempting to seed players...")
                    players_to_seed = [
                        Player( player_name="Vasanth Ab", image_filename="vasanth_ab.png", cpl_2024_team="Crazy-11", cpl_2024_innings=8, cpl_2024_runs=302, cpl_2024_average=50.33, cpl_2024_sr=107.86, cpl_2024_hs=75, overall_matches=135, overall_runs=2813, overall_wickets=38, overall_bat_avg=25.81, overall_bowl_avg=21.61),
                        Player( player_name="Mukil Hitman", image_filename="mukil_hitman.jpg", cpl_2024_team="Thunder Strikers", cpl_2024_innings=9, cpl_2024_runs=268, cpl_2024_average=29.78, cpl_2024_sr=120.18, cpl_2024_hs=46, overall_matches=263, overall_runs=7278, overall_wickets=99, overall_bat_avg=31.51, overall_bowl_avg=20.73),
                        Player( player_name="M Govindaraj", image_filename="govindaraj.png", cpl_2024_team="Puthiya Sirakukal", cpl_2024_innings=6, cpl_2024_runs=223, cpl_2024_average=44.60, cpl_2024_sr=153.79, cpl_2024_hs=95, overall_matches=83, overall_runs=2098, overall_wickets=56, overall_bat_avg=29.14, overall_bowl_avg=15.32),
                        Player( player_name="Nithesh Kumar", image_filename="nithesh_kumar.png", cpl_2024_team="APJ Tamizhan Youngstars", cpl_2024_innings=8, cpl_2024_runs=194, cpl_2024_average=24.25, cpl_2024_sr=125.16, cpl_2024_hs=87, overall_matches=220, overall_runs=3485, overall_wickets=77, overall_bat_avg=21.65, overall_bowl_avg=26.03),
                        Player( player_name="Poovarasan", image_filename="poovarasan.png", cpl_2024_team="SPARTAN ROCKERZ", cpl_2024_innings=6, cpl_2024_runs=186, cpl_2024_average=31.00, cpl_2024_sr=137.78, cpl_2024_hs=63, overall_matches=237, overall_runs=5776, overall_wickets=157, overall_bat_avg=29.03, overall_bowl_avg=19.72),
                        Player( player_name="R Raja", image_filename="r_raja.png", cpl_2024_team="APJ Tamizhan Youngstars", cpl_2024_innings=8, cpl_2024_runs=171, cpl_2024_average=21.38, cpl_2024_sr=133.59, cpl_2024_hs=61, overall_matches=118, overall_runs=1971, overall_wickets=49, overall_bat_avg=18.95, overall_bowl_avg=13.31),
                        Player( player_name="Silambu R", image_filename="silambu_r.png", cpl_2024_team="APJ Tamizhan Youngstars", cpl_2024_innings=8, cpl_2024_runs=147, cpl_2024_average=24.50, cpl_2024_sr=125.64, cpl_2024_hs=46, overall_matches=109, overall_runs=1908, overall_wickets=147, overall_bat_avg=23.27, overall_bowl_avg=12.35),
                        Player( player_name="Prabha", image_filename="prabha.png", cpl_2024_team="Jolly Players", cpl_2024_innings=6, cpl_2024_runs=136, cpl_2024_average=45.33, cpl_2024_sr=107.09, cpl_2024_hs=29, overall_matches=279, overall_runs=6883, overall_wickets=195, overall_bat_avg=35.48, overall_bowl_avg=13.39),
                        Player( player_name="Hariharan R", image_filename="hariharan_r.png", cpl_2024_team="Thunder Strikers", cpl_2024_innings=9, cpl_2024_runs=130, cpl_2024_average=14.44, cpl_2024_sr=83.33, cpl_2024_hs=34, overall_matches=142, overall_runs=1984, overall_wickets=81, overall_bat_avg=17.71, overall_bowl_avg=18.36),
                        Player( player_name="Ramesh G", image_filename=None, cpl_2024_team="APJ Tamizhan Youngstars", cpl_2024_innings=8, cpl_2024_runs=126, cpl_2024_average=18.00, cpl_2024_sr=104.13, cpl_2024_hs=39, overall_matches=87, overall_runs=1156, overall_wickets=46, overall_bat_avg=18.35, overall_bowl_avg=20.78),
                    ]
                    db.session.bulk_save_objects(players_to_seed)
                    db.session.commit()
                    print(f"{len(players_to_seed)} players seeded.")
                # Removed the 'else' block that checked for missing players to simplify seeding logic
                # Seeding now strictly happens only if the tables don't exist initially.

            else: # If tables already exist
                print("Database tables already exist.")
        app.tables_created = True # Mark tables as created/checked for this app run


# --- CUSTOM DECORATORS for security ---
def role_required(role_names):
    if not isinstance(role_names, list): role_names = [role_names]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated: return login_manager.unauthorized()
            if current_user.role != 'Super Admin' and current_user.role not in role_names:
                flash('You do not have permission to access this page.', 'error'); return redirect(url_for('dashboard')) # Redirect to dashboard for permission errors
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
    if current_user.is_authenticated:
         # If already logged in, redirect based on role
         if current_user.role == 'Captain':
             return redirect(url_for('teams')) # Captains go to Teams
         else:
             return redirect(url_for('dashboard')) # Admins/Super Admins go to Dashboard

    if request.method == 'POST':
        username = request.form.get('username'); password = request.form.get('password'); user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user); flash('Logged in successfully!', 'success')
            # Redirect based on role AFTER login
            if user.role == 'Captain':
                return redirect(url_for('teams')) # Captains go to Teams page
            else:
                return redirect(url_for('dashboard')) # Admins/Super Admins go to Dashboard
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
@role_required(['Admin']) # Only Admins/Super Admins allowed
def dashboard():
    all_users = []
    if current_user.role == 'Super Admin':
        all_users = User.query.filter(User.id != current_user.id).order_by(User.role, User.full_name).all()
    return render_template('dashboard.html', active_page='dashboard', all_users=all_users)


@app.route('/players')
@login_required
def players():
    all_players = Player.query.all()
    return render_template('players.html', active_page='players', players=all_players)

# --- TEAMS ROUTE (PUBLIC) ---
@app.route('/teams')
def teams():
    all_teams = Team.query.options(db.joinedload(Team.players)).all()
    return render_template('teams.html',
                           active_page='teams',
                           teams=all_teams,
                           current_user=current_user) # Pass current_user

# --- AUCTION ROUTES (PUBLIC, content conditional) ---
@app.route('/auctions')
def auctions():
    all_teams = Team.query.all()
    auction_started = session.get('auction_started', False)
    auction_round = session.get('auction_round', 1)
    round_complete = session.get('round_complete', False)
    auction_complete = session.get('auction_complete', False)
    auction_paused = session.get('auction_paused', False)
    current_player = None
    next_round_players_count = 0

    if auction_started and not round_complete and not auction_complete and not auction_paused:
        player_id = session.get('current_player_id')
        if player_id:
            current_player = Player.query.get(player_id)
            if current_player and current_player.status != 'Unsold':
                 session.pop('current_player_id', None)
                 # Redirect immediately only if user is admin to avoid loops for visitors
                 if current_user.is_authenticated and current_user.role in ['Admin', 'Super Admin']:
                    return redirect(url_for('next_player'))
                 else:
                    current_player = None # Clear player for non-admins

    if round_complete:
        next_round_status = f'Round {auction_round} Unsold'
        next_round_players_count = Player.query.filter_by(status=next_round_status).count()
        if next_round_players_count == 0:
             auction_complete = True; auction_started = False
             session['auction_complete'] = True; session['auction_started'] = False

    return render_template('auctions.html',
                           active_page='auctions', all_teams=all_teams,
                           auction_started=auction_started, round_complete=round_complete,
                           auction_complete=auction_complete, auction_paused=auction_paused,
                           next_round_players_count=next_round_players_count,
                           auction_round=auction_round, player=current_player,
                           current_user=current_user) # Pass current_user


@app.route('/next_player')
@login_required
@role_required(['Admin'])
def next_player():
    if session.get('auction_paused'): flash('Auction is paused. Resume before proceeding.', 'warning'); return redirect(url_for('auctions'))
    auction_round = session.get('auction_round', 1); current_round_status = 'Unsold'; next_round_status_check = f'Round {auction_round} Unsold'; unsold_players = Player.query.filter_by(status=current_round_status).all()
    if not unsold_players:
        players_for_next_round_count = Player.query.filter_by(status=next_round_status_check).count()
        if players_for_next_round_count > 0: flash(f'Round {auction_round} complete. Ready for Round {auction_round + 1}.', 'info'); session['round_complete'] = True; session['auction_started'] = False; session.pop('current_player_id', None)
        else: flash(f'Auction complete after Round {auction_round}! All players processed.', 'success'); session['auction_started'] = False; session['auction_complete'] = True; session.pop('current_player_id', None)
        return redirect(url_for('auctions'))
    random_player = random.choice(unsold_players); session['auction_started'] = True; session['current_player_id'] = random_player.id; session['round_complete'] = False; session['auction_complete'] = False
    return redirect(url_for('auctions'))

@app.route('/start_next_round')
@login_required
@role_required(['Admin'])
def start_next_round():
    auction_round = session.get('auction_round', 1); round_complete = session.get('round_complete', False)
    if not round_complete: flash('Cannot start next round until the current one is complete.', 'warning'); return redirect(url_for('auctions'))
    completed_round_status = f'Round {auction_round} Unsold'; players_for_next_round = Player.query.filter_by(status=completed_round_status).all()
    if not players_for_next_round: flash('No players available for the next round.', 'info'); session['auction_complete'] = True; session['auction_started'] = False; session['round_complete'] = False; return redirect(url_for('auctions'))
    for player in players_for_next_round: player.status = 'Unsold'
    db.session.commit(); next_round_number = auction_round + 1; session['auction_round'] = next_round_number; session['round_complete'] = False; session['auction_started'] = True; session['auction_paused'] = False
    flash(f'Starting Round {next_round_number}!', 'success'); return redirect(url_for('next_player'))


@app.route('/sold/<int:player_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def mark_sold(player_id):
    if session.get('auction_paused'): flash('Auction is paused. Resume before marking player sold.', 'warning'); return redirect(url_for('auctions'))
    player = Player.query.get_or_404(player_id);
    if player.status != 'Unsold' or not session.get('auction_started') or session.get('current_player_id') != player_id: flash('This player is not currently up for auction or action already taken.', 'error'); return redirect(url_for('auctions'))
    try: team_id = int(request.form.get('team_id')); sold_price = int(request.form.get('sold_price'))
    except (ValueError, TypeError): flash('Invalid team or price.', 'error'); return redirect(url_for('auctions'))
    team = Team.query.get_or_404(team_id)
    if team.slots_remaining <= 0: flash(f'{team.team_name} has no remaining slots!', 'error'); return redirect(url_for('auctions'))
    if team.purse < sold_price: flash(f'{team.team_name} does not have enough purse (Remaining: {team.purse})!', 'error'); return redirect(url_for('auctions'))
    player.status = 'Sold'; player.sold_price = sold_price; player.team_id = team.id; team.purse -= sold_price; team.purse_spent += sold_price; team.players_taken_count += 1; team.slots_remaining -= 1
    db.session.commit(); flash(f'{player.player_name} sold to {team.team_name} for {sold_price} points!', 'success')
    session.pop('current_player_id', None); return redirect(url_for('next_player'))


@app.route('/unsold/<int:player_id>', methods=['POST'])
@login_required
@role_required(['Admin'])
def mark_unsold(player_id):
    if session.get('auction_paused'): flash('Auction is paused. Resume before marking player unsold.', 'warning'); return redirect(url_for('auctions'))
    player = Player.query.get_or_404(player_id);
    if player.status != 'Unsold' or not session.get('auction_started') or session.get('current_player_id') != player_id: flash('This player is not currently up for auction or action already taken.', 'error'); return redirect(url_for('auctions'))
    auction_round = session.get('auction_round', 1); player.status = f'Round {auction_round} Unsold'; flash_msg = f'{player.player_name} marked as unsold for Round {auction_round}. Available in next round.'
    db.session.commit(); flash(flash_msg, 'info'); session.pop('current_player_id', None)
    return redirect(url_for('next_player'))


@app.route('/restart_auction', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def restart_auction():
    if request.method == 'POST':
        if not current_user.is_authenticated: flash('Authentication error. Please log in again.', 'error'); return redirect(url_for('login'))
        password = request.form.get('password')
        if not password or not current_user.check_password(password): flash('Invalid admin password. Auction not reset.', 'error'); return render_template('restart_confirm.html', active_page='auctions')
        try:
            players_to_reset = Player.query.all();
            for player in players_to_reset: player.status = 'Unsold'; player.sold_price = 0; player.team_id = None
            teams_to_reset = Team.query.all();
            for team in teams_to_reset: team.purse = 10000; team.purse_spent = 0; team.players_taken_count = 0; team.slots_remaining = 15
            db.session.commit()
            session.pop('auction_started', None); session.pop('current_player_id', None); session.pop('auction_round', None); session.pop('round_complete', None); session.pop('auction_complete', None); session.pop('auction_paused', None)
            flash('Auction has been reset!', 'success'); return redirect(url_for('auctions'))
        except Exception as e: db.session.rollback(); flash(f'An error occurred while resetting the auction: {e}', 'error'); return redirect(url_for('auctions'))
    return render_template('restart_confirm.html', active_page='auctions')


@app.route('/pause_auction', methods=['POST'])
@login_required
@role_required(['Admin'])
def pause_auction():
    if not session.get('auction_started', False) or session.get('auction_complete', False): flash('Auction is not currently running or is already complete.', 'warning'); return redirect(url_for('auctions'))
    session['auction_paused'] = True; flash('Auction paused.', 'info'); return redirect(url_for('auctions'))

@app.route('/resume_auction', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def resume_auction():
    if not session.get('auction_paused', False): flash('Auction is not paused.', 'warning'); return redirect(url_for('auctions'))
    if request.method == 'POST':
        if not current_user.is_authenticated: flash('Authentication error. Please log in again.', 'error'); return redirect(url_for('login'))
        password = request.form.get('password')
        if not password or not current_user.check_password(password): flash('Invalid admin credentials. Auction not resumed.', 'error'); return render_template('resume_confirm.html', active_page='auctions')
        session['auction_paused'] = False; flash('Auction resumed.', 'success')
        if session.get('current_player_id'): return redirect(url_for('auctions'))
        else: return redirect(url_for('next_player'))
    return render_template('resume_confirm.html', active_page='auctions')


# --- ADMIN & SUPER ADMIN ROUTES ---
@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def create_user():
    teams = Team.query.all()
    if request.method == 'POST':
        full_name = request.form.get('full_name'); username = request.form.get('username'); password = request.form.get('password'); role = request.form.get('role'); team_id = request.form.get('team_id')
        if current_user.role == 'Admin' and role in ['Super Admin', 'Admin']:
             flash('Admins can only create Captains.', 'error'); return redirect(url_for('create_user'))
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
    team = Team.query.get_or_404(team_id) # Get team or return 404 error if not found

    # Security Check: User must be logged in (already handled by @login_required)
    # No need for extra checks as all logged-in users can export per your last request

    players_data = []
    # Loop through players associated with the specific team
    for player in team.players:
        players_data.append({
            'Player Name': player.player_name,
            'Sold Price': player.sold_price,
            'Overall Matches': player.overall_matches,
            'Overall Runs': player.overall_runs,
            'Overall Wickets': player.overall_wickets,
            'Overall Bat Avg': player.overall_bat_avg,
            'Overall Bowl Avg': player.overall_bowl_avg,
            # Add more CPL 2024 stats if desired
            'CPL 2024 Team': player.cpl_2024_team,
            'CPL 2024 Innings': player.cpl_2024_innings,
            'CPL 2024 Runs': player.cpl_2024_runs,
            'CPL 2024 Average': player.cpl_2024_average,
            'CPL 2024 SR': player.cpl_2024_sr,
            'CPL 2024 HS': player.cpl_2024_hs,
        })

    # Check if there's any data to export
    if not players_data:
        flash(f"{team.team_name} has no players to export.", "info")
        return redirect(url_for('teams')) # Redirect back to the teams page

    # Create a Pandas DataFrame
    df = pd.DataFrame(players_data)

    # Create an in-memory Excel file (BytesIO buffer)
    output = io.BytesIO()
    # Use context manager for ExcelWriter to ensure resources are managed
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=team.team_name)
    output.seek(0) # Go to the beginning of the buffer

    # Send the in-memory file to the user's browser as a download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # Standard Excel MIME type
        download_name=f'{team.team_name}_players.xlsx', # Filename for the download
        as_attachment=True # Tell the browser to download the file
    )

# --- NEW ROUTE TO EDIT USER ---
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Super Admin']) # Only Super Admins can edit
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id) # Find the user or show 404 error
    teams = Team.query.all() # Get teams for the dropdown

    if request.method == 'POST':
        # Get data from the submitted form
        new_full_name = request.form.get('full_name')
        new_username = request.form.get('username')
        new_role = request.form.get('role')
        new_team_id = request.form.get('team_id')
        new_password = request.form.get('password') # Optional new password

        # --- Validation ---
        # Check if username changed and if the new one is taken by *another* user
        if new_username != user_to_edit.username and User.query.filter(User.username == new_username, User.id != user_id).first():
            flash(f'Username "{new_username}" is already taken.', 'error')
            # Reload the edit page with current data
            return render_template('edit_user.html', active_page='dashboard', user=user_to_edit, teams=teams)

        # --- Update User Data ---
        user_to_edit.full_name = new_full_name
        user_to_edit.username = new_username
        user_to_edit.role = new_role
        # Only set team if the role is Captain
        user_to_edit.team_id = int(new_team_id) if new_team_id and new_role == 'Captain' else None

        # Only update password if a new one was entered
        if new_password:
            user_to_edit.set_password(new_password)
            flash('Password updated successfully.', 'info') # Optional feedback

        try:
            db.session.commit() # Save the changes to the database
            flash(f'User "{user_to_edit.full_name}" updated successfully!', 'success')
            return redirect(url_for('dashboard')) # Go back to the dashboard
        except Exception as e:
            db.session.rollback() # Undo changes if error
            flash(f'Error updating user: {e}', 'error')

    # If GET request, show the pre-filled form
    return render_template('edit_user.html',
                           active_page='dashboard', # Keep dashboard highlighted in nav
                           user=user_to_edit, # Pass the user object to the template
                           teams=teams)         # Pass the teams list
                           # --- NEW ROUTE TO DELETE USER ---
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Super Admin']) # Only Super Admins can delete
def delete_user(user_id):
    # Prevent super admin from deleting themselves
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('dashboard'))

    user_to_delete = User.query.get_or_404(user_id) # Find user or show 404

    try:
        # Check if the user is a captain and might be linked to a team
        # (Handle this relationship if necessary, e.g., set team.captain_id to None)
        # For simplicity now, we just delete. Add relationship handling if needed.

        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User "{user_to_delete.username}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {e}', 'error')

    return redirect(url_for('dashboard')) # Redirect back to the dashboard
# --- RUN THE APP ---
# This should be the last part of your file
if __name__ == '__main__':
    app.run(debug=True)
