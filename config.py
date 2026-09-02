# Screenshot API Configuration File
# Edit these settings according to your setup

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = 'YOUR_AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'YOUR_AWS_SECRET_ACCESS_KEY'
AWS_REGION = 'us-west-2'
S3_BUCKET_NAME = 'mf-infringement-bucket-manual-social-media'

POPUP_HANDLING_ENABLED = True # Enable/disable popup handling
POPUP_WAIT_TIME = 2 # seconds to wait for popups to appear
SMART_LOGIN_DETECTION = True # Enable/disable smart login detection
VERIFY_COOKIES = True # Enable/disable cookie verification

# ChromeDriver Configuration
# Set the full path to your ChromeDriver executable
# Examples:
# Windows: r"C:\chromedriver\chromedriver.exe"
# Linux: "/usr/bin/chromedriver"
# macOS: "/usr/local/bin/chromedriver"
CHROMEDRIVER_PATH = r"drivers\chromedriver.exe"  # Set to None to auto-detect, or specify full path

# API Configuration
API_HOST = '0.0.0.0'
API_PORT = 5000
DEBUG_MODE = False

# Screenshot Configuration
DEFAULT_ZOOM = 100
SCREENSHOT_TIMEOUT = 20  # seconds
PAGE_LOAD_TIMEOUT = 10   # seconds

# Directory Configuration
# These will be created automatically in your home directory
BASE_DIR_NAME = r"C:\Users\Acer\OneDrive - Pixeltruth\Desktop\Pixeltruth Codes\Screenshotapi\Screenshot_API"
SCREENSHOTS_DIR_NAME = r"C:\Users\Acer\OneDrive - Pixeltruth\Desktop\Pixeltruth Codes\Screenshotapi\screenshots"
BACKGROUND_DIR_NAME = r"C:\Users\Acer\OneDrive - Pixeltruth\Desktop\Pixeltruth Codes\Screenshotapi\background"
DRIVERS_DIR_NAME = r"C:\Users\Acer\OneDrive - Pixeltruth\Desktop\Pixeltruth Codes\Screenshotapi\drivers"

# Social Media Credentials
TWITTER_CREDENTIALS = [
    {'username': 'user1@example.com', 'password': 'YourStrongPassword123!'},
    {'username': 'user2@example.com', 'password': 'YourStrongPassword123!'},
    {'username': 'user3@example.com', 'password': 'YourStrongPassword123!'},
    {'username': 'user4@example.com', 'password': 'YourStrongPassword123!'},
    {'username': 'user5@example.com', 'password': 'YourStrongPassword123!'}
]

INSTAGRAM_CREDENTIALS = {
    'username': 'your_insta_user',
    'password': 'YourStrongPassword123!'
}

# Facebook Cookies (for authentication)
FACEBOOK_COOKIES = {
    "datr": "YOUR_FACEBOOK_DATR_COOKIE",
    "wd": "1227x912",
    "ps_l": "1",
    "ps_n": "1",
    "usida": "YOUR_USIDA_COOKIE",
    "sb": "YOUR_SB_COOKIE",
    "c_user": "YOUR_FB_USER_ID",
    "presence": "YOUR_PRESENCE_COOKIE",
    "xs": "YOUR_FACEBOOK_XS_COOKIE",
    "fr": "YOUR_FACEBOOK_FR_COOKIE"
}

# Threading Configuration
MAX_WORKERS = 3

# Logging Configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR 