# Flask Reminder Application

A simple web application built with Flask to manage reminders and send email notifications to specified recipients.

## Features

*   **Recipient Management:**
    *   Add new recipients with name, designation, location, email, and phone number.
    *   View a list of all recipients.
    *   Edit existing recipient details.
    *   Delete recipients.
*   **Reminder Management:**
    *   Add new reminders with task details, type, purpose, and next reminder date.
    *   Assign one or more recipients to each reminder.
    *   Set reminders as recurring with a specified interval in days.
    *   View a list of all reminders.
    *   Edit existing reminder details.
    *   Delete reminders.
*   **Email Notifications:**
    *   Automatically sends email reminders to assigned recipients one day before the scheduled `next_reminder_date`.
*   **Background Scheduler:**
    *   Uses a background thread and the `schedule` library to periodically check for upcoming reminders.

## Technologies Used

*   **Backend:** Python, Flask
*   **Database:** SQLite (via Flask-SQLAlchemy)
*   **Email:** Flask-Mail (configured for Gmail SMTP)
*   **Scheduling:** `schedule` library
*   **Frontend:** HTML (using Flask's Jinja2 templating)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    Flask
    Flask-SQLAlchemy
    Flask-Mail
    schedule
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the Application (`app.py`):**
    *   **Secret Key:** Change `'your_secret_key_here'` to a strong, unique secret key.
        ```python
        app.config['SECRET_KEY'] = 'a_very_strong_and_unique_secret_key'
        ```
    *   **Database URI:** The default is `sqlite:///reminder.db`. You can change the path or use a different database supported by SQLAlchemy if needed.
    *   **Flask-Mail Settings:**
        *   Replace `'gg@gmail.com'` with *your* Gmail address in `MAIL_USERNAME` and `MAIL_DEFAULT_SENDER`.
        *   Replace `''` with *your* Gmail App Password. **Important:** Do not use your regular Gmail password. You need to generate an "App Password" for this application in your Google Account settings (under Security -> 2-Step Verification -> App passwords).
       
5.  **Run the Application:**
    ```bash
    python app.py
    ```
    The application will start, create the `reminder.db` SQLite database file if it doesn't exist, and launch the background scheduler.

## Usage

1.  Open your web browser and navigate to `http://127.0.0.1:5000` (or `http://<your-server-ip>:5000` if running on a different host).
2.  **Manage Recipients:** Go to the `/recipients` page to add, view, edit, or delete recipients.
3.  **Manage Reminders:**
    *   Go to the home page (`/`) to view existing reminders.
    *   Click "Add Reminder" to create a new reminder, select recipients, and set recurrence if needed.
    *   Use the "Edit" and "Delete" buttons next to each reminder on the home page to manage them.
4.  **Email Notifications:** The application automatically checks every minute (as configured in `run_scheduler`) for reminders whose `next_reminder_date` is *tomorrow*. If found, it sends an email notification to the associated recipients. For recurring reminders, the `next_reminder_date` is updated after the email is sent.

## Database

The application uses SQLite by default. The database file (`reminder.db`) will be created in the same directory as `app.py` when the application first runs. The database schema is defined using Flask-SQLAlchemy models (`Recipient`, `Reminder`, and the `reminder_recipients` association table).

## Scheduler

A background thread runs the `run_scheduler` function, which uses the `schedule` library. It executes the `check_and_send_reminders` function every minute. This function queries the database for reminders due the next day and triggers the email sending process.
