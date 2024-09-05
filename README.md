# Water Reservoir Visualization Project Configuration Guide

## Introduction

Welcome to the Water Reservoir Visualization project! This web application visualizes data about water reservoirs in Mexico, providing insights into water levels, storage capacity, and other key metrics.

## Local Setup

Follow these steps to set up the project on your local machine for development:

### 1. Create a Virtual Environment

Open your terminal and run:

```bash
python3 -m venv myenv
source myenv/bin/activate
```

You'll notice your terminal prompt change, indicating that the virtual environment is active. Any Python packages we install now will be confined to this project.

### 2. Install Dependencies

Now, let's install the packages our project needs. We keep a list of these in a file called `requirements.in`:

```
Flask
pandas
```

Then, install these packages by running:

```bash
pip install -r requirements.in
```

This command tells pip (Python's package installer) to read our requirements file and install the specified packages.

### 3. Preprocessing the Data

Before we start our application, we need to prepare our data. Our `preprocessor.py` script takes the raw JSON files and converts them into two SQLite databases:

1. `reservoir_static.db`: Contains static data about reservoirs.
2. `reservoir_dynamic.db`: Contains dynamic data that changes over time, plus the `clavesih` identifier.

Ensure all your raw JSON data files are in the `dam_data` directory, then run:

```bash
python preprocessing.py dam_data
```

The script processes all JSON files in the specified directory and will create two SQLite database files in your project root directory:

- `reservoir_static.db`: Contains static data about reservoirs (location, name, state, etc.)
- `reservoir_dynamic.db`: Contains dynamic data that changes over time (water levels, storage amounts, etc.)

If you add new JSON files later, you can run this script again to update the databases.

### 4. Starting the Application

Now we're ready to run our application:

```bash
python app.py
```

You should see some output indicating that the server is running. Open your web browser and go to `http://127.0.0.1:5000`. You should see the Water Reservoir Visualization application.

## Production Setup (Ubuntu Server)

When we're ready to make our application available to the world, we'll deploy it to an Ubuntu server. This process is a bit more involved, but we'll go through it step by step.

### 1. Setting Up Python

First, let's make sure our server has the latest version of Python and pip (Python's package installer). SSH into your Ubuntu server and run:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. Creating a Project Environment

Just like on our local machine, we'll create a virtual environment on the server:

```bash
sudo pip3 install virtualenv
mkdir water_reservoir_viz
cd water_reservoir_viz
virtualenv venv
source venv/bin/activate
```

Now we're in our project directory with our virtual environment active.

### 3. Preparing the Application and Data

Transfer your project files to the server (you can use SCP, SFTP, or any method you're comfortable with). Once the files are on the server, install the requirements:

```bash
pip install -r requirements.in
```

Now, run the preprocessor to prepare your databases:

```bash
python preprocessor.py dam_data
```

This will create the `reservoir_static.db` and `reservoir_dynamic.db` files on your server.

### 4. Serving the Application

For production, we'll use Gunicorn to serve our application. While Flask's built-in server is great for development, it's not suitable for production environments. Here's why:

- Flask's server is single-threaded, handling only one request at a time. This can lead to slow response times under moderate traffic (as low as 10-30 requests per minute).
- It lacks features needed for production, such as load balancing and process management.

Gunicorn, on the other hand, is a production-ready WSGI server that:
- Supports multiple worker processes, handling concurrent requests efficiently.
- Provides better resource management and fault tolerance.
- Can significantly improve your application's ability to handle traffic, potentially managing hundreds of requests per minute, depending on your server's capacity and application complexity.

There are alternatives to Gunicorn, such as uWSGI, mod_wsgi (for Apache), and Waitress, but Gunicorn is widely used and easy to set up.

To install and run Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Note: Make sure you're running this command from the directory containing your `app.py` file, and that your virtual environment is activated.

This command tells Gunicorn to use 4 worker processes and accept connections from any IP address on port 5000.

At this point, if your server's firewall allows it, you should be able to access your application by visiting your server's IP address in a web browser.

### 5. Adding Nginx as a Reverse Proxy

While Gunicorn can serve our application, adding Nginx as a reverse proxy provides additional benefits:
- Efficient handling of static files
- Easier SSL/TLS configuration
- Ability to serve multiple applications on the same server
- Additional layer of security and load balancing

1. Install Nginx:

```bash
sudo apt install nginx
```

2. Remove the default Nginx configuration:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

3. Create a new Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/water_reservoir_viz
```

4. Add the following configuration:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;  # Your server's IP address
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

The `/etc/nginx/sites-available` directory contains configuration files for all potential Nginx virtual hosts. To actually enable a configuration, we need to link it to the `/etc/nginx/sites-enabled` directory, which Nginx reads from when it starts.

5. Create this symbolic link to enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/water_reservoir_viz /etc/nginx/sites-enabled
```

This approach allows for easy enabling or disabling of sites without duplicating configuration files.

6. Check that our configuration doesn't have any errors:

```bash
sudo nginx -t
```

7. If everything looks good, restart Nginx to apply the changes:

```bash
sudo systemctl restart nginx
```

### 6. Opening the Firewall

Finally, we need to configure the firewall to allow web traffic to reach our Nginx server. Ubuntu comes with a firewall configuration tool called UFW (Uncomplicated Firewall). We'll use it to open the necessary ports.

Run the following command:

```bash
sudo ufw allow 'Nginx Full'
```

This command does the following:
- It uses the predefined 'Nginx Full' profile in UFW.
- This profile allows incoming traffic on both port 80 (HTTP) and port 443 (HTTPS).
- It ensures that web users can access your site via both unsecured (HTTP) and secured (HTTPS) connections.

To verify that the firewall rule has been added correctly, you can check the status of UFW:

```bash
sudo ufw status
```

You should see output that includes these lines:

```
Nginx Full                  ALLOW       Anywhere
Nginx Full (v6)             ALLOW       Anywhere (v6)
```

If you don't see these lines, or if you see that UFW is inactive, you may need to enable it:

```bash
sudo ufw enable
```

Remember, if UFW was not active before, enabling it might block other connections, so be sure you've set up rules for any other necessary services (like SSH) before enabling the firewall.

If we skip this step, our Nginx server would be running, but it wouldn't be accessible from the internet. The firewall would block all incoming web traffic, essentially hiding our application from the world. This step is crucial for making our application publicly accessible while maintaining basic server security.

### 7. Verifying the Setup

After completing these steps, you should be able to access your application by entering your server's IP address (208.109.234.143) in a web browser or using curl:

```bash
curl http://208.109.234.143
```

This should now return the content of your Flask application instead of the Nginx welcome page.

### Note on HTTPS

Currently, HTTPS is not set up, which is why you're getting an error when trying to access the site via HTTPS. Setting up HTTPS involves obtaining and configuring SSL/TLS certificates. This is an important step for production environments, but it's beyond the scope of this basic setup.

If you want to set up HTTPS in the future, you'll need to:
1. Obtain an SSL/TLS certificate (e.g., using Let's Encrypt)
2. Configure Nginx to use the certificate
3. Update the Nginx configuration to listen on port 443 and redirect HTTP to HTTPS

For now, your application will be accessible via HTTP on your IP address.

## Database Schema

For those interested in the structure of our databases:

### reservoir_static.db
- Table: `reservoirs`
  - `clavesih` (TEXT): Primary Key, unique identifier for each reservoir
  - `nombreoficial` (TEXT): Official name of the reservoir
  - `nombrecomun` (TEXT): Common name of the reservoir
  - `estado` (TEXT): State where the reservoir is located
  - `nommunicipio` (TEXT): Municipality name
  - `regioncna` (TEXT): CNA region
  - `latitud` (REAL): Latitude coordinate
  - `longitud` (REAL): Longitude coordinate
  - `uso` (TEXT): Usage of the reservoir
  - `corriente` (TEXT): Water current
  - `tipovertedor` (TEXT): Type of spillway
  - `inicioop` (TEXT): Year of initial operation
  - `elevcorona` (TEXT): Crown elevation
  - `bordolibre` (REAL): Free board
  - `nameelev` (REAL): Normal maximum water elevation
  - `namealmac` (REAL): Normal maximum storage
  - `namoelev` (REAL): Normal operating maximum elevation
  - `namoalmac` (REAL): Normal operating maximum storage
  - `alturacortina` (TEXT): Dam height

### reservoir_dynamic.db
- Table: `reservoir_data`
  - `idmonitoreodiario` (INTEGER): Primary Key, unique identifier for each data point
  - `clavesih` (TEXT): Foreign Key, references `reservoirs` table in `reservoir_static.db`
  - `fechamonitoreo` (DATE): Date of the recorded data
  - `elevacionactual` (REAL): Current water elevation
  - `almacenaactual` (REAL): Current water storage amount

Note: The `llenano` field is not stored in either database, as it can be derived from other fields if needed.

## Crontab Documentation for Conagua Project

### Overview

This document provides comprehensive information about the crontab setup for the Conagua project, including its structure, how to manage jobs, and how to monitor their execution.

### Current Crontab Structure

The crontab for this project is defined in the `app_crontab` file in the root of the repository. Its current structure is as follows:

```crontab
CONAGUA_LOG_FILE=/repositories/conagua/conagua_unified.log

# Run the data fetch and processing pipeline daily at 2 AM
0 2 * * * /repositories/conagua/run_pipeline.sh >> /repositories/conagua/cron_execution.log 2>&1
```

### Reasoning Behind Decisions

1. **Single crontab file**: We use a single `app_crontab` file to keep all project-related cron jobs in one place, making it easier to version control and manage.

2. **Environment variables**: We set environment variables (like `CONAGUA_LOG_FILE`) directly in the crontab to ensure they're available to the scripts when they run.

3. **Logging**: We redirect both standard output and standard error to a log file (`cron_execution.log`) to capture any issues that might occur during execution.

4. **Execution time**: The job is set to run at 2 AM daily, assuming this is a low-traffic time and new data is available daily.

### How to Add New Jobs

To add a new job to the crontab:

1. Open the `app_crontab` file in a text editor.
2. Add a new line with the following format:
   ```
   * * * * * /path/to/your/script.sh >> /path/to/logfile.log 2>&1
   ```
   Replace the asterisks with the appropriate time specification, and adjust the script path and log file as needed.
3. Save the file and commit it to the repository.
4. After pushing to the server, reinstall the crontab (see "Applying Changes" section below).

### Manual Modifications

While it's best to manage the crontab through the versioned `app_crontab` file, you can make manual modifications if necessary:

1. SSH into the server.
2. Edit the crontab directly:
   ```
   crontab -e
   ```
3. Make your changes and save.

Note: Manual changes will be overwritten the next time the crontab is installed from the `app_crontab` file.

### Applying Changes

After modifying the `app_crontab` file and pushing changes to the server:

1. SSH into the server.
2. Navigate to the project directory:
   ```
   cd /repositories/conagua
   ```
3. Install the updated crontab:
   ```
   crontab app_crontab
   ```

### Checking If a Job Is Being Executed

To check if a job is currently running:

1. SSH into the server.
2. Use the `ps` command to look for the running script:
   ```
   ps aux | grep run_pipeline.sh
   ```

### Checking Previous Runs

To check the results of previous runs:

1. Examine the main log file:
   ```
   tail -n 100 /repositories/conagua/conagua_unified.log
   ```

2. Check the cron execution log:
   ```
   tail -n 100 /repositories/conagua/cron_execution.log
   ```

3. For more detailed logs, you may need to check specific log files created by individual scripts.

### Troubleshooting

If jobs are not running as expected:

1. Check if the cron daemon is running:
   ```
   sudo systemctl status cron
   ```

2. Verify that the crontab is installed correctly:
   ```
   crontab -l
   ```

3. Check the system logs for cron-related messages:
   ```
   sudo grep CRON /var/log/syslog
   ```

4. Ensure that all paths in the crontab are absolute paths.

5. Verify that the user running the crontab has the necessary permissions to execute the scripts and write to the log files.

### Best Practices

1. Always use absolute paths in crontab entries.
2. Redirect output to log files for easier debugging.
3. Use comments in the crontab file to describe what each job does.
4. Test new cron jobs by setting them to run more frequently and monitoring the output.
5. Keep the `app_crontab` file in version control and use it as the single source of truth for cron jobs.

Remember to update this documentation whenever significant changes are made to the crontab setup or related processes.

## Logging Documentation

### Overview

This document describes the logging setup for the Conagua data pipeline, including how to check logs and customize logging behavior for different scenarios.

### Logging Setup

The logging system is centralized in a `logger_config.py` file, which is used by all Python scripts in the project. The bash script that orchestrates the pipeline also logs to the same file.

#### File Structure

- `logger_config.py`: Central logging configuration
- `fetch_dam_data.py`: Uses the centralized logging
- `preprocessing.py`: Uses the centralized logging
- `run_pipeline.sh`: Bash script that also logs to the same file

### How to Check Logs

The unified log file is located at `/repositories/conagua/conagua_unified.log`.

To view the entire log file:
```bash
cat /repositories/conagua/conagua_unified.log
```

To view the last 50 lines of the log:
```bash
tail -n 50 /repositories/conagua/conagua_unified.log
```

To follow the log in real-time (useful for debugging):
```bash
tail -f /repositories/conagua/conagua_unified.log
```

### Customization Options

#### In logger_config.py

1. **Log Level**: 
   - Current: `logging.INFO`
   - Options: `logging.DEBUG`, `logging.WARNING`, `logging.ERROR`, `logging.CRITICAL`
   - Usage: Change `logger.setLevel(logging.INFO)` to desired level

2. **Log Format**:
   - Current: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
   - Customizable fields: `%(filename)s`, `%(funcName)s`, `%(lineno)d`, etc.

3. **Log File Location**:
   - Current: `/repositories/conagua/conagua_unified.log`
   - Modify `LOG_FILE` variable to change location

4. **Adding Handlers**:
   - Current: File and Console handlers
   - Options: Add handlers for email notifications, database logging, etc.

#### In Python Scripts (fetch_dam_data.py, preprocessing.py)

1. **Logger Name**:
   - Current: `logger = setup_logging(__name__)`
   - Options: Use a custom name, e.g., `logger = setup_logging("FetchData")`

2. **Log Messages**:
   - Use appropriate log levels: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`, `logger.critical()`

#### In Bash Script (run_pipeline.sh)

1. **Log Message Prefix**:
   - Current: `"[$(date +'%Y-%m-%d %H:%M:%S')] BASH - $1"`
   - Customizable to add more information if needed

2. **Log Rotation**:
   - Current: Rotates at 10MB
   - Modify the condition `[ $(du -m "$LOG_FILE" | cut -f1) -gt 10 ]` to change the size threshold

### Scenarios and Recommendations

#### Debugging

1. Set log level to `DEBUG` in `logger_config.py`:
   ```python
   logger.setLevel(logging.DEBUG)
   ```
2. Add more detailed log messages in your scripts using `logger.debug()`

#### Production / Avoiding Excessive Logs

1. Set log level to `WARNING` or `ERROR` in `logger_config.py`:
   ```python
   logger.setLevel(logging.WARNING)
   ```
2. Increase the log rotation size in `run_pipeline.sh`:
   ```bash
   if [ -f "$LOG_FILE" ] && [ $(du -m "$LOG_FILE" | cut -f1) -gt 100 ]; then
   ```

#### Performance Monitoring

1. Add timestamps to critical operations:
   ```python
   import time
   start_time = time.time()
   # ... operation ...
   logger.info(f"Operation completed in {time.time() - start_time} seconds")
   ```

#### Error Alerting

1. Add an email handler in `logger_config.py` for critical errors:
   ```python
   import logging.handlers
   smtp_handler = logging.handlers.SMTPHandler(
       mailhost=("smtp.example.com", 587),
       fromaddr="alert@example.com",
       toaddrs=["admin@example.com"],
       subject="Conagua Pipeline Critical Error",
       credentials=("username", "password"),
       secure=()
   )
   smtp_handler.setLevel(logging.CRITICAL)
   logger.addHandler(smtp_handler)
   ```

Remember to adjust these settings based on your specific needs and infrastructure setup.

