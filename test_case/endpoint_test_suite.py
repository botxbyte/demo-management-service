#!/usr/bin/env python3
"""
Comprehensive Endpoint Test Suite for Workspace Management Service
Tests all endpoints and generates a CSV report with results.
"""

import asyncio
import csv
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx
from uuid import UUID


class EndpointTester:
    def __init__(self, base_url: str = "http://localhost:8801"):
        self.base_url = base_url
        self.test_results = []
        self.created_workspace_id = None
        self.test_user_id = "550e8400-e29b-41d4-a716-446655440000"
        self.test_workspace_id = "550e8400-e29b-41d4-a716-446655440001"
        
    async def run_test(self, test_name: str, method: str, endpoint: str, 
                      headers: Optional[Dict] = None, 
                      json_data: Optional[Dict] = None,
                      params: Optional[Dict] = None,
                      expected_status: int = 200) -> Dict[str, Any]:
        """Run a single test and return results"""
        url = f"{self.base_url}{endpoint}"
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    json=json_data,
                    params=params
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Check if response is successful
                is_success = response.status_code == expected_status
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text}
                
                result = {
                    "test_name": test_name,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "expected_status": expected_status,
                    "success": is_success,
                    "duration_seconds": round(duration, 3),
                    "response_size_bytes": len(response.content),
                    "timestamp": start_time.isoformat(),
                    "error_message": None if is_success else f"Expected {expected_status}, got {response.status_code}",
                    "response_preview": str(response_data)[:200] + "..." if len(str(response_data)) > 200 else str(response_data)
                }
                
                # Store workspace ID for subsequent tests
                if is_success and "workspace_id" in str(response_data):
                    try:
                        if isinstance(response_data, dict) and "data" in response_data:
                            if isinstance(response_data["data"], dict) and "workspace_id" in response_data["data"]:
                                self.created_workspace_id = str(response_data["data"]["workspace_id"])
                    except:
                        pass
                
                # Also try to extract from list workspaces response
                if is_success and "data" in str(response_data) and "workspaces" in str(response_data):
                    try:
                        if isinstance(response_data, dict) and "data" in response_data:
                            data = response_data["data"]
                            if isinstance(data, list) and len(data) > 0:
                                first_workspace = data[0]
                                if isinstance(first_workspace, dict) and "workspace_id" in first_workspace:
                                    self.created_workspace_id = str(first_workspace["workspace_id"])
                    except:
                        pass
                
                return result
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "test_name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "expected_status": expected_status,
                "success": False,
                "duration_seconds": round(duration, 3),
                "response_size_bytes": 0,
                "timestamp": start_time.isoformat(),
                "error_message": str(e),
                "response_preview": "Connection failed"
            }
    
    async def test_health_check(self):
        """Test health check endpoint"""
        return await self.run_test(
            "Health Check",
            "GET",
            "/api/v1/health/",
            expected_status=200
        )
    
    async def test_create_workspace(self):
        """Test workspace creation"""
        headers = {"user-id": self.test_user_id}
        payload = {
            "name": f"Test Workspace {uuid.uuid4().hex[:8]}",
            "logo": "https://example.com/logo.png"
        }
        
        result = await self.run_test(
            "Create Workspace",
            "POST",
            "/api/v1/workspace/create/",
            headers=headers,
            json_data=payload,
            expected_status=201
        )
        
        # Store the created workspace ID for other tests
        if result["success"]:
            try:
                # Try to extract workspace ID from response
                response_text = result["response_preview"]
                if "workspace_id" in response_text:
                    # This is a simplified extraction - in real scenario, parse JSON properly
                    self.created_workspace_id = str(uuid.uuid4())  # Generate a test UUID
            except:
                pass
        
        return result
    
    async def test_list_workspaces(self):
        """Test listing workspaces"""
        headers = {"user-id": self.test_user_id}
        params = {
            "limit": 10,
            "offset": 0,
            "order_by": "-created_at"
        }
        
        return await self.run_test(
            "List Workspaces",
            "GET",
            "/api/v1/workspaces/",
            headers=headers,
            params=params,
            expected_status=200
        )
    
    async def test_get_workspace(self):
        """Test getting a specific workspace"""
        if not self.created_workspace_id:
            # Use a test UUID if no workspace was created
            test_workspace_id = str(uuid.uuid4())
        else:
            test_workspace_id = self.created_workspace_id
            
        headers = {"user-id": self.test_user_id}
        
        return await self.run_test(
            "Get Workspace",
            "GET",
            f"/api/v1/workspace/read/{test_workspace_id}/",
            headers=headers,
            expected_status=200
        )
    
    async def test_update_workspace(self):
        """Test updating a workspace"""
        if not self.created_workspace_id:
            test_workspace_id = str(uuid.uuid4())
        else:
            test_workspace_id = self.created_workspace_id
            
        headers = {"user-id": self.test_user_id}
        payload = {
            "name": f"Updated Test Workspace {uuid.uuid4().hex[:8]}",
            "logo": "https://example.com/updated-logo.png"
        }
        
        return await self.run_test(
            "Update Workspace",
            "PATCH",
            f"/api/v1/workspace/update/{test_workspace_id}/",
            headers=headers,
            json_data=payload,
            expected_status=200
        )
    
    async def test_update_workspace_status(self):
        """Test updating workspace status"""
        if not self.created_workspace_id:
            test_workspace_id = str(uuid.uuid4())
        else:
            test_workspace_id = self.created_workspace_id
            
        headers = {"user-id": self.test_user_id}
        payload = {
            "status": "updated",
            "error_message": None,
            "error_user_message": None
        }
        
        return await self.run_test(
            "Update Workspace Status",
            "PATCH",
            f"/api/v1/workspace/update/status/{test_workspace_id}/",
            headers=headers,
            json_data=payload,
            expected_status=200
        )
    
    async def test_update_workspace_is_active(self):
        """Test updating workspace is_active status"""
        if not self.created_workspace_id:
            test_workspace_id = str(uuid.uuid4())
        else:
            test_workspace_id = self.created_workspace_id
            
        headers = {"user-id": self.test_user_id}
        payload = {
            "is_active": False
        }
        
        return await self.run_test(
            "Update Workspace Is Active",
            "PATCH",
            f"/api/v1/workspace/update/is-active/{test_workspace_id}/",
            headers=headers,
            json_data=payload,
            expected_status=200
        )
    
    async def test_get_workspace_members(self):
        """Test getting workspace members"""
        headers = {
            "user-id": self.test_user_id,
            "workspace-id": self.test_workspace_id
        }
        params = {
            "limit": 10,
            "offset": 0,
            "order_by": "-created_at"
        }
        
        return await self.run_test(
            "Get Workspace Members",
            "GET",
            "/api/v1/workspace/members/",
            headers=headers,
            params=params,
            expected_status=200
        )
    
    async def test_assign_member(self):
        """Test assigning member to workspace"""
        headers = {
            "user-id": self.test_user_id,
            "workspace-id": self.test_workspace_id
        }
        params = {
            "member_user_id": "test-member-789",
            "role": "member"
        }
        
        return await self.run_test(
            "Assign Member to Workspace",
            "POST",
            "/api/v1/workspace/assign-member/",
            headers=headers,
            params=params,
            expected_status=200
        )
    
    async def test_delete_workspace(self):
        """Test deleting a workspace"""
        if not self.created_workspace_id:
            test_workspace_id = str(uuid.uuid4())
        else:
            test_workspace_id = self.created_workspace_id
            
        headers = {"user-id": self.test_user_id}
        
        return await self.run_test(
            "Delete Workspace",
            "DELETE",
            f"/api/v1/workspace/delete/{test_workspace_id}/",
            headers=headers,
            expected_status=200
        )
    
    async def test_invalid_endpoint(self):
        """Test invalid endpoint to verify error handling"""
        return await self.run_test(
            "Invalid Endpoint Test",
            "GET",
            "/api/v1/invalid-endpoint/",
            expected_status=404
        )
    
    async def test_invalid_method(self):
        """Test invalid HTTP method"""
        return await self.run_test(
            "Invalid Method Test",
            "PUT",
            "/api/v1/health/",
            expected_status=405
        )
    
    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting comprehensive endpoint testing...")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Define all test methods
        test_methods = [
            self.test_health_check,
            self.test_create_workspace,
            self.test_list_workspaces,
            self.test_get_workspace,
            self.test_update_workspace,
            self.test_update_workspace_status,
            self.test_update_workspace_is_active,
            self.test_get_workspace_members,
            self.test_assign_member,
            self.test_delete_workspace,
            self.test_invalid_endpoint,
            self.test_invalid_method
        ]
        
        # Run tests sequentially to maintain order and dependencies
        for test_method in test_methods:
            print(f"🧪 Running: {test_method.__name__}")
            result = await test_method()
            self.test_results.append(result)
            
            # Print result summary
            status_emoji = "✅" if result["success"] else "❌"
            print(f"   {status_emoji} {result['test_name']}: {result['status_code']} ({result['duration_seconds']}s)")
            if not result["success"]:
                print(f"   ⚠️  Error: {result['error_message']}")
        
        print("=" * 60)
        print("🏁 All tests completed!")
        
        return self.test_results
    
    def generate_csv_report(self, filename: str = "endpoint_test_report.csv"):
        """Generate CSV report of test results"""
        if not self.test_results:
            print("❌ No test results to generate report")
            return
        
        filepath = filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_name', 'method', 'endpoint', 'status_code', 
                'expected_status', 'success', 'duration_seconds', 
                'response_size_bytes', 'timestamp', 'error_message', 
                'response_preview'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.test_results:
                writer.writerow(result)
        
        print(f"📊 CSV report generated: {filepath}")
        
        # Print summary statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        avg_duration = sum(r["duration_seconds"] for r in self.test_results) / total_tests
        
        print("\n📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"   ⏱️  Average Duration: {avg_duration:.3f}s")
        
        return filepath


async def main():
    """Main function to run the test suite"""
    # You can change the base URL here if testing against a different environment
    base_url = "http://localhost:8801"
    
    print("🔧 Workspace Management Service - Endpoint Test Suite")
    print("=" * 60)
    
    tester = EndpointTester(base_url=base_url)
    
    try:
        # Run all tests
        await tester.run_all_tests()
        
        # Generate CSV report
        report_file = tester.generate_csv_report()
        
        print(f"\n🎉 Test suite completed successfully!")
        print(f"📄 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
