#!/usr/bin/env python3
"""
Test script to verify Screenshot API installation
This script checks if all dependencies and components are properly installed
"""

import sys
import subprocess
import os
import importlib

# Import configuration
from config import *

def print_status(message, status):
    """Print colored status message"""
    if status:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", True)
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.7+)", False)
        return False

def check_python_dependencies():
    """Check if all Python dependencies are installed"""
    dependencies = [
        'flask', 'selenium', 'boto3', 'requests', 'werkzeug',
        'jinja2', 'markupsafe', 'itsdangerous', 'click', 'blinker',
        'botocore', 'jmespath', 'python_dateutil', 'urllib3',
        's3transfer', 'six', 'certifi', 'charset_normalizer', 'idna'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            importlib.import_module(dep.replace('-', '_'))
            print_status(f"Python package: {dep}", True)
        except ImportError:
            print_status(f"Python package: {dep}", False)
            missing.append(dep)
    
    return len(missing) == 0

def check_chrome():
    """Check if Chrome is installed"""
    # Common Chrome paths
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",  # Windows
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",  # Windows
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Linux
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_status(f"Google Chrome: {version}", True)
                    return True
            except:
                pass
    
    print_status("Google Chrome: Not found", False)
    return False

def check_chromedriver():
    """Check if ChromeDriver is installed using config settings"""
    # If specific path is set in config, check it first
    if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
        try:
            result = subprocess.run([CHROMEDRIVER_PATH, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                print_status(f"ChromeDriver (config): {version}", True)
                return True
        except:
            pass
    
    # Otherwise, try to find in common locations
    possible_paths = [
        "chromedriver",  # If it's in PATH
        "chromedriver.exe",  # Windows
        os.path.join(os.getcwd(), "chromedriver"),
        os.path.join(os.getcwd(), "chromedriver.exe")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_status(f"ChromeDriver: {version}", True)
                    return True
            except:
                pass
    
    # Try to find in PATH
    try:
        result = subprocess.run(['which', 'chromedriver'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        print_status(f"ChromeDriver (PATH): {version}", True)
                        return True
                except:
                    pass
    except:
        pass
    
    # Try Windows 'where' command
    try:
        result = subprocess.run(['where', 'chromedriver'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        print_status(f"ChromeDriver (PATH): {version}", True)
                        return True
                except:
                    pass
    except:
        pass
    
    print_status("ChromeDriver: Not found", False)
    return False

def check_directories():
    """Check if required directories exist using config settings"""
    home_dir = os.path.expanduser("~")
    required_dirs = [
        os.path.join(home_dir, BASE_DIR_NAME),
        os.path.join(home_dir, BASE_DIR_NAME, SCREENSHOTS_DIR_NAME),
        os.path.join(home_dir, BASE_DIR_NAME, BACKGROUND_DIR_NAME),
        os.path.join(home_dir, BASE_DIR_NAME, DRIVERS_DIR_NAME)
    ]
    
    all_good = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print_status(f"Directory: {directory}", True)
        else:
            print_status(f"Directory: {directory}", False)
            all_good = False
    
    return all_good

def test_selenium():
    """Test if Selenium can create a WebDriver using config settings"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Create Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Try to find ChromeDriver (same logic as the main script)
        driver_path = None
        
        # If specific path is set in config, use it
        if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
            driver_path = CHROMEDRIVER_PATH
        
        if not driver_path:
            # Try common locations
            possible_paths = [
                "chromedriver",
                "chromedriver.exe",
                os.path.join(os.getcwd(), "chromedriver"),
                os.path.join(os.getcwd(), "chromedriver.exe")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    driver_path = path
                    break
        
        if not driver_path:
            # Try PATH
            try:
                result = subprocess.run(['which', 'chromedriver'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    driver_path = result.stdout.strip().split('\n')[0]
            except:
                pass
        
        if not driver_path:
            # Try Windows 'where' command
            try:
                result = subprocess.run(['where', 'chromedriver'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    driver_path = result.stdout.strip().split('\n')[0]
            except:
                pass
        
        if not driver_path:
            print_status("Selenium WebDriver test failed: ChromeDriver not found", False)
            return False
        
        # Create service
        service = Service(executable_path=driver_path)
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test basic functionality
        driver.get('https://www.google.com')
        title = driver.title
        
        # Clean up
        driver.quit()
        
        print_status(f"Selenium WebDriver test successful (loaded: {title})", True)
        return True
        
    except Exception as e:
        print_status(f"Selenium WebDriver test failed: {str(e)}", False)
        return False

def test_aws_credentials():
    """Test if AWS credentials are working using config settings"""
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Try to create a session with the credentials from config
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Test S3 access
        s3 = session.resource('s3')
        bucket = s3.Bucket(S3_BUCKET_NAME)
        
        # Try to list objects (this will test credentials)
        list(bucket.objects.limit(1))
        
        print_status("AWS credentials and S3 access working", True)
        return True
        
    except NoCredentialsError:
        print_status("AWS credentials not found", False)
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print_status("AWS credentials working but S3 access denied", False)
        else:
            print_status(f"AWS error: {error_code}", False)
        return False
    except Exception as e:
        print_status(f"AWS test failed: {str(e)}", False)
        return False

def check_config():
    """Check if config file is properly set up"""
    try:
        # Check if required config variables are set
        required_vars = [
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 
            'S3_BUCKET_NAME', 'API_HOST', 'API_PORT'
        ]
        
        for var in required_vars:
            if not globals().get(var):
                print_status(f"Config variable {var} is not set", False)
                return False
        
        print_status("Config file is properly set up", True)
        return True
        
    except Exception as e:
        print_status(f"Config check failed: {str(e)}", False)
        return False

def main():
    """Run all tests"""
    print("🔍 Screenshot API Installation Test")
    print("=" * 60)
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🔧 ChromeDriver Path: {CHROMEDRIVER_PATH or 'Auto-detect'}")
    print(f"☁️  AWS Region: {AWS_REGION}")
    print(f"🪣 S3 Bucket: {S3_BUCKET_NAME}")
    print("=" * 60)
    
    tests = [
        ("Config File", check_config),
        ("Python Version", check_python_version),
        ("Python Dependencies", check_python_dependencies),
        ("Google Chrome", check_chrome),
        ("ChromeDriver", check_chromedriver),
        ("Required Directories", check_directories),
        ("Selenium WebDriver", test_selenium),
        ("AWS Credentials", test_aws_credentials)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your Screenshot API is ready to use!")
        print("\nNext steps:")
        print("1. Start the API: python screenshot_api_endpoint.py")
        print("2. Test the API: python example_usage.py")
        print("3. Check the documentation: README.md")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("1. Check your config.py file")
        print("2. Make sure Chrome and ChromeDriver are installed")
        print("3. Verify your AWS credentials")
        print("4. Set CHROMEDRIVER_PATH in config.py if needed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 