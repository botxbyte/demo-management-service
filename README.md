# [ ]: Test case should have seperate folder? like for repository, endpoints 
# [ ]: Deployment part is missing - specifically k8s and Dockerfile
# [ ]: Shall we have any evironment like run.py for dev and prod version? via .env file



# Endpoint Test Suite

This directory contains comprehensive tests for all endpoints in the Demo Management Service.

## Files

- `endpoint_test_suite.py` - Main test suite with all endpoint tests
- `run_tests.py` - Simple runner script
- `README.md` - This documentation file
- `endpoint_test_report.csv` - Generated test results (created after running tests)

## Tested Endpoints

### Health Check
- `GET /api/v1/health/` - Service health check

### Demo CRUD Operations
- `POST /api/v1/demo/create/` - Create new demo
- `GET /api/v1/demo/read/{demo_id}/` - Get demo by ID
- `GET /api/v1/demos/` - List all demos (with pagination)
- `PATCH /api/v1/demo/update/{demo_id}/` - Update demo
- `DELETE /api/v1/demo/delete/{demo_id}/` - Delete demo

### Demo Status Management
- `PATCH /api/v1/demo/update/status/{demo_id}/` - Update demo status
- `PATCH /api/v1/demo/update/is-active/{demo_id}/` - Update active status

### Demo Members
- `GET /api/v1/demo/members/` - Get demo members
- `POST /api/v1/demo/assign-member/` - Assign member to demo

### Error Handling Tests
- Invalid endpoint test (404 error)
- Invalid HTTP method test (405 error)

## How to Run Tests

### Prerequisites
1. Make sure the Demo Management Service is running on `http://localhost:8801`
2. Install dependencies: `pip install -r requirements/base.txt`

### Running Tests

#### Option 1: Using the runner script
```bash
cd test_case
python run_tests.py
```

#### Option 2: Direct execution
```bash
cd test_case
python endpoint_test_suite.py
```

#### Option 3: Using pytest (if you want to run individual tests)
```bash
pytest test_case/endpoint_test_suite.py -v
```

## Test Results

After running the tests, a CSV report will be generated at `test_case/endpoint_test_report.csv` with the following columns:

- `test_name` - Name of the test
- `method` - HTTP method used
- `endpoint` - API endpoint tested
- `status_code` - Actual HTTP status code received
- `expected_status` - Expected HTTP status code
- `success` - Boolean indicating if test passed
- `duration_seconds` - Time taken for the request
- `response_size_bytes` - Size of response in bytes
- `timestamp` - When the test was run
- `error_message` - Error message if test failed
- `response_preview` - Preview of response data

## Test Configuration

The test suite uses the following default configuration:
- Base URL: `http://localhost:8801`
- Test User ID: `test-user-123`
- Test Demo ID: `test-demo-456`
- Timeout: 30 seconds per request

You can modify these values in the `EndpointTester` class constructor.

## Notes

- Tests run sequentially to maintain dependencies (e.g., create demo before testing read/update/delete)
- The test suite generates test UUIDs for demo operations
- Some tests may fail if the service is not properly configured or if external dependencies (like user management service) are not available
- The CSV report provides detailed information for debugging failed tests

## Troubleshooting

1. **Connection Refused**: Make sure the service is running on the correct port
2. **404 Errors**: Check if the API routes are properly configured
3. **500 Errors**: Check service logs for internal errors
4. **Timeout Errors**: Increase timeout or check service performance

## Customization

To test against a different environment:
1. Modify the `base_url` in `endpoint_test_suite.py`
2. Update test data as needed
3. Adjust expected status codes if your service behaves differently
