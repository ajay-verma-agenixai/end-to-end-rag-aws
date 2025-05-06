from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
# The API Gateway URL should be in the format: https://[api-id].execute-api.[region].amazonaws.com/[stage]
API_GATEWAY_BASE_URL = 'https://riau15k291.execute-api.us-east-1.amazonaws.com/default/genai-app-april'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        # Log the raw request data
        raw_data = request.get_data()
        logger.info(f"Raw request data: {raw_data}")
        
        # Parse the request data
        try:
            data = request.json
            logger.info(f"Parsed request JSON: {data}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            return jsonify({'error': 'Invalid JSON format'}), 400
        
        # Extract query from the request data
        query = None
        if isinstance(data, dict):
            if 'query' in data:
                query = data['query']
            elif 'body' in data and isinstance(data['body'], dict) and 'query' in data['body']:
                query = data['body']['query']
        
        logger.info(f"Extracted query: {query}")
        
        if not query:
            logger.error("No query found in request data")
            return jsonify({'error': 'Query is required'}), 400
        
        # Construct the full API URL
        api_url = API_GATEWAY_BASE_URL
        logger.info(f"Making request to API URL: {api_url}")
        
        # Format the request body for the Lambda function
        request_body = {
            "query": query  # Send the query directly without nesting
        }
        
        logger.info(f"Sending request body to API Gateway: {request_body}")
        
        response = requests.post(
            api_url,
            json=request_body,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        logger.info(f"API Gateway Response Status: {response.status_code}")
        logger.info(f"API Gateway Response: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return jsonify(response_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                return jsonify({'error': 'Invalid response format from API'}), 500
        elif response.status_code == 404:
            logger.error(f"API endpoint not found: {api_url}")
            return jsonify({
                'error': f'API endpoint not found. Please check the API Gateway configuration. URL: {api_url}'
            }), 404
        else:
            error_message = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_message = error_data['error']
            except:
                pass
            logger.error(f"API Error: {error_message}")
            return jsonify({'error': error_message}), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to API")
        return jsonify({'error': 'Failed to connect to API. Please check your connection.'}), 503
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    # Print the API Gateway URL at startup for verification
    logger.info(f"API Gateway Base URL: {API_GATEWAY_BASE_URL}")
    app.run(debug=True) 