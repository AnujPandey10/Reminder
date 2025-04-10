from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta, date
import threading, schedule, time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reminder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration (using Gmail as an example)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''        # Replace with your email
app.config['MAIL_PASSWORD'] = ''         # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'anujmukul9@gmail.com'
mail = Mail(app)

db = SQLAlchemy(app)

# Association table for many-to-many relationship between Reminders and Recipients
reminder_recipients = db.Table('reminder_recipients',
    db.Column('reminder_id', db.Integer, db.ForeignKey('reminder.id'), primary_key=True),
    db.Column('recipient_id', db.Integer, db.ForeignKey('recipient.id'), primary_key=True)
)

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    location = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))

    def __repr__(self):
        return f'<Recipient {self.name}>'

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_detail = db.Column(db.String(200), nullable=False)
    reminder_type = db.Column(db.String(50))
    purpose = db.Column(db.String(200))
    next_reminder_date = db.Column(db.Date, nullable=False)
    recurring = db.Column(db.Boolean, default=False)
    interval_days = db.Column(db.Integer, default=0)  # Interval (in days) for recurring reminders
    recipients = db.relationship('Recipient', secondary=reminder_recipients, lazy='subquery',
        backref=db.backref('reminders', lazy=True))

    def __repr__(self):
        return f'<Reminder {self.task_detail} on {self.next_reminder_date}>'

# -------------------------
# Recipient CRUD Operations
# -------------------------

@app.route('/recipients', methods=['GET', 'POST'])
def manage_recipients():
    if request.method == 'POST':
        name = request.form['name']
        designation = request.form.get('designation', '')
        location = request.form.get('location', '')
        email_addr = request.form['email']
        phone = request.form.get('phone', '')
        new_recipient = Recipient(name=name, designation=designation, location=location, email=email_addr, phone=phone)
        db.session.add(new_recipient)
        db.session.commit()
        flash('Recipient added successfully!')
        return redirect(url_for('manage_recipients'))
    recipients = Recipient.query.all()
    return render_template('recipients.html', recipients=recipients)

@app.route('/edit_recipient/<int:id>', methods=['GET', 'POST'])
def edit_recipient(id):
    recipient = Recipient.query.get_or_404(id)
    if request.method == 'POST':
        recipient.name = request.form['name']
        recipient.designation = request.form.get('designation', '')
        recipient.location = request.form.get('location', '')
        recipient.email = request.form['email']
        recipient.phone = request.form.get('phone', '')
        db.session.commit()
        flash('Recipient updated successfully!')
        return redirect(url_for('manage_recipients'))
    return render_template('edit_recipient.html', recipient=recipient)

@app.route('/delete_recipient/<int:id>', methods=['POST'])
def delete_recipient(id):
    recipient = Recipient.query.get_or_404(id)
    db.session.delete(recipient)
    db.session.commit()
    flash('Recipient deleted successfully!')
    return redirect(url_for('manage_recipients'))

# -------------------------
# Reminder CRUD Operations
# -------------------------

@app.route('/')
def index():
    reminders = Reminder.query.all()
    return render_template('index.html', reminders=reminders)

@app.route('/add_reminder', methods=['GET', 'POST'])
def add_reminder():
    if request.method == 'POST':
        task_detail = request.form['task_detail']
        reminder_type = request.form['reminder_type']
        purpose = request.form['purpose']
        next_date_str = request.form['next_reminder_date']
        next_reminder_date = datetime.strptime(next_date_str, '%Y-%m-%d').date()
        recurring = True if request.form.get('recurring') == 'on' else False
        interval_days = int(request.form['interval_days']) if recurring else 0
        recipient_ids = request.form.getlist('recipients')
        reminder = Reminder(task_detail=task_detail, reminder_type=reminder_type, purpose=purpose,
                            next_reminder_date=next_reminder_date, recurring=recurring, interval_days=interval_days)
        for rid in recipient_ids:
            recipient = Recipient.query.get(int(rid))
            if recipient:
                reminder.recipients.append(recipient)
        db.session.add(reminder)
        db.session.commit()
        flash('Reminder added successfully!')
        return redirect(url_for('index'))
    recipients = Recipient.query.all()
    return render_template('add_reminder.html', recipients=recipients)

@app.route('/edit_reminder/<int:id>', methods=['GET', 'POST'])
def edit_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if request.method == 'POST':
        reminder.task_detail = request.form['task_detail']
        reminder.reminder_type = request.form['reminder_type']
        reminder.purpose = request.form['purpose']
        next_date_str = request.form['next_reminder_date']
        reminder.next_reminder_date = datetime.strptime(next_date_str, '%Y-%m-%d').date()
        reminder.recurring = True if request.form.get('recurring') == 'on' else False
        reminder.interval_days = int(request.form['interval_days']) if reminder.recurring else 0
        # Update recipients: clear existing list and add new selections
        reminder.recipients.clear()
        recipient_ids = request.form.getlist('recipients')
        for rid in recipient_ids:
            recipient = Recipient.query.get(int(rid))
            if recipient:
                reminder.recipients.append(recipient)
        db.session.commit()
        flash('Reminder updated successfully!')
        return redirect(url_for('index'))
    recipients = Recipient.query.all()
    return render_template('edit_reminder.html', reminder=reminder, recipients=recipients)

@app.route('/delete_reminder/<int:id>', methods=['POST'])
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    flash('Reminder deleted successfully!')
    return redirect(url_for('index'))

# -------------------------
# Reminder Scheduler & Email Sender
# -------------------------

def send_email_reminder(reminder):
    subject = f"Reminder: {reminder.task_detail}"
    body = (f"Task Detail: {reminder.task_detail}\n"
            f"Type: {reminder.reminder_type}\n"
            f"Purpose: {reminder.purpose}\n"
            f"Scheduled Date: {reminder.next_reminder_date}")
    for recipient in reminder.recipients:
        msg = Message(subject, recipients=[recipient.email])
        msg.body = body
        try:
            mail.send(msg)
            print(f"Email sent to {recipient.email} for reminder {reminder.id}")
        except Exception as e:
            print(f"Failed to send email to {recipient.email}: {str(e)}")

def check_and_send_reminders():
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        reminders = Reminder.query.filter_by(next_reminder_date=tomorrow).all()
        for reminder in reminders:
            send_email_reminder(reminder)
            if reminder.recurring:
                reminder.next_reminder_date = reminder.next_reminder_date + timedelta(days=reminder.interval_days)
                db.session.commit()

def run_scheduler():
    schedule.every(1).minutes.do(check_and_send_reminders)
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    app.run(host='0.0.0.0', debug=True)
