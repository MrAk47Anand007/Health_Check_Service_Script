# Health Check Service & CircleCI Configuration

## Overview

This repository contains a Python-based health check service that interacts with Google Sheets and an API to monitor service status. It includes a CircleCI configuration file that automates the process of running the health check script in a resource-efficient manner using Docker.

## Python Code Overview

### 1. **Health Check Service**
The Python script (`health_check_service.py`) performs the following tasks:
- Connects to Google Sheets via the service account JSON credentials.
- Authenticates against a specified API using a username and password.
- Calls an API endpoint to check the health status of a service.
- Sends notifications to a Slack webhook based on the service status (e.g., "Running" or "Warning").

### 2. **Requirements**
The Python script requires the following dependencies:
- `gspread`: For interacting with Google Sheets.
- `requests`: For making HTTP requests to APIs.
- `traceback`: For error handling and logging.
- `json`: For handling JSON data.

These dependencies are listed in `requirements.txt`.

### 3. **Environment Variables**
Ensure the following environment variables are set before running the Python script:
- `SERVICE_JSON`: The Google Service Account JSON used to authenticate with Google Sheets.
- `KEYS_JSON`: The JSON file containing necessary keys for the service.
- `WEBHOOK_URL`: The Slack webhook URL for sending service status updates.
- `SERVICE_API_URL`: The URL for the API endpoint that checks the service status.
- `AUTH_API_URL`: The URL for the authentication API.

### 4. **How to Run the Script Locally**
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo.git
   cd your-repo
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   . venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set the required environment variables:
   ```bash
   export SERVICE_JSON="your-service-json"
   export KEYS_JSON="your-keys-json"
   export WEBHOOK_URL="your-webhook-url"
   export SERVICE_API_URL="your-service-api-url"
   export AUTH_API_URL="your-auth-api-url"
   ```

4. Run the health check script:
   ```bash
   python health_check_service.py
   ```

---

## CircleCI Configuration

### 1. **CircleCI Configuration Overview**
This CircleCI configuration file automates the health check script execution in a Docker container. It uses a minimal `cimg/python:3.9` Docker image and caches dependencies to optimize for resource usage and speed.

### 2. **Key Features of CircleCI Config**
- **Docker Executor**: Uses the `cimg/python:3.9` Docker image to run the script in an isolated environment.
- **Resource Optimization**: The `resource_class` is set to `small` to minimize CPU and memory usage.
- **Dependency Caching**: Caches Python dependencies to speed up subsequent builds by reusing the virtual environment (`venv`).
- **File Management**: Environment variables (`SERVICE_JSON`, `KEYS_JSON`) are written as files during the build, so they can be used by the script.

### 3. **CircleCI Job Flow**
The CircleCI job consists of the following steps:
1. **Checkout**: Pulls the latest code from the repository.
2. **Dependency Installation**: Creates a virtual environment, installs dependencies from `requirements.txt`, and caches them.
3. **File Creation**: Creates the required JSON files (`service_account.json` and `keys.json`) using environment variables.
4. **Script Execution**: Runs the Python health check script.

### 4. **How to Use the CircleCI Configuration**
To use this CircleCI configuration:
1. **Create a CircleCI Project**: Link your GitHub repository to CircleCI.
2. **Add Environment Variables**: Set the following environment variables in CircleCI:
   - `SERVICE_JSON`
   - `KEYS_JSON`
   - `WEBHOOK_URL`
   - `SERVICE_API_URL`
   - `AUTH_API_URL`
3. **Push Changes**: Push your code to the repository, and CircleCI will automatically run the workflow defined in the `.circleci/config.yml`.

---

## Example CircleCI Config

```yaml
version: 2.1

# Use an optimized and lightweight CircleCI Python image
executors:
  python-executor:
    docker:
      - image: cimg/python:3.9  # Use next-gen minimal Python 3.9 image
    resource_class: small  # Use the smallest available resource class
    working_directory: ~/repo

# Jobs Section
jobs:
  run-health-check-script:
    executor: python-executor
    steps:
      # Check out the code from your repository
      - checkout

      # Restore cached virtual environment (if available)
      - restore_cache:
          keys:
            - v1-venv-{{ checksum "requirements.txt" }}

      # Install dependencies inside a virtual environment
      - run:
          name: Install Dependencies
          command: |
            python -m venv venv  # Create virtual environment
            . venv/bin/activate  # Activate it
            pip install -r requirements.txt  # Install dependencies

      # Save the virtual environment to the cache
      - save_cache:
          paths:
            - ./venv
          key: v1-venv-{{ checksum "requirements.txt" }}

      # Create Google Service Account JSON file from the environment variable
      - run:
          name: Create Google Service Account File
          command: |
            echo "$SERVICE_JSON" > service_account.json

      # Create Keys JSON file from the environment variable
      - run:
          name: Create Keys JSON File
          command: |
            echo "$KEYS_JSON" > keys.json

      # Run the Python script for health check
      - run:
          name: Run Python Script
          command: |
            . venv/bin/activate  # Activate the virtual environment
            python health_check_service.py  # Run the script

# Workflows Section
workflows:
  version: 2
  run-script-workflow:
    jobs:
      - run-health-check-script
```

---

## Additional Notes

- **Caching Dependencies**: The configuration optimizes build times by caching the Python virtual environment (`venv`), making it quicker to install dependencies on subsequent builds.
- **Environment Variables**: Make sure that the necessary environment variables are added both locally and in CircleCI to ensure smooth execution.
- **Optimized Resources**: The `small` resource class is used to minimize resource consumption and reduce costs. If needed, you can switch to a larger resource class for more intensive tasks.
