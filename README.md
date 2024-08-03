# Water Reservoir Visualization Project Configuration Guide

## Introduction

Welcome to the Water Reservoir Visualization project! This guide will walk you through setting up the project for both local development and deployment on an Ubuntu server. We've designed this guide to be friendly for newcomers, so don't worry if you're not familiar with all the terms – we'll explain everything as we go along.

## Project Structure

Our project is organized like this:

```
water_reservoir_viz/
│
├── dam_data/
│   └── (your raw JSON files here)
│
├── static/
│   ├── index.html
│   └── app.js
│
├── preprocessor.py
├── app.py
├── reservoir_static.db
├── reservoir_dynamic.db
└── requirements.in
```

This structure keeps our raw data, processed data (in SQLite databases), backend code, and frontend assets neatly separated.

## Local Setup

Let's start by setting up the project on your local machine for development.

### 1. Creating a Virtual Environment

First, we'll create a virtual environment. Think of this as a private workspace for our project, keeping its tools and libraries separate from other Python projects you might have.

Open your terminal and run:

```bash
python3 -m venv venv
source venv/bin/activate
```

You'll notice your terminal prompt change, indicating that the virtual environment is active. Any Python packages we install now will be confined to this project.

### 2. Installing Dependencies

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
python preprocessor.py dam_data
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
pip install -r requirements.txt
```

Now, run the preprocessor to prepare your databases:

```bash
python preprocessor.py dam_data
```

This will create the `reservoir_static.db` and `reservoir_dynamic.db` files on your server.

### 4. Serving the Application

Now, we come to an important difference between development and production. While Flask's built-in server is great for development, it's not designed to handle multiple users or high traffic. For production, we'll use a tool called Gunicorn.

Install Gunicorn:

```bash
pip install gunicorn
```

Gunicorn is a program that can run our Flask application and handle multiple user requests efficiently. To start our application with Gunicorn, run:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Let's break down this command:
- `-w 4` tells Gunicorn to use 4 "worker" processes. Think of these as copies of our application that can handle requests simultaneously.
- `-b 0.0.0.0:5000` tells Gunicorn to accept connections from any IP address on port 5000.
- `app:app` points Gunicorn to our Flask application.

If we were to skip using Gunicorn and just use Flask's built-in server, our application would still run, but it wouldn't be able to handle multiple requests efficiently. This could lead to slow response times or even crashes when multiple users try to access the site simultaneously. Gunicorn allows our application to serve many users at once, making it crucial for a production environment.

At this point, if your server's firewall allows it, you should be able to access your application by visiting your server's IP address in a web browser.

### 5. Adding Nginx to the Mix

While Gunicorn is running our application, we can add another program called Nginx to make things even better. Nginx will act as a "front door" for our application, handling tasks like serving static files and managing HTTPS connections.

Install Nginx:

```bash
sudo apt install nginx
```

Now we need to tell Nginx about our application. Create a new configuration file:

```bash
sudo nano /etc/nginx/sites-available/water_reservoir_viz
```

In this file, add the following configuration:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

This configuration tells Nginx to listen for incoming connections and forward them to our Gunicorn server.

To activate this configuration, create a link to it in the `sites-enabled` directory:

```bash
sudo ln -s /etc/nginx/sites-available/water_reservoir_viz /etc/nginx/sites-enabled
```

Check that our configuration doesn't have any errors:

```bash
sudo nginx -t
```

If everything looks good, restart Nginx to apply the changes:

```bash
sudo systemctl restart nginx
```

If we were to skip the Nginx setup, our application would still work through Gunicorn, but we'd miss out on several important benefits. Nginx is much more efficient at serving static files (like images or CSS) than Gunicorn, so without it, our application might be slower. Additionally, Nginx makes it easier to set up HTTPS for secure connections and can act as a buffer against certain types of cyber attacks. It also allows us to run multiple applications on the same server more easily.

### 6. Opening the Firewall

Finally, we need to make sure the server's firewall allows traffic to reach Nginx:

```bash
sudo ufw allow 'Nginx Full'
```

This command opens ports 80 (for HTTP) and 443 (for HTTPS) in the firewall.

If we skip this step, our application would be running, but it wouldn't be accessible from the internet. The firewall would block all incoming web traffic, essentially hiding our application from the world. This step is crucial for making our application publicly accessible.

Visit your server's IP address or domain name in a web browser to see it in action.


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

## Accessing the Databases

Here's a basic example of how to query the databases in your Flask application:

```python
import sqlite3

def get_reservoir_data(clavesih):
    # Connect to the static database
    static_conn = sqlite3.connect('reservoir_static.db')
    static_cursor = static_conn.cursor()

    # Get static data
    static_cursor.execute("SELECT * FROM reservoirs WHERE clavesih = ?", (clavesih,))
    static_data = static_cursor.fetchone()

    # Connect to the dynamic database
    dynamic_conn = sqlite3.connect('reservoir_dynamic.db')
    dynamic_cursor = dynamic_conn.cursor()

    # Get the latest dynamic data
    dynamic_cursor.execute("""
    SELECT * FROM reservoir_data 
    WHERE clavesih = ? 
    ORDER BY fechamonitoreo DESC 
    LIMIT 1
    """, (clavesih,))
    dynamic_data = dynamic_cursor.fetchone()

    # Close connections
    static_conn.close()
    dynamic_conn.close()

    return static_data, dynamic_data
```

Remember to close your database connections after use to prevent resource leaks.

--------------------------------
# Water Reservoir Visualization Project Configuration Guide

[... previous sections remain unchanged ...]

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

[... rest of the guide remains unchanged ...]