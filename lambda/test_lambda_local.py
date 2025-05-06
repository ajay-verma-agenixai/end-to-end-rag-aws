import json
from lambda_function import lambda_handler

def test_lambda():
    # Load test events
    with open('test_event.json', 'r') as f:
        test_cases = json.load(f)['testCases']
    
    # Run each test case
    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"Running test case: {test_case['name']}")
        print(f"{'='*80}")
        
        try:
            # Create a mock context
            class MockContext:
                def __init__(self):
                    self.function_name = "test_function"
                    self.memory_limit_in_mb = 128
                    self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
                    self.aws_request_id = "test-request-id"
            
            context = MockContext()
            
            # Call the lambda handler
            response = lambda_handler(test_case['event'], context)
            
            # Print the response
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            # Check if the response is valid
            if response['statusCode'] == 200:
                body = json.loads(response['body'])
                if 'packages' in body:
                    print(f"\nFound {len(body['packages'])} packages")
                    for i, package in enumerate(body['packages'], 1):
                        print(f"\nPackage {i}:")
                        print(f"Hospital: {package.get('hospital', 'N/A')}")
                        print(f"Price: ₹{package.get('price', 'N/A')}")
                        print(f"Description: {package.get('description', 'N/A')}")
                        print("Features:")
                        for feature in package.get('features', []):
                            print(f"- {feature}")
            else:
                print("\nError Response:")
                print(json.loads(response['body']))
                
        except Exception as e:
            print(f"\nError running test case: {str(e)}")
        
        print(f"\n{'-'*80}")

if __name__ == "__main__":
    # Set environment variables for local testing
    import os
    os.environ['KB_ID'] = 'YOUR_KB_ID'  # Replace with your actual KB ID
    os.environ['AWS_RGN'] = 'us-east-1'  # Replace with your actual region
    
    test_lambda() 