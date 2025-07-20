import requests
import json
import re

def get_general_response(message):
    """
    Sends a POST request to the specified endpoint with the provided message.

    Args:
    - message (str): The message to be sent in the request body.

    Returns:
    - response_data (dict): The JSON response from the server if the request is successful.
    """
    try:
        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'message': message
        }

        assistant_host = "http://{sensitive-ip}:8002"  # Replace with your actual assistant host
        response = requests.post(f"{assistant_host}/chat/general/", json=payload, headers=headers)

        response.raise_for_status()  # Raise an exception for HTTP errors

        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"Error fetching data: {err}")
        raise Exception(f"Failed to fetch data: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")
        raise Exception(f"An error occurred: {err}")


def parse_data(data: str, parse_prompt='extract all available data'):
    pattern_examples = """
    ip_with_prefix_pattern = r'(\d{1,3}\.){3}\d{1,3}/\d{1,2}'
    mac_pattern = r'[a-z0-9]{4}.[a-z0-9]{4}.[a-z0-9]{4}'
    interface_pattern = r'[A-Za-z]+\d+(/\d+){0,4}'
    int_or_subint_pattern = r'[a-zA-Z\-]+\d+(/\d+){0,4}(\.){0,1}(\d){0,10}'
    """

    pattern = get_general_response(f"""
    data: `{data}`
    
    Here is data in text format, that needs to be extracted into python object only with the relevant data.
    
    Your answer should only include the regex pattern line necessary to to fetch the data from the text
    using the findall function, you are creating only the pattern part, without anything else and in one line.
    The pattern should include specifications that make sure that only relevant data is extracted.
    
    The information that needs to be extracted, 
    and other instructions if they exist are specified here: `{parse_prompt}`.
    
    regex pattern examples: {pattern_examples} 
    
    """).split("'")[1].split("'")[0]

    return re.findall(pattern=pattern, string=data)

