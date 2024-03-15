from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
import socket
import ssl
import requests
import OpenSSL
import re
import smtplib
from email.mime.text import MIMEText
import yaml

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///certificates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)
scheduler = APScheduler()

# Load SMTP configuration from config.yaml
with open('config.yaml', 'r') as config_file:
    smtp_config = yaml.safe_load(config_file)

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False, unique=True)
    port = db.Column(db.Integer, nullable=False, default=443)
    email = db.Column(db.String(200))  # New field for email address
    issuer = db.Column(db.String(200))
    expiry_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    servers = Server.query.all()
    return render_template('index.html', servers=servers)

def extract_domain(url):
    pattern = r"(https?://)?(www\d?\.)?(?P<domain>[\w\.-]+\.\w+)"
    match = re.match(pattern, url)
    if match:
        domain = match.group("domain")
        return domain
    else:
        return None

@app.route('/add_server', methods=['POST'])
def add_server():
    name = request.form['name']
    url = request.form['url']
    port = request.form['port'] if 'port' in request.form else '443'
    email = request.form['email']  # New field for email address

    if not url.startswith("https://"):
        url = "https://" + url

    if not url:
        flash('URL is required!', 'error')
        return redirect('/')

    try:
        port = int(port)
    except ValueError:
        flash('Invalid port format!', 'error')
        return redirect('/')

    if port <= 0 or port > 65535:
        flash('Invalid port number!', 'error')
        return redirect('/')

    existing_server = Server.query.filter_by(url=url, port=port).first()
    if existing_server:
        flash('URL already exists!', 'error')
        return redirect('/')

    domain = extract_domain(url)
    if domain:
        if not server_exists(domain, port):
            flash('Server or domain does not exist or is not reachable on specified port!', 'error')
            return redirect('/')
    else:
        flash('Invalid URL format!', 'error')
        return redirect('/')

    issuer = get_cert_issuer(domain)
    expiry_date = get_cert_expiry_date(domain, port)
    status = get_cert_status(expiry_date)
    new_server = Server(name=name, url=url, port=port, email=email, issuer=issuer, expiry_date=expiry_date, status=status)
    db.session.add(new_server)
    db.session.commit()
    flash('Server added successfully!', 'success')
    return redirect('/')

@app.route('/remove_server/<int:server_id>', methods=['POST'])
def remove_server(server_id):
    server = Server.query.get_or_404(server_id)
    db.session.delete(server)
    db.session.commit()
    flash('Server removed successfully!', 'success')
    return redirect('/')

def server_exists(domain, port):
    try:
        response = requests.get(f"https://{domain}:{port}", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_cert_expiry_date(domain, port):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                return expiry_date
    except Exception as e:
        print(f"Error getting expiry date for {domain}:{port}: {e}")
        return None

def get_cert_issuer(domain):
    try:
        cert = ssl.get_server_certificate((domain, 443))
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        issuer = x509.get_issuer().commonName
        return issuer
    except Exception as e:
        print(f"Error getting issuer for {domain}: {e}")
        return ""

def get_cert_status(expiry_date):
    if not expiry_date:
        return "Invalid"
    today = datetime.now()
    delta = expiry_date - today
    if delta.days <= 90:
        return "Critical"
    elif delta.days <= 180:
        return "Info"
    else:
        return "OK"

def send_email(sender, recipient, subject, message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        mail = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
        mail.starttls()
        mail.login(smtp_config['username'], smtp_config['password'])
        mail.sendmail(sender, recipient, msg.as_string())
        mail.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

# Define the function to perform automated tasks
def scheduled_task():
    servers = Server.query.all()
    for server in servers:
        domain = extract_domain(server.url)
        if domain:
            if not server_exists(domain, server.port):
                flash(f'Server {server.name} or domain does not exist or is not reachable on specified port!', 'error')
                continue
            issuer = get_cert_issuer(domain)
            expiry_date = get_cert_expiry_date(domain, server.port)
            status = get_cert_status(expiry_date)
            server.issuer = issuer
            server.expiry_date = expiry_date
            server.status = status
            db.session.commit()
            if status == "Critical" and server.email:
                send_email(smtp_config['username'], server.email, "Certificate Expiry Alert", f"The certificate for {server.name} is expiring soon.")
        else:
            flash(f'Invalid URL format for {server.name}!', 'error')

# Configure the scheduler
scheduler.add_job(id='scheduled_task', func=scheduled_task, trigger='cron', hour=2)

# Start the scheduler with the Flask application
scheduler.init_app(app)
scheduler.start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
