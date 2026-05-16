"""
College Lost and Found Management System
Main application entry point.
"""
import os
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, request,
                   flash, abort, send_from_directory)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from config import Config
from models import db, User, Item, Claim


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables + a default admin on first run
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@college.edu').first():
            admin = User(
                name='Administrator',
                email='admin@college.edu',
                roll_number='ADMIN',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def save_upload(file_storage):
        """Save uploaded image and return relative filename, or None."""
        if not file_storage or file_storage.filename == '':
            return None
        if not allowed_file(file_storage.filename):
            flash('Invalid image format. Use PNG, JPG, JPEG, or GIF.', 'danger')
            return None
        filename = secure_filename(file_storage.filename)
        # Avoid collisions with a timestamp prefix
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_storage.save(path)
        return filename

    def admin_required(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_admin:
                abort(403)
            return f(*args, **kwargs)
        return wrapper

    # -----------------------------------------------------------------------
    # Public routes
    # -----------------------------------------------------------------------
    @app.route('/')
    def index():
        recent_lost = Item.query.filter_by(item_type='lost', status='open') \
            .order_by(Item.created_at.desc()).limit(6).all()
        recent_found = Item.query.filter_by(item_type='found', status='open') \
            .order_by(Item.created_at.desc()).limit(6).all()
        stats = {
            'total_lost': Item.query.filter_by(item_type='lost').count(),
            'total_found': Item.query.filter_by(item_type='found').count(),
            'resolved': Item.query.filter_by(status='resolved').count(),
            'users': User.query.count(),
        }
        return render_template('index.html',
                               recent_lost=recent_lost,
                               recent_found=recent_found,
                               stats=stats)

    @app.route('/browse')
    def browse():
        item_type = request.args.get('type', 'all')
        category = request.args.get('category', 'all')
        keyword = request.args.get('q', '').strip()

        query = Item.query.filter_by(status='open')
        if item_type in ('lost', 'found'):
            query = query.filter_by(item_type=item_type)
        if category != 'all':
            query = query.filter_by(category=category)
        if keyword:
            like = f'%{keyword}%'
            query = query.filter(or_(Item.title.ilike(like),
                                     Item.description.ilike(like),
                                     Item.location.ilike(like)))

        items = query.order_by(Item.created_at.desc()).all()
        return render_template('browse.html',
                               items=items,
                               item_type=item_type,
                               category=category,
                               keyword=keyword,
                               categories=Item.CATEGORIES)

    @app.route('/item/<int:item_id>')
    def item_detail(item_id):
        item = Item.query.get_or_404(item_id)
        possible_matches = []
        if item.item_type == 'lost' and item.status == 'open':
            possible_matches = Item.query.filter(
                Item.item_type == 'found',
                Item.status == 'open',
                Item.category == item.category,
            ).order_by(Item.created_at.desc()).limit(5).all()
        elif item.item_type == 'found' and item.status == 'open':
            possible_matches = Item.query.filter(
                Item.item_type == 'lost',
                Item.status == 'open',
                Item.category == item.category,
            ).order_by(Item.created_at.desc()).limit(5).all()

        return render_template('item_detail.html',
                               item=item,
                               possible_matches=possible_matches)

    # -----------------------------------------------------------------------
    # Auth
    # -----------------------------------------------------------------------
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            roll_number = request.form.get('roll_number', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            errors = []
            if not name or len(name) < 2:
                errors.append('Please enter a valid name.')
            if not email or '@' not in email:
                errors.append('Please enter a valid email.')
            if not roll_number:
                errors.append('Roll number is required.')
            if len(password) < 6:
                errors.append('Password must be at least 6 characters.')
            if password != confirm:
                errors.append('Passwords do not match.')
            if User.query.filter_by(email=email).first():
                errors.append('That email is already registered.')

            if errors:
                for e in errors:
                    flash(e, 'danger')
                return render_template('register.html')

            user = User(
                name=name,
                email=email,
                roll_number=roll_number,
                phone=phone,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash(f'Welcome back, {user.name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            flash('Invalid email or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # -----------------------------------------------------------------------
    # User dashboard
    # -----------------------------------------------------------------------
    @app.route('/dashboard')
    @login_required
    def dashboard():
        my_items = Item.query.filter_by(user_id=current_user.id) \
            .order_by(Item.created_at.desc()).all()
        my_claims = Claim.query.filter_by(claimant_id=current_user.id) \
            .order_by(Claim.created_at.desc()).all()
        # Claims made on items the user posted
        claims_on_my_items = Claim.query.join(Item) \
            .filter(Item.user_id == current_user.id) \
            .order_by(Claim.created_at.desc()).all()
        return render_template('dashboard.html',
                               my_items=my_items,
                               my_claims=my_claims,
                               claims_on_my_items=claims_on_my_items)

    # -----------------------------------------------------------------------
    # Reporting items
    # -----------------------------------------------------------------------
    @app.route('/report/<string:item_type>', methods=['GET', 'POST'])
    @login_required
    def report_item(item_type):
        if item_type not in ('lost', 'found'):
            abort(404)

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            location = request.form.get('location', '').strip()
            date_str = request.form.get('date_occurred', '').strip()
            contact_info = request.form.get('contact_info', '').strip()

            if not all([title, description, category, location, date_str]):
                flash('Please fill in all required fields.', 'danger')
                return render_template('report_item.html',
                                       item_type=item_type,
                                       categories=Item.CATEGORIES)

            try:
                date_occurred = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return render_template('report_item.html',
                                       item_type=item_type,
                                       categories=Item.CATEGORIES)

            image_filename = None
            if 'image' in request.files:
                image_filename = save_upload(request.files['image'])

            item = Item(
                title=title,
                description=description,
                category=category,
                location=location,
                date_occurred=date_occurred,
                contact_info=contact_info or current_user.phone or current_user.email,
                item_type=item_type,
                image_filename=image_filename,
                user_id=current_user.id,
            )
            db.session.add(item)
            db.session.commit()
            flash(f'Your {item_type} item has been posted successfully.', 'success')
            return redirect(url_for('item_detail', item_id=item.id))

        return render_template('report_item.html',
                               item_type=item_type,
                               categories=Item.CATEGORIES)

    @app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_item(item_id):
        item = Item.query.get_or_404(item_id)
        if item.user_id != current_user.id and not current_user.is_admin:
            abort(403)

        if request.method == 'POST':
            item.title = request.form.get('title', '').strip()
            item.description = request.form.get('description', '').strip()
            item.category = request.form.get('category', '').strip()
            item.location = request.form.get('location', '').strip()
            item.contact_info = request.form.get('contact_info', '').strip()
            date_str = request.form.get('date_occurred', '').strip()
            try:
                item.date_occurred = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

            if 'image' in request.files and request.files['image'].filename:
                new_image = save_upload(request.files['image'])
                if new_image:
                    item.image_filename = new_image

            db.session.commit()
            flash('Item updated.', 'success')
            return redirect(url_for('item_detail', item_id=item.id))

        return render_template('edit_item.html',
                               item=item,
                               categories=Item.CATEGORIES)

    @app.route('/item/<int:item_id>/delete', methods=['POST'])
    @login_required
    def delete_item(item_id):
        item = Item.query.get_or_404(item_id)
        if item.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted.', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/item/<int:item_id>/resolve', methods=['POST'])
    @login_required
    def resolve_item(item_id):
        item = Item.query.get_or_404(item_id)
        if item.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        item.status = 'resolved'
        item.resolved_at = datetime.utcnow()
        db.session.commit()
        flash('Item marked as resolved. Thanks for the update!', 'success')
        return redirect(url_for('item_detail', item_id=item.id))

    # -----------------------------------------------------------------------
    # Claims
    # -----------------------------------------------------------------------
    @app.route('/item/<int:item_id>/claim', methods=['POST'])
    @login_required
    def claim_item(item_id):
        item = Item.query.get_or_404(item_id)
        if item.user_id == current_user.id:
            flash("You can't claim your own item.", 'warning')
            return redirect(url_for('item_detail', item_id=item.id))
        if item.status != 'open':
            flash('This item is no longer open.', 'warning')
            return redirect(url_for('item_detail', item_id=item.id))

        existing = Claim.query.filter_by(item_id=item.id,
                                         claimant_id=current_user.id).first()
        if existing:
            flash('You have already submitted a claim for this item.', 'info')
            return redirect(url_for('item_detail', item_id=item.id))

        message = request.form.get('message', '').strip()
        if not message:
            flash('Please describe why this item is yours.', 'danger')
            return redirect(url_for('item_detail', item_id=item.id))

        claim = Claim(
            item_id=item.id,
            claimant_id=current_user.id,
            message=message,
        )
        db.session.add(claim)
        db.session.commit()
        flash('Your claim has been submitted. The poster will contact you.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))

    @app.route('/claim/<int:claim_id>/<string:action>', methods=['POST'])
    @login_required
    def handle_claim(claim_id, action):
        claim = Claim.query.get_or_404(claim_id)
        # Only the item poster (or admin) can approve / reject
        if claim.item.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        if action not in ('approve', 'reject'):
            abort(400)

        if action == 'approve':
            claim.status = 'approved'
            claim.item.status = 'resolved'
            claim.item.resolved_at = datetime.utcnow()
            flash('Claim approved. Item marked as resolved.', 'success')
        else:
            claim.status = 'rejected'
            flash('Claim rejected.', 'info')

        db.session.commit()
        return redirect(url_for('dashboard'))

    # -----------------------------------------------------------------------
    # Admin
    # -----------------------------------------------------------------------
    @app.route('/admin')
    @admin_required
    def admin_panel():
        users = User.query.order_by(User.created_at.desc()).all()
        items = Item.query.order_by(Item.created_at.desc()).all()
        claims = Claim.query.order_by(Claim.created_at.desc()).all()
        stats = {
            'total_users': len(users),
            'total_items': len(items),
            'open_items': sum(1 for i in items if i.status == 'open'),
            'resolved_items': sum(1 for i in items if i.status == 'resolved'),
            'pending_claims': sum(1 for c in claims if c.status == 'pending'),
        }
        return render_template('admin.html',
                               users=users,
                               items=items,
                               claims=claims,
                               stats=stats)

    @app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
    @admin_required
    def toggle_user(user_id):
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You can't deactivate yourself.", 'warning')
            return redirect(url_for('admin_panel'))
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash(f'User {user.name} is now '
              f'{"active" if user.is_active_account else "inactive"}.', 'info')
        return redirect(url_for('admin_panel'))

    # -----------------------------------------------------------------------
    # Uploaded files
    # -----------------------------------------------------------------------
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # -----------------------------------------------------------------------
    # Error handlers
    # -----------------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(_):
        return render_template('error.html', code=403,
                               message="You don't have permission to do that."), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template('error.html', code=404,
                               message='The page you requested was not found.'), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template('error.html', code=500,
                               message='Something went wrong on our end.'), 500

    # Context processor: small helpers for templates
    @app.context_processor
    def inject_globals():
        return {'current_year': datetime.utcnow().year}

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_DEBUG', '1') == '1')
