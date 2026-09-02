from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import uuid
import random
import time
import re
import os
import traceback
import subprocess
from boto3.session import Session
import io
import boto3
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

# Import configuration
from config import *

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)

class ScreenshotAPI:
    def __init__(self):
        """Initialize the Screenshot API using config settings"""
        
        # Setup directories using config
        self.home_dir = os.path.expanduser("~")
        self.base_dir = os.path.join(self.home_dir, BASE_DIR_NAME)
        self.screenshots_dir = os.path.join(self.base_dir, SCREENSHOTS_DIR_NAME)
        self.background_dir = os.path.join(self.base_dir, BACKGROUND_DIR_NAME)
        self.drivers_dir = os.path.join(self.base_dir, DRIVERS_DIR_NAME)
        
        # Create necessary directories
        for directory in [self.base_dir, self.screenshots_dir, self.background_dir, self.drivers_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Use credentials from config
        self.twitter_credentials = TWITTER_CREDENTIALS
        self.facebook_cookies = FACEBOOK_COOKIES
        self.instagram_credentials = INSTAGRAM_CREDENTIALS
        
        # Initialize AWS session using config
        self.session = Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.s3 = self.session.resource('s3')
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay

    def create_driver(self):
        """Create a new Chrome WebDriver instance using config settings"""
        try:
            # Chrome options for automation
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')  # Start with maximized window
            chrome_options.add_argument('--window-size=1920,1080')  # Set window size
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("--disable-blink-features")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument('--headless')  # Run in headless mode for server
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # Additional options to fix black screenshots
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Anti-bot detection measures
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            
            # Random user agent to avoid detection
            import random
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Use ChromeDriver path from config
            driver_path = self.find_chromedriver()
            if not driver_path:
                raise Exception("ChromeDriver not found. Please set CHROMEDRIVER_PATH in config.py")
            
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute JavaScript to remove automation indicators
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})")
            
            return driver
            
        except Exception as e:
            logger.error(f"Error creating Chrome driver: {str(e)}")
            raise

    def find_chromedriver(self):
        """Find ChromeDriver executable using config settings"""
        # If specific path is set in config, use it
        if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
            logger.info(f"Using ChromeDriver from config: {CHROMEDRIVER_PATH}")
            return CHROMEDRIVER_PATH
        
        # Otherwise, try to find in common locations
        possible_paths = [
            "chromedriver",  # If it's in PATH
            "chromedriver.exe",  # Windows
            os.path.join(self.drivers_dir, "chromedriver"),
            os.path.join(self.drivers_dir, "chromedriver.exe"),
            os.path.join(os.getcwd(), "chromedriver"),
            os.path.join(os.getcwd(), "chromedriver.exe")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found ChromeDriver at: {path}")
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['which', 'chromedriver'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                if os.path.exists(path):
                    logger.info(f"Found ChromeDriver in PATH: {path}")
                    return path
        except:
            pass
        
        # Try Windows 'where' command
        try:
            result = subprocess.run(['where', 'chromedriver'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                if os.path.exists(path):
                    logger.info(f"Found ChromeDriver in PATH: {path}")
                    return path
        except:
            pass
        
        logger.error("ChromeDriver not found. Please set CHROMEDRIVER_PATH in config.py")
        return None

    def generate_image_name(self):
        """Generate unique image name"""
        unique_id = str(uuid.uuid4())
        timestamp = int(time.time())
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"{timestamp}_{unique_id}_{date_str}.jpg"

    def upload_to_s3(self, image_path, image_name):
        """Upload image to S3 and return public URL using config settings"""
        try:
            cdate = datetime.now().strftime('%Y-%m-%d')
            s3_image_path = f'pixeltruth/pxt_automation/{cdate}/{image_name}'
            
            with open(image_path, "rb") as f:
                self.s3.Bucket(S3_BUCKET_NAME).put_object(
                    Key=s3_image_path,
                    Body=f,
                    ContentType='image/jpg'
                )
            
            screenshot_url = f"http://d13uxlm82x9iqw.cloudfront.net/{s3_image_path}"
            return screenshot_url
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return None

    def facebook_login(self, driver):
        """Login to Facebook using cookies from config"""
        try:
            # First navigate to facebook.com to set domain context
            driver.get("https://www.facebook.com/")
            time.sleep(2)
            
            # Now add cookies for facebook.com domain
            cookies_added = 0
            for name, value in self.facebook_cookies.items():
                try:
                    driver.add_cookie({"name": name, "value": value})
                    cookies_added += 1
                except Exception as e:
                    logger.warning(f"Failed to add cookie {name}: {str(e)}")
            
            logger.info(f"Facebook cookies added successfully! ({cookies_added}/{len(self.facebook_cookies)} cookies)")
            
            # Verify cookies were added by checking if we can access a protected page
            if VERIFY_COOKIES:
                cookies_working = self.verify_facebook_cookies(driver)
                if not cookies_working:
                    logger.error("Facebook cookies verification failed - cookies may be invalid or expired")
                    raise Exception("Facebook cookies are invalid or expired. Please update cookies in config.py")
            
        except Exception as e:
            logger.error(f"Facebook login error: {str(e)}")

    def refresh_facebook_cookies(self, driver):
        """Refresh Facebook cookies if they're not working"""
        try:
            logger.info("Refreshing Facebook cookies...")
            
            # Clear existing cookies
            driver.delete_all_cookies()
            time.sleep(1)
            
            # Navigate to Facebook again
            driver.get("https://www.facebook.com/")
            time.sleep(2)
            
            # Add cookies again
            cookies_added = 0
            for name, value in self.facebook_cookies.items():
                try:
                    driver.add_cookie({"name": name, "value": value})
                    cookies_added += 1
                except Exception as e:
                    logger.warning(f"Failed to add cookie {name}: {str(e)}")
            
            logger.info(f"Facebook cookies refreshed! ({cookies_added}/{len(self.facebook_cookies)} cookies)")
            
        except Exception as e:
            logger.error(f"Error refreshing Facebook cookies: {str(e)}")

    def verify_facebook_cookies(self, driver):
        """Verify if Facebook cookies are working by accessing a protected page"""
        try:
            logger.info("Verifying Facebook cookies...")
            
            # Try to access a protected page
            driver.get("https://www.facebook.com/me")
            time.sleep(3)
            
            current_url = driver.current_url.lower()
            
            # Check if redirected to login page
            if "login" in current_url or "auth" in current_url or "checkpoint" in current_url:
                logger.error("Facebook cookies verification failed - redirected to login page")
                return False
            
            # Check if we can access the protected page
            if "me" in current_url or "profile" in current_url:
                logger.info("Facebook cookies verification successful - can access protected pages")
                return True
            else:
                logger.error("Facebook cookies verification failed - unexpected redirect")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying Facebook cookies: {str(e)}")
            return False

    def check_facebook_login_required(self, driver, url):
        """Check if Facebook login is required for the given URL"""
        try:
            # Navigate to the URL first (without cookies)
            driver.get(url)
            # Add random delay to simulate human behavior
            delay = self.random_delay(2, 4)
            logger.info(f"Added random delay: {delay:.2f} seconds")
            time.sleep(3)
            
            # Check if we're redirected to login page
            current_url = driver.current_url.lower()
            if "login" in current_url or "auth" in current_url or "checkpoint" in current_url:
                logger.info(f"Login required - redirected to login/auth page: {driver.current_url}")
                return True
            
            # Check if redirected to home page (means login required)
            if current_url == "https://www.facebook.com/" and url != "https://www.facebook.com/":
                logger.info("Login required - redirected to home page")
                return True
            
            # Special case: Facebook homepage is public (even though it has login forms)
            if url == "https://www.facebook.com/" or url == "https://www.facebook.com":
                logger.info("Facebook homepage detected - treating as public")
                return False
            

            
            # Check for specific login-related text in page source (most reliable for posts)
            page_source = driver.page_source.lower()
            login_text_indicators = [
                'you must log in to continue',
                'log in to see this content',
                'access denied',
                'forbidden',
                'log into facebook',
                'this content is not available right now',
                'this content is no longer available',
                'content not available',
                'this page is not available',
                'page not found'
            ]
            
            for text in login_text_indicators:
                if text in page_source:
                    logger.info(f"Login required - detected text: {text}")
                    return True
            
            # Additional check: Look for content that indicates the page is unavailable/private
            # These patterns suggest the content requires login even if they appear as "content"
            unavailable_patterns = [
                'this content isn\'t available',
                'this content is not available',
                'content isn\'t available',
                'content is not available',
                'this page is not available',
                'page is not available',
                'content unavailable',
                'unavailable content',
                'this content is unavailable',
                'content not available right now',
                'content is no longer available',
                'when this happens, it\'s usually because',
                'owner only shared it with a small group',
                'owner changed who can see it',
                'content was removed',
                'content has been removed'
            ]
            
            for pattern in unavailable_patterns:
                if pattern in page_source:
                    logger.info(f"Login required - detected unavailable pattern: {pattern}")
                    return True
            
            # Special case: Facebook post URLs that show "You must log in to continue" in search results
            # but show different content to Selenium should be treated as requiring login
            # This handles Facebook's anti-bot content delivery
            if ('/posts/' in url or 'permalink.php' in url):
                # Check if we have login forms present (indicates potential login requirement)
                try:
                    login_elements = driver.find_elements(By.CSS_SELECTOR, 'input[name="email"], input[name="pass"], button[type="submit"]')
                    if login_elements and len(login_elements) >= 2:
                        # If we have login forms AND this is a post URL, require login
                        # This catches cases where Facebook shows different content to automation
                        logger.info("Login required - Facebook post URL with login forms present (potential anti-bot content)")
                        return True
                except:
                    pass
            
            # Check for actual meaningful content to determine if page is public
            # Look for actual post content
            content_selectors = [
                '[data-testid="post_message"]',
                '[data-testid="post_text"]',
                '[data-testid="feed_story"]',
                'div[role="article"]',
                'div[role="main"]',
                '[data-testid="post_container"]',
                '[data-testid="story_container"]'
            ]
            
            content_found = False
            meaningful_content = False
            
            # Content that indicates the page is NOT public (requires login)
            unavailable_content_indicators = [
                'this content isn\'t available',
                'this content is not available',
                'content isn\'t available',
                'content is not available',
                'this page is not available',
                'page is not available',
                'content unavailable',
                'unavailable content',
                'this content is unavailable',
                'content not available right now',
                'content is no longer available'
            ]
            
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed() and element.text.strip():
                                text_content = element.text.strip().lower()
                                
                                # Check if this content indicates the page is unavailable/private
                                is_unavailable = False
                                for indicator in unavailable_content_indicators:
                                    if indicator in text_content:
                                        is_unavailable = True
                                        logger.info(f"Found unavailable content indicator: '{indicator}' in text: {text_content[:100]}...")
                                        break
                                
                                if is_unavailable:
                                    # This content indicates login is required
                                    logger.info("Login required - content indicates page is unavailable/private")
                                    return True
                                
                                if len(text_content) > 50:  # Meaningful content
                                    content_found = True
                                    meaningful_content = True
                                    logger.info(f"Found meaningful content: {text_content[:100]}...")
                                    break
                        if meaningful_content:
                            break
                except:
                    continue
            
            # If we found meaningful content, the page is public
            if meaningful_content:
                logger.info("No login required - meaningful content found")
                return False
            
            # Additional check: For Facebook post URLs, if we can't find meaningful content,
            # it's likely that the content is private or requires login
            if ('/posts/' in url or 'permalink.php' in url):
                logger.info("Login required - Facebook post URL with no meaningful content found")
                return True
            
            # Special case: Facebook post URLs that show "You must log in to continue" in search results
            # but show different content to Selenium should be treated as requiring login
            # This handles Facebook's anti-bot content delivery
            if ('/posts/' in url or 'permalink.php' in url):
                # Check if we have login forms present (indicates potential login requirement)
                try:
                    login_elements = driver.find_elements(By.CSS_SELECTOR, 'input[name="email"], input[name="pass"], button[type="submit"]')
                    if login_elements and len(login_elements) >= 2:
                        # If we have login forms AND this is a post URL, require login
                        # This catches cases where Facebook shows different content to automation
                        logger.info("Login required - Facebook post URL with login forms present (potential anti-bot content)")
                        return True
                except:
                    pass
            
            # Additional check: If we're on a Facebook post URL but found no meaningful content,
            # and the page has login forms, it likely requires login
            if ('/posts/' in url or 'permalink.php' in url) and not meaningful_content:
                try:
                    login_elements = driver.find_elements(By.CSS_SELECTOR, 'input[name="email"], input[name="pass"], button[type="submit"]')
                    if login_elements and len(login_elements) >= 2:
                        logger.info("Login required - Facebook post URL with no meaningful content but login forms present")
                        return True
                except:
                    pass
            
            # Check if page has login forms AND is not homepage, likely requires login
            try:
                login_elements = driver.find_elements(By.CSS_SELECTOR, 'input[name="email"], input[name="pass"], button[type="submit"]')
                if login_elements and len(login_elements) >= 2:  # At least email + password fields
                    # Check if we're on a login page (not just a page with login forms)
                    page_title = driver.title.lower()
                    if "log in" in page_title or "login" in page_title:
                        logger.info("Login required - on login page with login form")
                        return True
                    
                    # If no meaningful content found but login forms present, require login
                    if not content_found:
                        logger.info("Login required - login forms present but no meaningful content found")
                        return True
                        
            except Exception as e:
                logger.error(f"Error checking login elements: {e}")
            
            # If no login indicators found, assume page is public
            logger.info("No login indicators detected - page appears to be public")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Facebook login requirement: {str(e)}")
            # If we can't determine, assume login is required for safety
            return True
            # If we can't determine, assume login is required for safety
            return True

    def close_facebook_popups(self, driver):
        """Close various Facebook popups and overlays"""
        try:
            # Wait a bit for popups to appear
            time.sleep(POPUP_WAIT_TIME)
            
            # List of common popup close button selectors
            close_selectors = [
                # Close button with aria-label="Close"
                '[aria-label="Close"]',
                # Close button with role="button" and specific classes
                '[role="button"][aria-label="Close"]',
                # Generic close buttons
                'button[aria-label="Close"]',
                'div[aria-label="Close"]',
                # More specific close button from the provided element
                'div[aria-label="Close"][role="button"][tabindex="0"]',
                # Cookie consent close buttons
                '[data-testid="cookie-policy-manage-accept"]',
                '[data-testid="cookie-policy-dialog-accept"]',
                '[data-testid="cookie-policy-banner-accept"]',
                # Login popup close buttons
                '[data-testid="login_popup_close"]',
                '[data-testid="login_popup_not_now"]',
                # Generic popup close buttons
                '.x1i10hfl[aria-label="Close"]',
                # Additional Facebook-specific selectors
                '[data-testid="popup_close"]',
                '[data-testid="modal_close"]',
                # X buttons with specific classes
                'div[role="button"][tabindex="0"] i[data-visualcompletion="css-img"]',
                # ESC key simulation for any modal
                'body'  # For ESC key simulation
            ]
            
            # Try to close popups using various methods
            for selector in close_selectors:
                try:
                    if selector == 'body':
                        # Try ESC key to close any modal
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                # Try different click methods
                                try:
                                    element.click()
                                    logger.info(f"Closed popup using selector: {selector}")
                                    time.sleep(1)
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Closed popup using JavaScript: {selector}")
                                        time.sleep(1)
                                    except:
                                        continue
                except Exception as e:
                    continue
            
            # Additional popup handling for specific Facebook elements
            try:
                # Handle the specific popup element you mentioned
                specific_popup = driver.find_element(By.CSS_SELECTOR, 
                    'div[aria-label="Close"][role="button"][tabindex="0"]')
                if specific_popup.is_displayed():
                    specific_popup.click()
                    logger.info("Closed specific Facebook popup")
                    time.sleep(1)
            except:
                pass
            
            # Try to find and click the close button using the exact structure you provided
            try:
                # Look for the specific element structure with the icon
                close_elements = driver.find_elements(By.CSS_SELECTOR, 
                    'div[aria-label="Close"][role="button"][tabindex="0"]')
                for element in close_elements:
                    if element.is_displayed():
                        # Try to find the icon inside and click it
                        try:
                            icon = element.find_element(By.CSS_SELECTOR, 'i[data-visualcompletion="css-img"]')
                            if icon.is_displayed():
                                icon.click()
                                logger.info("Closed Facebook popup by clicking icon")
                                time.sleep(1)
                                break
                        except:
                            # If icon click fails, try clicking the parent element
                            try:
                                element.click()
                                logger.info("Closed Facebook popup by clicking parent")
                                time.sleep(1)
                                break
                            except:
                                # Try JavaScript click as last resort
                                driver.execute_script("arguments[0].click();", element)
                                logger.info("Closed Facebook popup using JavaScript")
                                time.sleep(1)
                                break
            except:
                pass
            
            # Try to handle cookie consent banners
            try:
                cookie_buttons = [
                    'button[data-testid="cookie-policy-manage-accept"]',
                    'button[data-testid="cookie-policy-dialog-accept"]',
                    'button[data-testid="cookie-policy-banner-accept"]',
                    '[data-testid="cookie-policy-manage-accept"]',
                    '[data-testid="cookie-policy-dialog-accept"]',
                    '[data-testid="cookie-policy-banner-accept"]'
                ]
                
                for cookie_selector in cookie_buttons:
                    try:
                        cookie_element = driver.find_element(By.CSS_SELECTOR, cookie_selector)
                        if cookie_element.is_displayed():
                            cookie_element.click()
                            logger.info(f"Accepted cookies using: {cookie_selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            # Handle "Not Now" buttons in login popups
            try:
                not_now_buttons = [
                    'button[data-testid="login_popup_not_now"]',
                    '[data-testid="login_popup_not_now"]',
                    'button:contains("Not Now")',
                    'div:contains("Not Now")'
                ]
                
                for not_now_selector in not_now_buttons:
                    try:
                        not_now_element = driver.find_element(By.CSS_SELECTOR, not_now_selector)
                        if not_now_element.is_displayed():
                            not_now_element.click()
                            logger.info(f"Clicked 'Not Now' using: {not_now_selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            logger.info("Facebook popup handling completed")
            
            # Final cleanup - try to remove any remaining overlays
            try:
                # Remove any remaining modal overlays
                overlay_selectors = [
                    '[data-testid="modal_overlay"]',
                    '.modal-overlay',
                    '.popup-overlay',
                    '[role="dialog"]',
                    '.x1n2onr6[role="dialog"]'
                ]
                
                for overlay_selector in overlay_selectors:
                    try:
                        overlays = driver.find_elements(By.CSS_SELECTOR, overlay_selector)
                        for overlay in overlays:
                            if overlay.is_displayed():
                                # Try to hide overlay with CSS
                                driver.execute_script(
                                    "arguments[0].style.display = 'none';", overlay)
                                logger.info(f"Hidden overlay: {overlay_selector}")
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error handling Facebook popups: {str(e)}")

    def close_instagram_popups(self, driver):
        """Close various Instagram popups and overlays"""
        try:
            # Wait a bit for popups to appear
            time.sleep(POPUP_WAIT_TIME)
            
            # List of common Instagram popup close button selectors
            close_selectors = [
                # Close button with aria-label="Close"
                '[aria-label="Close"]',
                # Close button with role="button" and specific classes
                '[role="button"][aria-label="Close"]',
                # Generic close buttons
                'button[aria-label="Close"]',
                'div[aria-label="Close"]',
                # More specific close button from the provided element
                'div[role="button"][tabindex="0"] svg[aria-label="Close"]',
                # Instagram-specific selectors
                '[data-testid="close-button"]',
                '[data-testid="modal-close"]',
                '[data-testid="popup-close"]',
                # SVG close icons
                'svg[aria-label="Close"]',
                'svg[role="img"][aria-label="Close"]',
                # ESC key simulation for any modal
                'body'  # For ESC key simulation
            ]
            
            # Try to close popups using various methods
            for selector in close_selectors:
                try:
                    if selector == 'body':
                        # Try ESC key to close any modal
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                # Try different click methods
                                try:
                                    element.click()
                                    logger.info(f"Closed Instagram popup using selector: {selector}")
                                    time.sleep(1)
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Closed Instagram popup using JavaScript: {selector}")
                                        time.sleep(1)
                                    except:
                                        continue
                except Exception as e:
                    continue
            
            # Try to find and click the close button using the exact structure you provided
            try:
                # Look for the specific element structure with the SVG
                close_elements = driver.find_elements(By.CSS_SELECTOR, 
                    'div[role="button"][tabindex="0"]')
                for element in close_elements:
                    if element.is_displayed():
                        # Try to find the SVG inside and click it
                        try:
                            svg = element.find_element(By.CSS_SELECTOR, 'svg[aria-label="Close"]')
                            if svg.is_displayed():
                                svg.click()
                                logger.info("Closed Instagram popup by clicking SVG")
                                time.sleep(1)
                                break
                        except:
                            # If SVG click fails, try clicking the parent element
                            try:
                                element.click()
                                logger.info("Closed Instagram popup by clicking parent")
                                time.sleep(1)
                                break
                            except:
                                # Try JavaScript click as last resort
                                driver.execute_script("arguments[0].click();", element)
                                logger.info("Closed Instagram popup using JavaScript")
                                time.sleep(1)
                                break
            except:
                pass
            
            # Try to handle cookie consent banners
            try:
                cookie_buttons = [
                    'button[data-testid="cookie-policy-accept"]',
                    '[data-testid="cookie-policy-accept"]',
                    'button:contains("Accept")',
                    'button:contains("Accept All")',
                    'button:contains("Allow")'
                ]
                
                for cookie_selector in cookie_buttons:
                    try:
                        cookie_element = driver.find_element(By.CSS_SELECTOR, cookie_selector)
                        if cookie_element.is_displayed():
                            cookie_element.click()
                            logger.info(f"Accepted Instagram cookies using: {cookie_selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            # Handle "Not Now" buttons in login popups
            try:
                not_now_buttons = [
                    'button[data-testid="login_popup_not_now"]',
                    '[data-testid="login_popup_not_now"]',
                    'button:contains("Not Now")',
                    'div:contains("Not Now")',
                    'button:contains("Skip")',
                    'button:contains("Later")'
                ]
                
                for not_now_selector in not_now_buttons:
                    try:
                        not_now_element = driver.find_element(By.CSS_SELECTOR, not_now_selector)
                        if not_now_element.is_displayed():
                            not_now_element.click()
                            logger.info(f"Clicked 'Not Now' using: {not_now_selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            # Handle "Turn On" notifications popup
            try:
                notification_buttons = [
                    'button[data-testid="notification-popup-not-now"]',
                    '[data-testid="notification-popup-not-now"]',
                    'button:contains("Not Now")',
                    'button:contains("Turn Off")',
                    'button:contains("Skip")'
                ]
                
                for notification_selector in notification_buttons:
                    try:
                        notification_element = driver.find_element(By.CSS_SELECTOR, notification_selector)
                        if notification_element.is_displayed():
                            notification_element.click()
                            logger.info(f"Handled notification popup using: {notification_selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass
            
            logger.info("Instagram popup handling completed")
            
            # Final cleanup - try to remove any remaining overlays
            try:
                # Remove any remaining modal overlays
                overlay_selectors = [
                    '[data-testid="modal_overlay"]',
                    '.modal-overlay',
                    '.popup-overlay',
                    '[role="dialog"]',
                    '.x1n2onr6[role="dialog"]',
                    '[data-testid="modal"]'
                ]
                
                for overlay_selector in overlay_selectors:
                    try:
                        overlays = driver.find_elements(By.CSS_SELECTOR, overlay_selector)
                        for overlay in overlays:
                            if overlay.is_displayed():
                                # Try to hide overlay with CSS
                                driver.execute_script(
                                    "arguments[0].style.display = 'none';", overlay)
                                logger.info(f"Hidden Instagram overlay: {overlay_selector}")
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error handling Instagram popups: {str(e)}")

    def check_instagram_login_required(self, driver, url):
        """Check if Instagram login is required for the given URL"""
        try:
            # Navigate to the URL first
            driver.get(url)
            time.sleep(3)
            
            # Check if we're redirected to login page
            current_url = driver.current_url.lower()
            if "login" in current_url or "auth" in current_url or "accounts/login" in current_url:
                logger.info(f"Login required - redirected to login/auth page: {driver.current_url}")
                return True
            
            # Check if redirected to home page (means login required)
            if current_url == "https://www.instagram.com/" and url != "https://www.instagram.com/":
                logger.info("Login required - redirected to home page")
                return True
            
            # Check for login text in page content
            login_text_indicators = [
                'Log in to Instagram',
                'Log in to continue',
                'You must log in to continue',
                'Log in to see this content',
                'This content is not available right now',
                'This account is private'
            ]
            
            page_source = driver.page_source.lower()
            for text in login_text_indicators:
                if text.lower() in page_source:
                    logger.info(f"Login required - detected text: {text}")
                    return True
            
            # Check for actual content (posts, profile content, etc.)
            content_indicators = [
                # Post content
                '[data-testid="post"]',
                '[data-testid="post_image"]',
                '[data-testid="post_text"]',
                # Profile content
                '[data-testid="profile_picture"]',
                '[data-testid="profile_name"]',
                '[data-testid="profile_bio"]',
                # Story content
                '[data-testid="story"]',
                '[data-testid="story_ring"]',
                # Feed content
                '[data-testid="feed"]',
                '[data-testid="timeline"]',
                # General content
                'article[data-testid="post"]',
                'div[data-testid="post"]',
                # IGTV content
                '[data-testid="igtv"]',
                # Reels content
                '[data-testid="reel"]'
            ]
            
            content_found = False
            for indicator in content_indicators:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                content_found = True
                                logger.info(f"Content found: {indicator}")
                                break
                        if content_found:
                            break
                except:
                    continue
            
            # Check for empty/placeholder content
            empty_content_indicators = [
                'This content is not available right now',
                'This content is no longer available',
                'This content is not available',
                'Content not available',
                'This page is not available',
                'This account is private',
                'This account is not available'
            ]
            
            for text in empty_content_indicators:
                if text.lower() in page_source:
                    logger.info(f"Content not available - login may be required: {text}")
                    return True
            
            # If we found actual content, login is not required
            if content_found:
                logger.info("No login required - actual content found")
                return False
            
            # If we reach here, assume login is not required (content might be public)
            logger.info("No login required - page appears to be public")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Instagram login requirement: {str(e)}")
            # If we can't determine, assume login is required for safety
            return True

    def instagram_login(self, driver):
        """Login to Instagram using credentials from config"""
        try:
            driver.get("https://www.instagram.com/accounts/login")
            time.sleep(3)
            
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(self.instagram_credentials['username'])
            
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.send_keys(self.instagram_credentials['password'])
            
            time.sleep(1)
            login_button = driver.find_element(
                By.XPATH, 
                '/html/body/div[2]/div/div/div[1]/div/div/div/div[1]/section/main/div/div/div/div[2]/form/div/div[3]'
            )
            login_button.click()
            time.sleep(5)
            logger.info("Instagram login successful!")
            
        except Exception as e:
            logger.error(f"Instagram login error: {str(e)}")

    def twitter_login(self, driver):
        """Login to Twitter using credentials from config"""
        try:
            creds = random.choice(self.twitter_credentials)
            username = creds['username']
            password = creds['password']
            
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_field.send_keys(username)
            username_field.send_keys(Keys.RETURN)
            time.sleep(3)
            
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            time.sleep(3)
            
            logger.info("Twitter login successful!")
            
        except Exception as e:
            logger.error(f"Twitter login error: {str(e)}")

    def take_screenshot(self, url, zoom=DEFAULT_ZOOM):
        """
        Take screenshot of a URL using config settings
        
        Args:
            url (str): URL to screenshot
            zoom (int): Zoom percentage (default from config)
            
        Returns:
            dict: Dictionary containing screenshot URL and metadata
        """
        driver = None
        try:
            # Create new driver instance
            driver = self.create_driver()
            
            # Smart login detection and handling
            if SMART_LOGIN_DETECTION:
                if re.search("facebook.com", url):
                    # For Facebook, check if login is required first (without cookies)
                    logger.info("Checking Facebook login requirement without cookies...")
                    login_required = self.check_facebook_login_required(driver, url)
                    
                    if login_required:
                        logger.info("Facebook login required - adding cookies and proceeding with login")
                        # Add cookies only when login is required
                        self.facebook_login(driver)
                        # Navigate to URL with cookies
                        driver.get(url)
                        
                        # Verify if cookies worked - check if login is still required
                        time.sleep(3)
                        login_still_required = self.check_facebook_login_required(driver, url)
                        if login_still_required:
                            logger.error("Facebook cookies failed - login still required after adding cookies")
                            return {
                                'source_url': url,
                                'screenshot_url': None,
                                'timestamp': datetime.now().isoformat(),
                                'status': 'error',
                                'error': 'Facebook cookies are invalid or expired. Please update cookies in config.py'
                            }
                        else:
                            logger.info("Facebook cookies verified - login successful")
                    else:
                        logger.info("Facebook page is public - no cookies needed")
                        # URL is already loaded from the check
                    
                elif re.search("instagram.com", url):
                    # Check if login is required first
                    login_required = self.check_instagram_login_required(driver, url)
                    if login_required:
                        logger.info("Instagram login required - proceeding with login")
                        self.instagram_login(driver)
                        # Navigate back to the original URL after login
                        driver.get(url)
                    else:
                        logger.info("Instagram page is public - no login needed")
                        # URL is already loaded from the check
                        
                elif re.search("twitter.com", url):
                    self.twitter_login(driver)
                    # Navigate to URL after login
                    driver.get(url)
                else:
                    # For other platforms, just navigate to URL
                    driver.get(url)
            else:
                # Legacy behavior - always try to login
                if re.search("facebook.com", url):
                    self.facebook_login(driver)
                elif re.search("instagram.com", url):
                    self.instagram_login(driver)
                elif re.search("twitter.com", url):
                    self.twitter_login(driver)
                
                # Navigate to URL
                driver.get(url)
            
            # Wait for page to load using config timeout
            WebDriverWait(driver, SCREENSHOT_TIMEOUT).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Handle Facebook popups after page load
            if re.search("facebook.com", url) and POPUP_HANDLING_ENABLED:
                self.close_facebook_popups(driver)
            
            # Handle Instagram popups after page load
            elif re.search("instagram.com", url) and POPUP_HANDLING_ENABLED:
                self.close_instagram_popups(driver)
            
            # Handle any remaining login redirects (fallback)
            if "login" in driver.current_url.lower():
                logger.info("Login redirect detected - attempting login")
                if re.search("facebook.com", url):
                    self.facebook_login(driver)
                    time.sleep(3)
                    driver.get(url)
                    # Close popups again after login redirect
                    if POPUP_HANDLING_ENABLED:
                        self.close_facebook_popups(driver)
                elif re.search("instagram.com", url):
                    self.instagram_login(driver)
                    time.sleep(3)
                    driver.get(url)
                    # Close popups again after login redirect
                    if POPUP_HANDLING_ENABLED:
                        self.close_instagram_popups(driver)
                elif re.search("twitter.com", url):
                    self.twitter_login(driver)
                    time.sleep(3)
                    driver.get(url)
            
            # Final check - if we're still on a login page, don't take screenshot
            current_url = driver.current_url.lower()
            if "login" in current_url or "auth" in current_url or "checkpoint" in current_url:
                logger.error("Still on login page after login attempts - cannot take screenshot")
                return {
                    'source_url': url,
                    'screenshot_url': None,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': 'Unable to access content - still redirected to login page'
                }
            
            # Set zoom level
            driver.execute_script(f"document.body.style.zoom = '{zoom}%'")
            
            # Wait for dynamic content using config timeout
            time.sleep(PAGE_LOAD_TIMEOUT)
            
            # Final popup cleanup before screenshot (especially for Facebook and Instagram)
            if re.search("facebook.com", url) and POPUP_HANDLING_ENABLED:
                self.close_facebook_popups(driver)
            elif re.search("instagram.com", url) and POPUP_HANDLING_ENABLED:
                self.close_instagram_popups(driver)
            
            # Check if page has actual content before taking screenshot
            page_source = driver.page_source.lower()
            empty_content_indicators = [
                'this content is not available',
                'this page is not available',
                'content not available',
                'page not found',
                'access denied',
                'forbidden'
            ]
            
            for indicator in empty_content_indicators:
                if indicator in page_source:
                    logger.error(f"Page shows empty/error content: {indicator}")
                    return {
                        'source_url': url,
                        'screenshot_url': None,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'error',
                        'error': f'Page shows empty/error content: {indicator}'
                    }
            
            # Take screenshot
            image_name = self.generate_image_name()
            image_path = os.path.join(self.background_dir, image_name)
            driver.save_screenshot(image_path)
            
            # Upload to S3
            screenshot_url = self.upload_to_s3(image_path, image_name)
            
            # Clean up local file
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return {
                'source_url': url,
                'screenshot_url': screenshot_url,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error taking screenshot of {url}: {str(e)}")
            return {
                'source_url': url,
                'screenshot_url': None,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
        finally:
            if driver:
                driver.quit()

# Initialize the API using config
api = ScreenshotAPI()

# Thread pool for handling multiple requests using config
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Screenshot API',
        'config': {
            'aws_region': AWS_REGION,
            's3_bucket': S3_BUCKET_NAME,
            'chromedriver_path': CHROMEDRIVER_PATH,
            'max_workers': MAX_WORKERS
        }
    })

@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    """
    Take screenshot endpoint
    
    Expected JSON payload:
    {
        "url": "https://www.facebook.com/example",
        "zoom": 100
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'URL is required',
                'status': 'error'
            }), 400
        
        url = data['url']
        zoom = data.get('zoom', DEFAULT_ZOOM)
        
        # Validate URL
        if not re.match(r'^https?://', url):
            return jsonify({
                'error': 'Invalid URL format',
                'status': 'error'
            }), 400
        
        # Validate platform
        if not any(platform in url for platform in ['facebook.com', 'instagram.com', 'twitter.com']):
            return jsonify({
                'error': 'Only Facebook, Instagram, and Twitter URLs are supported',
                'status': 'error'
            }), 400
        
        # Take screenshot
        result = api.take_screenshot(url, zoom)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in screenshot endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/screenshots/batch', methods=['POST'])
def take_multiple_screenshots():
    """
    Take multiple screenshots endpoint
    
    Expected JSON payload:
    {
        "urls": [
            "https://www.facebook.com/example1",
            "https://www.instagram.com/example2",
            "https://twitter.com/example3"
        ],
        "zoom": 100
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({
                'error': 'URLs list is required',
                'status': 'error'
            }), 400
        
        urls = data['urls']
        zoom = data.get('zoom', DEFAULT_ZOOM)
        
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({
                'error': 'URLs must be a non-empty list',
                'status': 'error'
            }), 400
        
        if len(urls) > 10:  # Limit batch size
            return jsonify({
                'error': 'Maximum 10 URLs allowed per batch',
                'status': 'error'
            }), 400
        
        # Validate URLs
        for url in urls:
            if not re.match(r'^https?://', url):
                return jsonify({
                    'error': f'Invalid URL format: {url}',
                    'status': 'error'
                }), 400
            
            if not any(platform in url for platform in ['facebook.com', 'instagram.com', 'twitter.com']):
                return jsonify({
                    'error': f'Unsupported platform: {url}',
                    'status': 'error'
                }), 400
        
        # Take screenshots
        results = []
        for url in urls:
            result = api.take_screenshot(url, zoom)
            results.append(result)
            time.sleep(2)  # Small delay between requests
        
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch screenshot endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/screenshots/async', methods=['POST'])
def take_screenshots_async():
    """
    Asynchronous screenshot endpoint
    
    Expected JSON payload:
    {
        "urls": [
            "https://www.facebook.com/example1",
            "https://www.instagram.com/example2"
        ],
        "zoom": 100
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({
                'error': 'URLs list is required',
                'status': 'error'
            }), 400
        
        urls = data['urls']
        zoom = data.get('zoom', DEFAULT_ZOOM)
        
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({
                'error': 'URLs must be a non-empty list',
                'status': 'error'
            }), 400
        
        if len(urls) > 20:  # Limit async batch size
            return jsonify({
                'error': 'Maximum 20 URLs allowed for async processing',
                'status': 'error'
            }), 400
        
        # Submit tasks to thread pool
        futures = []
        for url in urls:
            future = executor.submit(api.take_screenshot, url, zoom)
            futures.append(future)
        
        # Return job ID for tracking
        job_id = str(uuid.uuid4())
        
        return jsonify({
            'job_id': job_id,
            'total_urls': len(urls),
            'status': 'processing',
            'message': 'Screenshots are being processed asynchronously'
        })
        
    except Exception as e:
        logger.error(f"Error in async screenshot endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting Screenshot API")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🏠 Home Directory: {os.getcwd()}")
    print(f"🌐 API will be available at: http://{API_HOST}:{API_PORT}")
    print(f"🔧 ChromeDriver Path: {CHROMEDRIVER_PATH or 'Auto-detect'}")
    print(f"☁️  AWS Region: {AWS_REGION}")
    print(f"🪣 S3 Bucket: {S3_BUCKET_NAME}")
    print("=" * 60)
    
    # Run the Flask app using config settings
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG_MODE)