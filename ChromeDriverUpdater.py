import os
import sys
import platform
import requests
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

class DriverCompatibilityChecker:
    
    def __init__(self):
        self.os_type = platform.system()
        self.driver_path = self._get_driver_path()
        
    def _get_driver_path(self):
        """Determines the appropriate directory to store driver files based on the OS."""
        username = os.getlogin()
        
        if self.os_type == "Windows":
            return os.path.join(f"C:/Users/William/Documents/GitRepos/AutoLinkedin/assets", "chromedriver.exe")
            # return os.path.join(f"C:/Users/{username}/AppData/Roaming/YourAppName", "chromedriver.exe")
        elif self.os_type == "Darwin":  # macOS's official name
            return os.path.join(f"/Users/{username}/Library/Application Support/YourAppName", "chromedriver")
        elif self.os_type == "Linux":
            return os.path.join(f"/home/{username}/.config/YourAppName", "chromedriver")
        else:
            raise ValueError(f"Unsupported OS: {self.os_type}")
    
    def is_driver_compatible(self):
        """Checks if the existing driver is compatible with the current browser."""
        try:
            _ = webdriver.Chrome(self.driver_path)
            return True
        except SessionNotCreatedException:
            return False
    
    def download_compatible_driver(self):
        """Downloads the compatible ChromeDriver."""
        response = requests.get("https://sites.google.com/a/chromium.org/chromedriver/downloads")
        # Here, some parsing might be needed to find the compatible version link.
        # This example assumes a direct link to the driver for simplicity.
        # driver_link = "https://path_to_compatible_driver_based_on_parsing" 
        with open(self.driver_path, 'wb') as f:
            f.write(response.content)
        
    def ensure_driver_compatibility(self):
        """Ensures driver compatibility. If incompatible, downloads the right driver."""
        if not self.is_driver_compatible():
            self.download_compatible_driver()

# Usage:
checker = DriverCompatibilityChecker()
checker.ensure_driver_compatibility()
