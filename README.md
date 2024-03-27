CertChecker

![image](https://github.com/AASoftware/CertChecker/assets/163601966/4e1e42f2-0673-457c-8fec-2e87cf148039)


CertChecker is a web application for monitoring SSL certificates on various servers. The application allows users to add servers to monitor their SSL certificates and displays the status of these certificates in a clear list.

Features
- Add Servers: Users can add new servers by entering their name, URL, port, and email address.
- SSL Certificate Monitoring: The application automatically checks the validity of SSL certificates on the added servers and displays the status (critical, info, ok) as well as the expiration date.
- Remove Servers: Users can remove servers from the list if they are no longer needed to be monitored.
- Notifications: The application sends notifications via email when a certificate has expired or has a critical status.
- Scheduled Refresh: The application automatically refreshes the server list and checks the certificate status at 2:00 AM every day using a Flask scheduler job.

Installation
1. Clone the repository to your local computer:
   git clone https://github.com/your-username/CertChecker.git
2. Navigate to the project directory:
   cd CertChecker
3. Install the required dependencies:
   pip install -r requirements.txt
4. Configure the YAML file:
   - Open config.yaml and update the email settings with your SMTP server details.
   - Customize other settings as needed.
5. Start the application:
   python app.py
6. Open a web browser and go to http://localhost:5000 to use the application.

Technologies
- Flask: Web framework for Python.
- Bootstrap: Frontend framework for design and user interface.
- SQLite: Database for storing server information.
- PyYAML: Library for reading and writing YAML files.

Configuration (config.yaml)
The config.yaml file contains settings for the application, including:
- Mail Configuration: SMTP server details for sending email notifications.
- Scheduler Configuration: Settings for the Flask scheduler job, including the time of the daily refresh.

Mail Functionality
CertChecker utilizes the configured SMTP server to send email notifications when SSL certificates expire or have a critical status. Users can provide their email address when adding a server to receive these notifications.

Flask Scheduler Job
The application uses the Flask scheduler to schedule a job that automatically refreshes the server list and checks the certificate status at 2:00 AM every day. This ensures that the certificate status is always up-to-date without manual intervention.

Author
CertChecker was developed by AASoftware.

License
This project is licensed under the MIT License.
