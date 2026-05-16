# College Lost and Found Management System

A full-stack web application that helps students at a college **report lost items, post found items, and reunite people with their belongings**. Built with Flask, SQLAlchemy, and Bootstrap 5.

> **Project type:** Mini-project / final-year project, Python + Flask
> **Stack:** Flask · SQLAlchemy · SQLite (dev) / PostgreSQL (prod) · Flask-Login · Bootstrap 5

---

## Features

### For Students
- Sign up with name, roll number, college email, and phone
- Secure login (passwords hashed with Werkzeug)
- **Report a lost item** with title, category, location, date, photo, and description
- **Report a found item** with the same details
- **Browse & search** all open posts; filter by type and category
- **Submit a claim** on someone else's found item with a verification message
- **Approve / reject** claims made on your own posts
- Personal **dashboard** showing your posts, your claims, and claims on your posts
- Edit, delete, or mark your posts as resolved
- "Possible matches" automatically suggested between lost and found items

### For Admins
- Default admin account is created automatically on first run
- View overall stats (users, items, claims)
- See all items, all users, all claims in one place
- Activate / deactivate user accounts
- Delete any post in the system

### Technical
- Image uploads with size and extension validation
- Session-based authentication
- CSRF-safe POST routes
- Responsive design (mobile + desktop)
- Custom 403 / 404 / 500 error pages
- Production-ready with `gunicorn`

---

## Project Structure

```
lost-and-found/
├── app.py                   # Main Flask application + routes
├── models.py                # SQLAlchemy models (User, Item, Claim)
├── config.py                # Configuration class
├── requirements.txt         # Python dependencies
├── Procfile                 # Process file for Heroku / Render / Railway
├── runtime.txt              # Python version
├── render.yaml              # Render.com deployment config
├── .gitignore
├── .env.example             # Example environment variables
├── README.md
├── templates/
│   ├── base.html            # Base layout with nav + footer
│   ├── _item_card.html      # Reusable item card partial
│   ├── index.html           # Homepage
│   ├── browse.html          # Browse & search items
│   ├── item_detail.html     # Single item view + claim form
│   ├── report_item.html     # Report lost or found
│   ├── edit_item.html       # Edit existing post
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html       # Personal dashboard
│   ├── admin.html           # Admin panel
│   └── error.html           # Generic error page
├── static/
│   ├── css/style.css        # Custom stylesheet
│   └── uploads/             # User-uploaded item photos
└── instance/                # SQLite DB lives here (auto-created)
```

---

## Database Schema

**User**: id, name, email, roll_number, phone, password_hash, is_admin, is_active_account, created_at

**Item**: id, title, description, category, location, date_occurred, contact_info, item_type (`lost`/`found`), status (`open`/`resolved`), image_filename, created_at, resolved_at, user_id (FK)

**Claim**: id, message, status (`pending`/`approved`/`rejected`), created_at, item_id (FK), claimant_id (FK)

---

## Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/lost-and-found.git
cd lost-and-found
```

### 2. Create a virtual environment
**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

### Default admin credentials
```
Email:    admin@college.edu
Password: admin123
```
**Change these immediately in production!**

---

## Deploying to a Live URL

You haven't lost anything by reading this far — let's get it online.

### Option A — Render.com (recommended, easiest, free tier)

1. **Push your code to GitHub** (see "Pushing to GitHub" below).
2. Go to [render.com](https://render.com) and sign up with GitHub.
3. Click **New +** → **Web Service**.
4. Connect your repository.
5. Render auto-detects `render.yaml`. If not, fill in:
   - **Environment:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
6. Click **Create Web Service**. First build takes ~2–4 minutes.
7. Your app will be live at `https://<your-service-name>.onrender.com`.

**Note:** The free tier puts your app to sleep after ~15 min of inactivity. The first request after sleep takes 30–60s to wake up — totally fine for a demo.

**Persistent uploads on Render free tier:** the filesystem is ephemeral, so uploaded images will reset on every redeploy. For a college demo that's usually OK. To persist across deploys, add a [Render Disk](https://render.com/docs/disks) or wire up Cloudinary / AWS S3.

### Option B — PythonAnywhere (free, no sleep)

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com).
2. Open a Bash console and clone your repo.
3. Create a virtualenv and `pip install -r requirements.txt`.
4. **Web tab** → **Add a new web app** → **Manual configuration** → **Python 3.11**.
5. Edit the WSGI config to point at `app.py` (the `app` variable).
6. Set the static files mapping: `/static/` → `/home/<user>/lost-and-found/static`.
7. Reload. Your app is live at `https://<username>.pythonanywhere.com`.

### Option C — Railway, Fly.io, Vercel (Python serverless)
All work similarly. Push to GitHub, connect the repo, and they auto-detect the Procfile.

---

## Pushing to GitHub

```bash
# from inside the lost-and-found folder
git init
git add .
git commit -m "Initial commit: College Lost and Found Management System"

# create a new empty repo on github.com, then:
git branch -M main
git remote add origin https://github.com/<your-username>/lost-and-found.git
git push -u origin main
```

---

## Tech Stack

| Layer        | Technology                       |
|--------------|----------------------------------|
| Backend      | Python 3.11, Flask 3             |
| Database ORM | SQLAlchemy 2 + Flask-SQLAlchemy  |
| Database     | SQLite (dev) / PostgreSQL (prod) |
| Auth         | Flask-Login                      |
| Frontend     | Jinja2, Bootstrap 5, Bootstrap Icons |
| Fonts        | Plus Jakarta Sans, Fraunces      |
| Production server | Gunicorn                    |

---

## Possible Future Enhancements

- Email notifications when a claim is submitted
- In-app chat between poster and claimant
- QR codes for physical lost & found boxes
- Image similarity (CV) for auto-matching items
- Mobile app (React Native / Flutter) using the same backend as an API

---

## License

MIT. Free for any educational use.
