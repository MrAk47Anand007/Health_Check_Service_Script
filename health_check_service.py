import os
import gspread
import json
import traceback
import requests
from typing import Any, Dict

# Environment variables for configuration
webhook_url = os.getenv('WEBHOOK_URL')
service_json = os.getenv('SERVICE_JSON')
service_api_url = os.getenv('SERVICE_API_URL')
auth_api_url = os.getenv('AUTH_API_URL')
keys_json = os.getenv('KEYS_JSON')

# Paths to store service account and keys JSON files
service_json_path = os.path.expanduser('~/repo/service_account.json')
with open(service_json_path, 'w') as f:
    f.write(service_json)  # Save service account JSON to a file

keys_json_path = os.path.expanduser('~/repo/keys.json')
with open(keys_json_path, 'w') as f:
    f.write(keys_json)  # Save keys JSON to a file

def apiCaller(url: str, reqType: str, jsonPayload: Dict[str, Any], token: str) -> requests.Response:
    """
    Makes an API call with the given parameters.

    Args:
        url (str): The API endpoint URL.
        reqType (str): The type of HTTP request (e.g., 'GET', 'POST', etc.).
        jsonPayload (Dict[str, Any]): The JSON payload to be sent with the request.
        token (str): The Bearer token for authorization.

    Returns:
        requests.Response: The response from the API call.
    """
    headers = {'Authorization': f'Bearer {token}'}  # Authorization header
    try:
        # Make the API call
        response = requests.request(reqType, url, headers=headers, json=jsonPayload)
        response.raise_for_status()  # Raise an error for HTTP 4xx/5xx status codes
        return response
    except requests.exceptions.RequestException as e:
        # Log the exception and re-raise
        print(f"An error occurred: {e}")
        raise

def googleSheetConnectNew(EXCEL_KEY: str):
    """
    Connects to a Google Sheet using the service account JSON file.

    Args:
        EXCEL_KEY (str): The key of the Google Spreadsheet.

    Returns:
        gspread.Spreadsheet: The connected spreadsheet object.
    """
    try:
        # Authenticate using the service account
        gc = gspread.service_account(service_json_path)
        spreadsheet = gc.open_by_key(EXCEL_KEY)  # Open spreadsheet by key
        return spreadsheet
    except Exception as e:
        # Log any exceptions and traceback
        print(f"Exception :: GoogleSheet_Connect Function - Failed to connect to Google Sheets: {str(e)}")
        traceback_message = traceback.format_exc()
        print("Traceback:\n", traceback_message)
        return None, None

def checkStausOfService(token):
    """
    Checks the status of a service by making an API call.

    Args:
        token (str): Authorization token.

    Returns:
        str: The service status if successful, None otherwise.
    """
    try:
        response = apiCaller(service_api_url, "GET", jsonPayload=None, token=token)
        return str(response.json()['status']['status'])  # Extract the service status
    except Exception as e:
        # Log any exceptions and traceback
        traceback_message = traceback.format_exc()
        print("Traceback:\n", traceback_message)
        return None, None

def authenticate(username, password):
    """
    Authenticates a user and retrieves a token.

    Args:
        username (str): Username for authentication.
        password (str): Password for authentication.

    Returns:
        str: The access token if authentication is successful, None otherwise.
    """
    try:
        JSON_PAYLOAD = {"username": username, "password": password}
        response = apiCaller(auth_api_url, "POST", JSON_PAYLOAD, None)
        return response.json()['token']  # Return the access token
    except Exception as e:
        # Log any exceptions and traceback
        traceback_message = traceback.format_exc()
        print("Traceback:\n", traceback_message)
        return None, None

def get_excel_key(key_name):
    """
    Retrieves an Excel key from the keys JSON file.

    Args:
        key_name (str): The name of the key to retrieve.

    Returns:
        str: The value of the key if found, None otherwise.
    """
    keys_file_path = keys_json_path
    try:
        # Read keys JSON file
        with open(keys_file_path, 'r') as file:
            config = json.load(file)
        return config.get(key_name, "")  # Return the key value
    except Exception as e:
        # Log exceptions
        print(f"Excel key invalid {str(e)}")

def post_to_webhook(text, color):
    """
    Sends a POST request to a Slack webhook URL with an adaptive card message.

    Args:
        text (str): The message text.
        color (str): The color of the message text.
    """
    if not webhook_url:
        print("Webhook URL is not configured.")
        return

    # Adaptive card message body
    body = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "BMS Service is " + text,
                        "wrap": True,
                        "spacing": "Medium",
                        "horizontalAlignment": "Center",
                        "height": "stretch",
                        "style": "heading",
                        "fontType": "Monospace",
                        "size": "ExtraLarge",
                        "weight": "Bolder",
                        "color": color,
                        "isSubtle": True
                    }
                ]
            }
        ]
    }

    try:
        # Send the POST request
        response = requests.post(webhook_url, json=body)
        if response.status_code == 202:
            print(f"Webhook message sent: {text}")
        else:
            print(f"Failed to send webhook message. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        # Log exceptions
        print(f"Error sending webhook message: {e}")

def process_all_req():
    """
    Orchestrates the entire process:
    - Connects to Google Sheets
    - Retrieves user credentials
    - Authenticates the user
    - Checks service status
    - Posts the status to the webhook

    Returns:
        str: "Success" if all steps succeed, None otherwise.
    """
    try:
        # Get the Excel key for the Windows Server
        windows_server_excel_key = get_excel_key("WINDOWS_SERVER_PASS")
        spreadsheet = googleSheetConnectNew(windows_server_excel_key)

        if not spreadsheet:
            raise RuntimeError("Failed to connect to Google Sheets. Check service account permissions and spreadsheet key.")

        # Access the first worksheet
        worksheet = spreadsheet.get_worksheet(0)
        if not worksheet:
            raise RuntimeError("Failed to access the first worksheet in the spreadsheet.")

        # Retrieve data from the worksheet
        data = worksheet.get_all_records()

        # Extract the last user's credentials
        correct_username = data[len(data) - 1]["Username"]
        correct_password = data[len(data) - 1]["Password"]

        # Authenticate and get the access token
        access_token = authenticate(correct_username, correct_password)

        # Check the service status
        service_message = checkStausOfService(token=access_token)

        # Post the service status to the webhook
        if service_message == "Running":
            post_to_webhook(service_message, "Good")
        else:
            post_to_webhook(service_message, "Warning")

        return "Success"
    except Exception as e:
        # Log any exceptions and traceback
        traceback_message = traceback.format_exc()
        print("Traceback:\n", traceback_message)
        return None, None

# Execute the process
process_all_req()
