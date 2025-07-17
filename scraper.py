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
        
        # Intelligent caching system
        self.business_cache = {}  # URL -> business_data cache
        self.failed_urls = set()  # URLs that failed extraction
        
        # Enhanced error tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.session_restarts = 0
        self.max_session_restarts = 3
        
        self.setup_driver()
    
    def setup_driver(self):
        """Sets up Chrome WebDriver with minimal, stable configuration for Google Maps compatibility."""
        try:
            chrome_options = Options()
            
            # Essential flags only - removing aggressive optimizations
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Headless mode for GUI (but more stable)
            if self.headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--window-size=1920,1080")
            else:
                chrome_options.add_argument("--start-maximized")
            
            # Minimal logging suppression
            chrome_options.add_argument("--log-level=3")
            
            # Basic anti-detection (minimal)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
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
                
                # Cancel timeout if successful
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                
                print("✅ Chrome browser started successfully")
                
                # Conservative timeout settings for stability
                self.driver.set_page_load_timeout(45)  # Increased for stability
                self.driver.implicitly_wait(10)  # Increased for stability
                self.wait = WebDriverWait(self.driver, 20)  # Increased for stability
                
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
                
                # Navigate to Google Maps with optimized URL
                encoded_query = query.replace(" ", "+")
                url = f"https://www.google.com/maps/search/{encoded_query}"
                
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
    
    def _scroll_results(self):
        """Optimized scrolling through search results to load more businesses."""
        try:
            results_panel = self.driver.find_element(By.CSS_SELECTOR, "[role='feed']")
            
            # Get initial business count
            initial_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']"))
            max_scrolls = 5  # Increased back to 5 for better coverage
            
            for i in range(max_scrolls):
                try:
                    # Check browser connectivity
                    if not self._is_browser_connected():
                        print("⚠️ Browser disconnected during scrolling")
                        break
                    
                    # Get current count before scrolling
                    current_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']"))
                    
                    # Perform optimized scroll
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                        results_panel
                    )
                    
                    # Smart wait with longer timeout for better reliability
                    try:
                        WebDriverWait(self.driver, 5).until(
                            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']")) > current_count
                        )
                        new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']"))
                        print(f"📜 Scroll {i+1}/{max_scrolls}: {current_count} → {new_count} businesses")
                    except TimeoutException:
                        print(f"📜 Scroll {i+1}/{max_scrolls}: No new content loaded")
                        # If no new content for 2 consecutive scrolls, stop
                        if i > 0:
                            break
                        time.sleep(0.5)  # Increased pause for better stability
                        
                except WebDriverException as e:
                    if "invalid session id" in str(e).lower():
                        print("⚠️ Session lost during scrolling")
                        break
                    else:
                        print(f"⚠️ Scroll error: {e}")
                        break
                        
            # Final count
            final_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']"))
            print(f"📜 Scrolling complete: {initial_count} → {final_count} total businesses")
            
        except Exception as e:
            print(f"⚠️ Scrolling failed: {e}")
    
    def _extract_phone_fallback(self, business_data: Dict):
        """Enhanced fallback method for phone extraction."""
        try:
            # Multiple phone patterns with priority
            phone_patterns = [
                r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                r'([0-9]{3})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            ]
            
            # Search in page text for phone numbers
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # Format the first match found
                    match = matches[0]
                    if len(match) == 3:
                        formatted_phone = f"({match[0]}) {match[1]}-{match[2]}"
                        business_data['phone'] = formatted_phone
                        return
        except:
            pass
    
    def _is_valid_website(self, url: str) -> bool:
        """Check if URL is a valid website to extract."""
        if not url:
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
        Extract detailed information from a single business listing with caching.
        
        Args:
            business_url (str): URL of the business listing
            
        Returns:
            Optional[Dict]: Business data or None if extraction failed
        """
        # Check cache first
        if business_url in self.business_cache:
            print(f"📋 Using cached data for: {business_url}")
            return self.business_cache[business_url]
        
        # Skip if previously failed
        if business_url in self.failed_urls:
            print(f"⚠️ Skipping previously failed URL: {business_url}")
            return None
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Check browser connectivity before extraction
                if not self._is_browser_connected():
                    print(f"❌ Browser not connected for extraction attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        self._recover_browser_session()
                        continue
                    else:
                        self.failed_urls.add(business_url)
                        return None
                
                print(f"🔍 Extracting data from: {business_url} (attempt {attempt + 1}/{max_retries})")
                
                # Cross-platform timeout mechanism
                import threading
                extraction_timeout = 30  # 30 seconds max per business
                timeout_occurred = threading.Event()
                
                def extraction_worker():
                    """Worker function that performs the actual extraction."""
                    try:
                        # Navigate to business page with timeout protection
                        self.driver.get(business_url)
                        
                        # Wait for page to load with shorter timeout
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, [data-section-id='hero']"))
                            )
                        except TimeoutException:
                            print(f"⚠️ Page load timeout on attempt {attempt + 1}, proceeding with extraction")
                        
                        business_data = {
                            'name': '',
                            'phone': '',
                            'address': '',
                            'website': '',
                            'description': '',
                            'url': business_url
                        }
                        
                        # Quick extraction with timeout protection
                        extraction_map = {
                            'name': [
                                "h1[data-attrid='title']",
                                "h1.DUwDvf",
                                "h1",
                                "[data-section-id='hero'] h1"
                            ],
                            'phone': [
                                "[data-item-id*='phone'] span[aria-label]",
                                "[data-item-id*='phone'] span",
                                "button[data-item-id*='phone']",
                                "span[data-local-attribute='d3ph']"
                            ],
                            'address': [
                                "[data-item-id*='address'] span[aria-label]",
                                "[data-item-id*='address'] span",
                                "button[data-item-id*='address']",
                                "[data-section-id='ad'] span"
                            ]
                        }
                        
                        # Extract basic info with timeout protection
                        for field, selectors in extraction_map.items():
                            if timeout_occurred.is_set():
                                break
                            for selector in selectors:
                                try:
                                    # Quick find with short timeout
                                    element = WebDriverWait(self.driver, 2).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                    )
                                    text = element.get_attribute('aria-label') or element.text
                                    if text and text.strip():
                                        business_data[field] = text.strip()
                                        break
                                except:
                                    continue
                            
                            # Quick fallback for phone extraction
                            if field == 'phone' and not business_data['phone']:
                                try:
                                    self._extract_phone_fallback(business_data)
                                except:
                                    pass
                        
                        # Quick website extraction with timeout protection
                        if not timeout_occurred.is_set():
                            try:
                                website_selectors = [
                                    "[data-item-id*='authority'] a",
                                    "[data-item-id*='website'] a",
                                    "a[href*='instagram.com']",
                                    "a[href*='facebook.com']",
                                    "a[href*='twitter.com']",
                                    "a[href*='squarespace.com']",
                                    "a[href*='booksy.com']"
                                ]
                                
                                for selector in website_selectors:
                                    if timeout_occurred.is_set():
                                        break
                                    try:
                                        elements = WebDriverWait(self.driver, 1).until(
                                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                                        )
                                        for element in elements:
                                            href = element.get_attribute('href')
                                            if href and self._is_valid_website(href):
                                                business_data['website'] = href
                                                break
                                        if business_data['website']:
                                            break
                                    except:
                                        continue
                                        
                            except Exception as e:
                                print(f"⚠️ Website extraction skipped due to timeout protection")
                        
                        # Quick description extraction (optional)
                        if not timeout_occurred.is_set():
                            try:
                                description_selectors = [
                                    "[data-section-id='overview'] span",
                                    ".section-editorial-quote",
                                    "[class*='editorial'] span"
                                ]
                                
                                description_texts = []
                                for selector in description_selectors:
                                    if timeout_occurred.is_set():
                                        break
                                    try:
                                        elements = WebDriverWait(self.driver, 1).until(
                                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                                        )
                                        for element in elements:
                                            text = element.text.strip()
                                            if text and len(text) > 10 and text not in description_texts:
                                                description_texts.append(text)
                                                break  # Only get first description
                                        if description_texts:
                                            break
                                    except:
                                        continue
                                
                                if description_texts:
                                    business_data['description'] = description_texts[0]  # Just first one
                                    
                            except Exception as e:
                                print(f"⚠️ Description extraction skipped due to timeout protection")
                        
                        return business_data
                        
                    except Exception as e:
                        print(f"❌ Error in extraction worker: {e}")
                        return None
                
                # Run extraction in thread with timeout
                result = [None]  # Use list to store result from thread
                
                def run_extraction():
                    result[0] = extraction_worker()
                
                extraction_thread = threading.Thread(target=run_extraction)
                extraction_thread.daemon = True
                extraction_thread.start()
                extraction_thread.join(timeout=extraction_timeout)
                
                if extraction_thread.is_alive():
                    # Timeout occurred
                    print(f"⏰ Extraction timeout on attempt {attempt + 1} (>{extraction_timeout}s)")
                    timeout_occurred.set()
                    # Force thread to recognize timeout
                    time.sleep(1)
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying extraction in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print("❌ All extraction attempts timed out")
                        self.failed_urls.add(business_url)
                        return None
                
                business_data = result[0]
                if business_data is None:
                    print(f"⚠️ No data extracted on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying extraction in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print("❌ Failed to extract data after all attempts")
                        self.failed_urls.add(business_url)
                        return None
                
                # Validate extracted data
                if not business_data.get('name'):
                    print(f"⚠️ No business name found on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying extraction in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print("❌ Failed to extract business name after all attempts")
                        self.failed_urls.add(business_url)
                        return None
                
                # Cache successful extraction
                self.business_cache[business_url] = business_data
                self.consecutive_failures = 0  # Reset failure counter
                return business_data
                
            except WebDriverException as e:
                print(f"❌ WebDriver error on extraction attempt {attempt + 1}: {e}")
                if "invalid session id" in str(e).lower():
                    print("🔄 Session lost, attempting recovery...")
                    if attempt < max_retries - 1:
                        self._recover_browser_session()
                        continue
                    else:
                        self.failed_urls.add(business_url)
                        return None
                elif attempt < max_retries - 1:
                    print(f"🔄 Retrying extraction in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print("❌ All extraction attempts failed")
                    self.failed_urls.add(business_url)
                    return None
            except Exception as e:
                print(f"❌ Extraction failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying extraction in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print("❌ All extraction attempts failed")
                    self.failed_urls.add(business_url)
                    return None
        
        # If we get here, all attempts failed
        self.failed_urls.add(business_url)
        return None
    
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