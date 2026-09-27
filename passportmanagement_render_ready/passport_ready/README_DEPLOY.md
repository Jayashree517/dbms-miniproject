# Deploy Passport Application Management System on Render

1. Upload this project to a GitHub repository.
2. In Render, choose New -> Web Service and connect the GitHub repository.
3. Set Root Directory to `passportmanagement` only if the repository contains a parent folder with this project inside it. If the repository itself contains `app.py`, leave Root Directory blank.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Add environment variable:
   - Key: `SECRET_KEY`
   - Value: use a long random secret string.
7. Create the service. Render will provide a public `onrender.com` URL.

Notes:
- This project uses SQLite (`passport.db`). It is suitable for a small college demo, but Render's normal web-service filesystem is not a durable production database. For a real production application, use a hosted database such as PostgreSQL.
- Do not enter real Aadhaar, passport, phone, email, or other sensitive personal information into the public demo. Use test data.
- The demo admin account currently created by the application is username `admin` and password `admin123`. Change this before using the application outside a classroom demo.
