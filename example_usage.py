#!/usr/bin/env python3
"""
Example usage of the Screenshot API
This script demonstrates how to use all the API endpoints
"""

import requests
import json
import time
from typing import List, Dict, Any

class ScreenshotAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the Screenshot API client
        
        Args:
            base_url (str): Base URL of the API server
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    def take_single_screenshot(self, url: str, zoom: int = 100) -> Dict[str, Any]:
        """
        Take a single screenshot
        
        Args:
            url (str): URL to screenshot
            zoom (int): Zoom percentage (default: 100)
            
        Returns:
            dict: API response
        """
        try:
            payload = {
                "url": url,
                "zoom": zoom
            }
            response = self.session.post(
                f"{self.base_url}/screenshot",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    def take_batch_screenshots(self, urls: List[str], zoom: int = 100) -> Dict[str, Any]:
        """
        Take multiple screenshots in batch
        
        Args:
            urls (List[str]): List of URLs to screenshot
            zoom (int): Zoom percentage (default: 100)
            
        Returns:
            dict: API response
        """
        try:
            payload = {
                "urls": urls,
                "zoom": zoom
            }
            response = self.session.post(
                f"{self.base_url}/screenshots/batch",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    def take_async_screenshots(self, urls: List[str], zoom: int = 100) -> Dict[str, Any]:
        """
        Take screenshots asynchronously
        
        Args:
            urls (List[str]): List of URLs to screenshot
            zoom (int): Zoom percentage (default: 100)
            
        Returns:
            dict: API response with job ID
        """
        try:
            payload = {
                "urls": urls,
                "zoom": zoom
            }
            response = self.session.post(
                f"{self.base_url}/screenshots/async",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}

def print_response(title: str, response: Dict[str, Any]):
    """Print formatted API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(json.dumps(response, indent=2))
    print(f"{'='*50}")

def main():
    """Main function demonstrating API usage"""
    
    # Initialize client
    client = ScreenshotAPIClient()
    
    print("🚀 Screenshot API Example Usage")
    print("Make sure the API server is running on http://localhost:5000")
    print()
    
    # Test URLs (replace with actual URLs you want to test)
    test_urls = [
        "https://www.facebook.com/example1",
        "https://www.instagram.com/example2",
        "https://twitter.com/example3"
    ]
    
    # 1. Health Check
    print("1. Testing Health Check...")
    health_response = client.health_check()
    print_response("Health Check Response", health_response)
    
    if health_response.get("status") != "healthy":
        print("❌ API is not healthy. Please check if the server is running.")
        return
    
    # 2. Single Screenshot
    print("2. Testing Single Screenshot...")
    single_response = client.take_single_screenshot(test_urls[0])
    print_response("Single Screenshot Response", single_response)
    
    if single_response.get("status") == "success":
        print(f"✅ Screenshot taken successfully!")
        print(f"📸 Screenshot URL: {single_response.get('screenshot_url')}")
    else:
        print(f"❌ Screenshot failed: {single_response.get('error', 'Unknown error')}")
    
    # 3. Batch Screenshots
    print("3. Testing Batch Screenshots...")
    batch_response = client.take_batch_screenshots(test_urls[:2])  # Test with 2 URLs
    print_response("Batch Screenshots Response", batch_response)
    
    if "results" in batch_response:
        successful = sum(1 for result in batch_response["results"] if result.get("status") == "success")
        print(f"✅ Successfully processed {successful}/{len(batch_response['results'])} screenshots")
        
        for i, result in enumerate(batch_response["results"]):
            if result.get("status") == "success":
                print(f"   📸 Screenshot {i+1}: {result.get('screenshot_url')}")
            else:
                print(f"   ❌ Screenshot {i+1} failed: {result.get('error', 'Unknown error')}")
    
    # 4. Async Screenshots
    print("4. Testing Async Screenshots...")
    async_response = client.take_async_screenshots(test_urls)
    print_response("Async Screenshots Response", async_response)
    
    if async_response.get("status") == "processing":
        print(f"✅ Async job started with ID: {async_response.get('job_id')}")
        print(f"📊 Processing {async_response.get('total_urls')} URLs")
    else:
        print(f"❌ Async job failed: {async_response.get('error', 'Unknown error')}")
    
    # 5. Error Handling Examples
    print("5. Testing Error Handling...")
    
    # Invalid URL
    invalid_response = client.take_single_screenshot("invalid-url")
    print_response("Invalid URL Response", invalid_response)
    
    # Unsupported platform
    unsupported_response = client.take_single_screenshot("https://www.google.com")
    print_response("Unsupported Platform Response", unsupported_response)
    
    # Empty batch
    empty_batch_response = client.take_batch_screenshots([])
    print_response("Empty Batch Response", empty_batch_response)

def interactive_mode():
    """Interactive mode for testing the API"""
    client = ScreenshotAPIClient()
    
    print("🎯 Interactive Screenshot API Testing")
    print("Type 'quit' to exit")
    print()
    
    while True:
        print("\nOptions:")
        print("1. Health check")
        print("2. Single screenshot")
        print("3. Batch screenshots")
        print("4. Async screenshots")
        print("5. Quit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            response = client.health_check()
            print_response("Health Check", response)
            
        elif choice == "2":
            url = input("Enter URL: ").strip()
            if url.lower() == "quit":
                break
            zoom = input("Enter zoom level (default 100): ").strip()
            zoom = int(zoom) if zoom.isdigit() else 100
            
            response = client.take_single_screenshot(url, zoom)
            print_response("Single Screenshot", response)
            
        elif choice == "3":
            print("Enter URLs (one per line, empty line to finish):")
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
            
            if urls:
                zoom = input("Enter zoom level (default 100): ").strip()
                zoom = int(zoom) if zoom.isdigit() else 100
                
                response = client.take_batch_screenshots(urls, zoom)
                print_response("Batch Screenshots", response)
            else:
                print("No URLs provided")
                
        elif choice == "4":
            print("Enter URLs (one per line, empty line to finish):")
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
            
            if urls:
                zoom = input("Enter zoom level (default 100): ").strip()
                zoom = int(zoom) if zoom.isdigit() else 100
                
                response = client.take_async_screenshots(urls, zoom)
                print_response("Async Screenshots", response)
            else:
                print("No URLs provided")
                
        elif choice == "5" or choice.lower() == "quit":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main() 