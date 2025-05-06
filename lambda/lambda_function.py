import json
import boto3
import os
from botocore.config import Config

# Initialize Bedrock client
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime', config=bedrock_config)
bedrock_agent_client = boto3.client("bedrock-agent-runtime", config=bedrock_config)

# Configuration
KB_ID = os.environ['KB_ID']  # Your Knowledge Base ID
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"  # or use Sonnet if preferred
REGION = os.environ['AWS_RGN']

def retrieve_and_generate(input_text, kb_id, session_id=None):
    model_arn = f'arn:aws:bedrock:{REGION}::foundation-model/{MODEL_ID}'
    
    try:
        if session_id:
            response = bedrock_agent_client.retrieve_and_generate(
                input={'text': input_text},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': model_arn
                    }
                },
                sessionId=session_id
            )
        else:
            response = bedrock_agent_client.retrieve_and_generate(
                input={'text': input_text},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': model_arn
                    }
                }
            )
        
        # Print the raw response for debugging
        print("Raw Bedrock Response:", json.dumps(response, indent=2))
        return response
    except Exception as e:
        print(f"Error in retrieve_and_generate: {str(e)}")
        raise

def parse_bedrock_response(response):
    """Parse the Bedrock response and structure it for the frontend"""
    try:
        # Print the response structure for debugging
        print("Response structure:", json.dumps(response, indent=2))
        
        generated_text = response['output']['text']
        print("Generated text:", generated_text)
        
        # Extract packages from the generated text
        packages = []
        
        # Split the response into sections
        sections = generated_text.split('\n\n')
        
        for section in sections:
            # Skip empty sections
            if not section.strip():
                continue
                
            # Initialize package dictionary
            package = {
                'hospital': 'Information Available',
                'description': '',
                'features': [],
                'price': 'Contact for pricing'
            }
            
            # Process each line in the section
            lines = section.split('\n')
            current_key = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to identify the type of information in the line
                lower_line = line.lower()
                
                # Check for hospital name
                if any(keyword in lower_line for keyword in ['hospital', 'medical center', 'clinic', 'healthcare']):
                    # Extract hospital name - take everything after the keyword
                    for keyword in ['hospital', 'medical center', 'clinic', 'healthcare']:
                        if keyword in lower_line:
                            parts = line.split(keyword, 1)
                            if len(parts) > 1:
                                package['hospital'] = parts[1].strip()
                            else:
                                package['hospital'] = line
                            break
                
                # Check for price
                elif '₹' in line or 'rs' in lower_line or 'inr' in lower_line:
                    # Extract price
                    price = line
                    if '₹' in line:
                        price = line.split('₹')[-1].strip()
                    elif 'rs' in lower_line:
                        price = line.split('rs')[-1].strip()
                    elif 'inr' in lower_line:
                        price = line.split('inr')[-1].strip()
                    
                    # Clean up price
                    price = price.replace(',', '').strip()
                    if price.replace('.', '').isdigit():
                        package['price'] = price
                
                # Check for description
                elif any(keyword in lower_line for keyword in ['package', 'checkup', 'health', 'renal', 'cardiac', 'diabetes']):
                    if not package['description']:
                        package['description'] = line
                
                # Check for features/includes
                elif any(keyword in lower_line for keyword in ['includes', 'features', 'tests', 'services']):
                    current_key = 'features'
                    # Extract features from the same line if they exist after the keyword
                    for keyword in ['includes', 'features', 'tests', 'services']:
                        if keyword in lower_line:
                            parts = line.split(keyword, 1)
                            if len(parts) > 1 and parts[1].strip():
                                features = [f.strip() for f in parts[1].split(',')]
                                package['features'].extend(features)
                
                # If we're in features mode, add the line as a feature
                elif current_key == 'features':
                    if line and not any(keyword in lower_line for keyword in ['hospital', 'price', 'package']):
                        package['features'].append(line)
            
            # Only add the package if we have some meaningful information
            if (package['hospital'] != 'Information Available' or 
                package['description'] or 
                package['features'] or 
                package['price'] != 'Contact for pricing'):
                packages.append(package)
        
        # If no packages were found, create a default package with the raw response
        if not packages:
            packages.append({
                'hospital': 'Information Available',
                'description': generated_text,
                'features': ['Please contact the hospital for detailed package information'],
                'price': 'Contact for pricing'
            })
        
        return {
            'packages': packages,
            'raw_response': generated_text  # Include raw response for debugging
        }
    except Exception as e:
        print(f"Error in parse_bedrock_response: {str(e)}")
        return {
            'error': f'Error parsing response: {str(e)}',
            'raw_response': str(response)  # Include raw response for debugging
        }

def lambda_handler(event, context):
    try:
        # Get the query from the request
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        # Handle different request formats
        if 'body' in body:
            # Format: {"body": {"query": "..."}}
            query = body['body'].get('query')
        else:
            # Format: {"query": "..."}
            query = body.get('query')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'error': 'Query is required. Please provide a query in the request body.'
                })
            }
        
        # Call Bedrock
        response = retrieve_and_generate(query, KB_ID)
        
        # Parse and structure the response
        result = parse_bedrock_response(response)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'error': f'An error occurred: {str(e)}'
            })
        } 