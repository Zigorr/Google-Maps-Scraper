import time
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import random


class GoogleMapsScraper:
    """
    Optimized web scraper for extracting business information from Google Maps.
    Designed for maximum speed, accuracy, and reliability in lead generation.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the scraper with Chrome WebDriver and performance optimizations.
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        
        # Enhanced error and duplicate tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.session_restarts = 0
        self.max_session_restarts = 3
        
        self.visited_cids = set()
        self.extraction_failures = []
        
        self.setup_driver()
    
    def setup_driver(self):
        """Sets up Chrome WebDriver with minimal, stable configuration for Google Maps compatibility."""
        try:
            chrome_options = Options()
            
            # Essential flags for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Force English locale
            chrome_options.add_argument("--lang=en-US")
            chrome_options.add_argument("--accept-lang=en-US,en")
            
            # Set viewport and zoom for consistency
            if self.headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--window-size=1920,1080")
            else:
                chrome_options.add_argument("--start-maximized")
            
            chrome_options.add_argument("--force-device-scale-factor=1")
            
            # Minimal logging
            chrome_options.add_argument("--log-level=3")
            
            # Anti-detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set English as preferred language (2024 fix)
            chrome_options.add_experimental_option('prefs', {
                'intl.accept_languages': 'en-US,en'
            })
            
            # Standard user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # REMOVED ALL AGGRESSIVE OPTIMIZATIONS:
            # - No GPU/rendering disabling
            # - No background process disabling  
            # - No memory pressure modifications
            # - No network optimizations
            # - No timer throttling changes
            # - No plugin/extension disabling
            
            # Setup Chrome service
            print("🔧 Setting up Chrome driver...")
            service = ChromeService(ChromeDriverManager().install())
            service.log_path = None
            
            # Initialize driver with timeout
            print("🚀 Starting Chrome browser...")
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Chrome startup timed out")
            
            # Set timeout for Chrome startup (60 seconds)
            if hasattr(signal, 'SIGALRM'):  # Unix systems
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)
            
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Enforce consistent zoom level
                self.driver.set_window_size(1920, 1080)
                self.driver.execute_script("document.body.style.zoom='100%'")

                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                
                print("✅ Chrome browser started successfully")
                
                # Optimized timeout settings for speed (updated 2024)
                self.driver.set_page_load_timeout(30)  # Reduced for faster processing
                self.driver.implicitly_wait(3)  # Reduced for faster element detection
                self.wait = WebDriverWait(self.driver, 10)  # Reduced for faster explicit waits
                
                # Minimal JavaScript injection
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                print("✅ Chrome WebDriver configured for maximum stability")
                
            except TimeoutError:
                print("❌ Chrome startup timed out after 60 seconds")
                raise Exception("Browser startup timed out - please try again")
            except Exception as e:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                raise e
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def search_google_maps(self, keyword: str, city: str) -> bool:
        """
        Optimized Google Maps search with enhanced error recovery.
        
        Args:
            keyword (str): Business type to search for (e.g., "tattoo shops")
            city (str): City to search in (e.g., "Nashville")
            
        Returns:
            bool: True if search was successful, False otherwise
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Check browser connectivity before search
                if not self._is_browser_connected():
                    print(f"❌ Browser not connected on search attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        print("🔄 Attempting to recover browser session...")
                        self._recover_browser_session()
                        continue
                    return False
                
                # Construct search query
                query = f"{keyword} in {city}"
                print(f"🔍 Searching for: {query} (attempt {attempt + 1}/{max_retries})")
                
                # Navigate to Google Maps with optimized URL and English locale
                encoded_query = query.replace(" ", "+")
                url = f"https://www.google.com/maps/search/{encoded_query}?hl=en&gl=us"
                
                # Load page with timeout handling
                self.driver.get(url)
                
                # Enhanced wait for search results with multiple fallback conditions
                try:
                    # Primary wait condition
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='feed']")))
                    print("✅ Search results loaded successfully")
                    self.consecutive_failures = 0  # Reset failure counter
                    return True
                except TimeoutException:
                    # Fallback: check for any business listings
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/maps/place/']"))
                        )
                        print("✅ Search results loaded (fallback detection)")
                        self.consecutive_failures = 0  # Reset failure counter
                        return True
                    except TimeoutException:
                        print(f"⚠️ Search results timeout on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            print(f"🔄 Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            print("❌ All search attempts failed - no businesses found")
                            return False
                    
            except WebDriverException as e:
                print(f"❌ WebDriver error on search attempt {attempt + 1}: {e}")
                if "invalid session id" in str(e).lower():
                    print("🔄 Session lost, attempting recovery...")
                    if attempt < max_retries - 1:
                        self._recover_browser_session()
                        continue
                    return False
                elif attempt < max_retries - 1:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
            except Exception as e:
                print(f"❌ Search failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
        
        return False
    
    def _scroll_results(self):
        """Scrolls the search results panel to load more businesses."""
        try:
            scrollable_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
            
            print("📜 Scrolling to load more results...")
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
            
            for _ in range(10): # Scroll up to 10 times
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                time.sleep(2) # Wait for new results to load
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
                if new_height == last_height:
                    print("✅ Reached the end of the results.")
                    break
                last_height = new_height
                
        except TimeoutException:
            print("⚠️ Could not find scrollable element for results.")
            
    def get_business_listings(self) -> List[str]:
        """
        Optimized extraction of business listing URLs with enhanced error recovery.
        
        Returns:
            List[str]: List of unique business listing URLs
        """
        business_urls = []
        
        try:
            # Initial extraction with improved selectors
            print("📍 Extracting business listings...")
            
            # Enhanced selector for business links
            listing_selector = "[role='feed'] a[href*='/maps/place/']"
            
            # Get initial listings with retry mechanism
            for attempt in range(3):
                try:
                    if not self._is_browser_connected():
                        print(f"❌ Browser disconnected during listing extraction (attempt {attempt + 1})")
                        if attempt < 2:
                            self._recover_browser_session()
                            continue
                        break
                    
                    listings = self.driver.find_elements(By.CSS_SELECTOR, listing_selector)
                    for listing in listings:
                        href = listing.get_attribute('href')
                        if href and '/maps/place/' in href and href not in business_urls:
                            business_urls.append(href)
                    
                    print(f"📍 Found {len(business_urls)} initial business listings")
                    break
                    
                except Exception as e:
                    print(f"⚠️ Error extracting initial listings (attempt {attempt + 1}): {e}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    break
            
            # Scroll to load more results if browser is stable
            if self._is_browser_connected() and len(business_urls) > 0:
                print("📜 Scrolling for more businesses...")
                self._scroll_results()
                
                # Extract additional listings after scrolling
                try:
                    listings = self.driver.find_elements(By.CSS_SELECTOR, listing_selector)
                    for listing in listings:
                        href = listing.get_attribute('href')
                        if href and '/maps/place/' in href and href not in business_urls:
                            business_urls.append(href)
                except Exception as e:
                    print(f"⚠️ Error extracting listings after scroll: {e}")
            
            # Remove any duplicates (just in case)
            business_urls = list(dict.fromkeys(business_urls))
            
            print(f"📍 Total unique businesses found: {len(business_urls)}")
            return business_urls
            
        except WebDriverException as e:
            if "invalid session id" in str(e).lower():
                print("❌ Browser session lost during listing extraction")
                # Return what we have so far
                business_urls = list(dict.fromkeys(business_urls))
                print(f"📍 Partial results: {len(business_urls)} business listings")
                return business_urls
            else:
                print(f"❌ WebDriver error during listing extraction: {e}")
                return []
        except Exception as e:
            print(f"❌ Failed to extract business listings: {e}")
            return []
    
    def _clean_phone(self, phone: str) -> str:
        """Cleans and formats phone numbers to (XXX) XXX-XXXX."""
        if not phone:
            return ""
        
        # Remove non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Handle US numbers
        if cleaned.startswith('+1'):
            cleaned = cleaned[2:]
        elif cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = cleaned[1:]
        
        # Format as (XXX) XXX-XXXX
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        
        return ""
    
    def _clean_address(self, address: str) -> str:
        """Removes Arabic text from address and formats it."""
        if not address:
            return ""
        # Remove common Arabic prefixes/suffixes and normalize
        address = re.sub(r'[\u0600-\u06FF]+', '', address).strip()
        address = re.sub(r'\s*([,GJWX])\s*', r'\1', address)
        address = address.replace("Unnamed Road", "").strip(", ")
        return address

    def _get_element_text(self, by: By, value: str) -> Optional[str]:
        """Safely find an element by a locator and return its text."""
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element.text
        except (NoSuchElementException, TimeoutException):
            return None

    def _get_element_attribute(self, by: By, value: str, attribute: str) -> Optional[str]:
        """Safely find an element and return the value of a given attribute."""
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element.get_attribute(attribute)
        except (NoSuchElementException, TimeoutException):
            return None

    def _classify_website(self, url: str) -> str:
        """Classifies a URL into predefined categories."""
        if not url or not isinstance(url, str) or not re.match(r'^https?://', url):
            return "N/A"
        
        url_lower = url.lower()
        if 'instagram.com' in url_lower:
            return 'instagram'
        if 'facebook.com' in url_lower:
            return 'facebook'
        if 'booksy.com' in url_lower:
            return 'booksy'
        if 'squarespace.com' in url_lower:
            return 'squarespace'
        
        return 'real_website'

    def _run_validation_pass(self, scraped_data: List[Dict], sample_ratio: float = 0.05) -> None:
        """
        Validates a sample of scraped data to ensure selectors are still working.
        """
        if not scraped_data:
            return

        sample_size = int(len(scraped_data) * sample_ratio)
        if sample_size == 0:
            return

        print(f"🕵️  Running validation pass on {sample_size} random samples...")
        validation_sample = random.sample(scraped_data, sample_size)
        failures = 0

        for business in validation_sample:
            self.driver.get(business['url'])
            time.sleep(2)  # Allow page to load
            
            # Re-extract and validate name
            current_name = self._get_element_text(By.CSS_SELECTOR, "h1.DUwDvf")
            if not current_name or current_name.strip() != business['name'].strip():
                failures += 1
                print(f"❌ Validation failed for: {business['name']} (URL: {business['url']})")

        failure_rate = (failures / sample_size) * 100
        print(f"📈 Validation failure rate: {failure_rate:.2f}%")

        if failure_rate > 5.0:
            print("🚨 High validation failure rate detected! Selectors may be outdated.")
            
    def _is_valid_website(self, url: str) -> bool:
        """Validates if a URL is a real website and not a generic booking/social site."""
        if not url or not isinstance(url, str):
            return False
        
        # Exclude Google and internal links
        excluded_domains = [
            'google.com', 'maps.google.com', 'googleusercontent.com',
            'gstatic.com', 'googleapis.com', 'accounts.google.com'
        ]
        
        for domain in excluded_domains:
            if domain in url:
                return False
        
        # Must be a valid HTTP/HTTPS URL
        return url.startswith(('http://', 'https://'))
    
    def _is_browser_connected(self) -> bool:
        """Enhanced browser connection check with multiple verification methods."""
        try:
            if not self.driver:
                print("🔍 Browser check: No driver instance")
                return False
            
            # Test 1: Check if driver is still alive
            try:
                current_url = self.driver.current_url
                if not current_url:
                    print("🔍 Browser check: No current URL")
                    return False
            except Exception as e:
                print(f"🔍 Browser check: Failed to get current URL - {e}")
                return False
            
            # Test 2: Try to execute a simple JavaScript command
            try:
                self.driver.execute_script("return document.readyState;")
            except Exception as e:
                print(f"🔍 Browser check: Failed to execute JavaScript - {e}")
                return False
            
            # Test 3: Check if we can find the body element
            try:
                self.driver.find_element(By.TAG_NAME, "body")
            except Exception as e:
                print(f"🔍 Browser check: Failed to find body element - {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"🔍 Browser check: Unexpected error - {e}")
            return False
    
    def _recover_browser_session(self):
        """Attempt to recover from browser session failures."""
        try:
            print("🔄 Attempting browser session recovery...")
            
            if self.session_restarts >= self.max_session_restarts:
                print(f"❌ Maximum session restarts ({self.max_session_restarts}) reached")
                return False
            
            # Close existing driver
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            # Wait before restart
            time.sleep(2)
            
            # Restart driver
            self.setup_driver()
            self.session_restarts += 1
            
            print(f"✅ Browser session recovered (restart #{self.session_restarts})")
            return True
            
        except Exception as e:
            print(f"❌ Browser session recovery failed: {e}")
            return False
    
    def extract_business_data(self, business_url: str) -> Optional[Dict]:
        """
        Extracts detailed business data from its Google Maps page with structured logging.
        """
        # Updated CID extraction to handle new Google Maps URL format
        cid = None
        # First, try to extract the CID from the 'data' parameter in the URL
        fid_match = re.search(r'!1s0x[a-f0-9]+:0x([a-f0-9]+)', business_url, re.IGNORECASE)
        if fid_match:
            hex_cid = fid_match.group(1)
            cid = str(int(hex_cid, 16))
        else:
            # If the new format is not found, fall back to the classic 'cid=' parameter
            cid_match = re.search(r'cid=(\d+)', business_url)
            if cid_match:
                cid = cid_match.group(1)

        # Use the extracted CID for duplicate checking, or the full URL as a fallback
        unique_identifier = cid if cid else business_url
        if unique_identifier in self.visited_cids:
            print(f"⏭️ Skipping duplicate business (Identifier: {unique_identifier})")
            return None
        self.visited_cids.add(unique_identifier)

        if not cid:
            print("⚠️ Could not extract CID from URL. Using full URL for uniqueness check.")

        # Navigate to business page
        self.driver.get(business_url)
        
        # Scroll to load lazy content
        try:
            scrollable_panel = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
            )
            for _ in range(3):  # Scroll a few times to be sure
                self.driver.execute_script("arguments[0].scrollTop += 500;", scrollable_panel)
                time.sleep(0.5)
        except TimeoutException:
            print("⚠️ Could not find scrollable panel for lazy loading.")

        # Robust data extraction with fallbacks
        name = self._get_element_text(By.CSS_SELECTOR, "h1.DUwDvf")
        phone = self._get_element_text(By.CSS_SELECTOR, "button[data-item-id^='phone'] div.rogA2c")
        address = self._get_element_text(By.CSS_SELECTOR, "button[data-item-id='address'] div.rogA2c")
        website = self._get_element_attribute(By.CSS_SELECTOR, "a[data-item-id='authority']", "href")

        # Fallback for website if authority link is not found
        if not website:
            website = self._get_element_attribute(By.CSS_SELECTOR, "a[aria-label^='Website:']", "href")
            
        # Log failure if name is missing (critical field)
        if not name:
            failure_log = {
                "url": business_url,
                "timestamp": time.time(),
                "missing_fields": ["name"],
                "html_snapshot": self.driver.page_source[:1000]  # Snippet of HTML
            }
            self.extraction_failures.append(failure_log)
            print(f"❌ Failed to extract critical data (name) for {business_url}")
            return None

        # Clean and validate data
        phone = self._clean_phone(phone) if phone else "N/A"
        address = self._clean_address(address) if address else "N/A"
        website_url = website if self._is_valid_website(website) else "N/A"
        website_type = self._classify_website(website_url)

        business_data = {
            "name": name,
            "phone": phone,
            "address": address,
            "website": website_url,
            "website_type": website_type,
            "url": business_url
        }

        return business_data

    def _is_website_link(self, url: str) -> bool:
        """
        Check if a URL is a legitimate website link (not social media or Google services).
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if it's a website link
        """
        if not url:
            return False
            
        # Exclude Google services and common non-website links
        excluded_domains = [
            'google.com', 'maps.google.com', 'facebook.com', 'instagram.com',
            'twitter.com', 'youtube.com', 'tiktok.com', 'linkedin.com'
        ]
        
        for domain in excluded_domains:
            if domain in url.lower():
                return False
                
        return True

    def _is_squarespace_hosted(self, url: str) -> bool:
        """
        Check if a URL is hosted on Squarespace.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if it's Squarespace-hosted
        """
        if not url:
            return False
            
        # Common Squarespace subdomains and domains
        squarespace_domains = [
            'squarespace.com', 'squarespace.net', 'squarespace.org',
            'squarespace.io', 'squarespace.co', 'squarespace.me',
            'squarespace.app', 'squarespace.dev', 'squarespace.test',
            'squarespace.local', 'squarespace.test', 'squarespace.dev'
        ]
        
        for domain in squarespace_domains:
            if domain in url.lower():
                return True
                
        return False
    
    def scrape_businesses(self, keyword: str, city: str, max_businesses: int = 50, retry_on_failure: bool = True) -> List[Dict]:
        """
        Optimized scraping workflow with enhanced speed and reliability.
        
        Args:
            keyword (str): Business type to search for
            city (str): City to search in
            max_businesses (int): Maximum number of businesses to scrape
            retry_on_failure (bool): Whether to retry if browser session fails
            
        Returns:
            List[Dict]: List of business data dictionaries
        """
        print(f"🚀 Starting optimized scrape for '{keyword}' in '{city}'")
        print(f"🔧 Configuration: max_businesses={max_businesses}, retry_on_failure={retry_on_failure}")
        
        try:
            # Step 1: Search Google Maps
            if not self.search_google_maps(keyword, city):
                print("❌ Failed to search Google Maps")
                return []
            
            # Step 2: Get business listing URLs
            business_urls = self.get_business_listings()
            
            if not business_urls:
                print("❌ No business listings found")
                return []
            
            # Limit to max_businesses
            business_urls = business_urls[:max_businesses]
            print(f"📍 Processing {len(business_urls)} businesses...")
            
            # Step 3: Extract data from each business with optimized processing
            all_business_data = []
            failed_extractions = 0
            
            for i, url in enumerate(business_urls, 1):
                print(f"\n📊 Processing {i}/{len(business_urls)} - {(i/len(business_urls)*100):.1f}%")
                
                # Enhanced connectivity check with recovery
                if not self._is_browser_connected():
                    print("❌ Browser disconnected during data extraction.")
                    self.consecutive_failures += 1
                    
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        print(f"❌ Too many consecutive failures ({self.consecutive_failures})")
                        if retry_on_failure and self.session_restarts < self.max_session_restarts:
                            print("🔄 Attempting to restart browser session...")
                            if self._recover_browser_session():
                                self.consecutive_failures = 0
                                # Retry current business
                                i -= 1
                                continue
                            else:
                                print("❌ Failed to restart browser session")
                                break
                        else:
                            print("❌ Maximum retries reached or retry disabled")
                            break
                    else:
                        print(f"🔄 Attempting quick recovery (failure {self.consecutive_failures}/{self.max_consecutive_failures})...")
                        if self._recover_browser_session():
                            self.consecutive_failures = 0
                            # Retry current business
                            i -= 1
                            continue
                        else:
                            failed_extractions += 1
                            print(f"⚠️ Failed to extract data from business {i}")
                            continue
                
                business_data = self.extract_business_data(url)
                if business_data:
                    all_business_data.append(business_data)
                    print(f"✅ {business_data['name']}")
                    self.consecutive_failures = 0  # Reset on success
                else:
                    failed_extractions += 1
                    self.consecutive_failures += 1
                    print(f"⚠️ Failed to extract data from business {i}")
                
                # Progressive delay based on consecutive failures
                if self.consecutive_failures > 0:
                    delay = min(0.5 + (self.consecutive_failures * 0.2), 2.0)
                    print(f"⏱️ Waiting {delay:.1f}s before next extraction...")
                    time.sleep(delay)
                else:
                    time.sleep(0.3)  # Slightly increased base delay for stability
            
            # Summary
            success_rate = (len(all_business_data) / len(business_urls)) * 100 if business_urls else 0
            print(f"\n✅ Scraping completed!")
            print(f"📊 Successfully extracted: {len(all_business_data)}/{len(business_urls)} ({success_rate:.1f}%)")
            if failed_extractions > 0:
                print(f"⚠️ Failed extractions: {failed_extractions}")
            print(f"🔄 Session restarts: {self.session_restarts}")
            
            # Run validation pass on scraped data
            self._run_validation_pass(all_business_data)

            # Report extraction failures
            if self.extraction_failures:
                print("\n--- Extraction Failure Report ---")
                print(f"Total failures: {len(self.extraction_failures)}")
                for failure in self.extraction_failures:
                    print(f"URL: {failure['url']}, Missing: {failure['missing_fields']}")
                print("---------------------------------")

            return all_business_data
            
        except Exception as e:
            print(f"❌ Scraping failed with error: {e}")
            if retry_on_failure and self.session_restarts < self.max_session_restarts:
                print("🔄 Attempting full retry...")
                try:
                    self.close()
                    self.setup_driver()
                    self.session_restarts += 1
                    return self.scrape_businesses(keyword, city, max_businesses, False)
                except Exception as retry_error:
                    print(f"❌ Retry failed: {retry_error}")
            return []
    
    def close(self):
        """Close the WebDriver and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Browser closed")
            except:
                print("🔒 Browser cleanup completed")
        self.driver = None
        self.wait = None 