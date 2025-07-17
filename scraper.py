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
    A web scraper for extracting business information from Google Maps.
    Designed to find businesses without established websites for lead generation.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the scraper with Chrome WebDriver.
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Sets up Chrome WebDriver with optimized options for scraping."""
        try:
            chrome_options = Options()
            
            # Basic Chrome options
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Suppress GPU and other error messages
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-gpu-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            
            # Anti-detection measures
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            # User agent to appear more human-like
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Setup Chrome service with logging disabled
            service = ChromeService(ChromeDriverManager().install())
            service.log_path = None
            
            # Initialize driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome WebDriver initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def search_google_maps(self, keyword: str, city: str) -> bool:
        """
        Search Google Maps for businesses matching the keyword and city.
        
        Args:
            keyword (str): Business type to search for (e.g., "tattoo shops")
            city (str): City to search in (e.g., "Nashville")
            
        Returns:
            bool: True if search was successful, False otherwise
        """
        try:
            # Construct search query
            query = f"{keyword} in {city}"
            print(f"🔍 Searching for: {query}")
            
            # Navigate to Google Maps with search query
            encoded_query = query.replace(" ", "+")
            url = f"https://www.google.com/maps/search/{encoded_query}"
            
            self.driver.get(url)
            
            # Wait for search results to load with intelligent waiting
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='feed']")))
                print("✅ Search results loaded successfully")
                return True
            except TimeoutException:
                print("⚠️ Search results took too long to load")
                return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def get_business_listings(self) -> List[str]:
        """
        Extract URLs of individual business listings from search results.
        
        Returns:
            List[str]: List of business listing URLs
        """
        business_urls = []
        
        try:
            # First, get initial listings before scrolling
            listings = self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']")
            for listing in listings:
                href = listing.get_attribute('href')
                if href and '/maps/place/' in href:
                    business_urls.append(href)
            
            print(f"📍 Found {len(business_urls)} initial business listings")
            
            # Scroll to load more results (if browser is stable)
            if self._is_browser_connected():
                self._scroll_results()
                
                # Get listings again after scrolling
                listings = self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']")
                for listing in listings:
                    href = listing.get_attribute('href')
                    if href and '/maps/place/' in href:
                        business_urls.append(href)
            
            # Remove duplicates while preserving order
            business_urls = list(dict.fromkeys(business_urls))
            
            print(f"📍 Total found: {len(business_urls)} business listings")
            return business_urls
            
        except WebDriverException as e:
            if "invalid session id" in str(e).lower():
                print("❌ Browser session lost. Returning listings found so far.")
                # Remove duplicates and return what we have
                business_urls = list(dict.fromkeys(business_urls))
                print(f"📍 Partial results: {len(business_urls)} business listings")
                return business_urls
            else:
                print(f"❌ Failed to extract business listings: {e}")
                return []
        except Exception as e:
            print(f"❌ Failed to extract business listings: {e}")
            return []
    
    def _scroll_results(self):
        """Scroll through search results to load more businesses."""
        try:
            results_panel = self.driver.find_element(By.CSS_SELECTOR, "[role='feed']")
            
            # Scroll multiple times to load more results with intelligent content detection
            for i in range(5):
                try:
                    # Check if browser is still connected
                    if not self._is_browser_connected():
                        print("⚠️ Browser disconnected during scrolling")
                        break
                    
                    # Get current number of results before scrolling
                    previous_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] > div"))
                        
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_panel)
                    
                    # Smart wait for new content to load
                    try:
                        WebDriverWait(self.driver, 3).until(
                            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "[role='feed'] > div")) > previous_count
                        )
                        print(f"📜 Scrolling... ({i+1}/5) - New content loaded")
                    except TimeoutException:
                        print(f"📜 Scrolling... ({i+1}/5) - No new content, continuing")
                        time.sleep(0.5)  # Brief pause if no new content
                except WebDriverException as e:
                    if "invalid session id" in str(e).lower():
                        print("⚠️ Session lost during scrolling, stopping scroll")
                        break
                    else:
                        raise e
                
        except Exception as e:
            print(f"⚠️ Scrolling failed: {e}")
    
    def _is_browser_connected(self) -> bool:
        """Check if the browser session is still active."""
        try:
            self.driver.current_url
            return True
        except WebDriverException:
            return False
    
    def _extract_phone_fallback(self, business_data: Dict) -> None:
        """Fallback method for phone extraction using alternative selectors."""
        try:
            phone_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '(') and contains(text(), ')')]")
            for element in phone_elements:
                text = element.text.strip()
                if re.search(r'\(\d{3}\)\s?\d{3}-?\d{4}', text):
                    business_data['phone'] = text
                    break
        except:
            pass
    
    def extract_business_data(self, business_url: str) -> Optional[Dict]:
        """
        Extract detailed information from a single business listing.
        
        Args:
            business_url (str): URL of the business listing
            
        Returns:
            Optional[Dict]: Business data or None if extraction failed
        """
        try:
            print(f"🏢 Extracting data from: {business_url}")
            self.driver.get(business_url)
            
            # Wait for page to load with intelligent detection
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
            except TimeoutException:
                print("⚠️ Page took too long to load, proceeding with extraction")
            
            business_data = {
                'name': '',
                'phone': '',
                'address': '',
                'website': '',
                'description': '',
                'url': business_url
            }
            
            # Extract all elements in parallel using multiple selectors
            extraction_tasks = [
                ('name', ["h1"], None),
                ('phone', ["[data-item-id*='phone']"], self._extract_phone_fallback),
                ('address', ["[data-item-id*='address']"], None),
            ]
            
            for field, selectors, fallback_func in extraction_tasks:
                try:
                    element_found = False
                    for selector in selectors:
                        try:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            business_data[field] = element.text.strip()
                            element_found = True
                            break
                        except:
                            continue
                    
                    if not element_found and fallback_func:
                        fallback_func(business_data)
                    elif not element_found:
                        print(f"⚠️ Could not find {field}")
                        
                except Exception as e:
                    print(f"⚠️ Error extracting {field}: {e}")
            
            # Extract website with comprehensive selectors
            try:
                website_selectors = [
                    "[data-item-id*='authority']",
                    "[data-item-id*='website']",
                    "a[href*='instagram.com']",
                    "a[href*='facebook.com']",
                    "a[href*='twitter.com']",
                    "a[href*='squarespace.com']",
                    "a[href*='booksy.com']",
                    "a[href*='acuityscheduling.com']",
                    "a[href*='schedulicity.com']",
                    "a[href*='vagaro.com']",
                    "a[href*='styleseat.com']"
                ]
                
                website_found = False
                for selector in website_selectors:
                    try:
                        website_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector.startswith("a[href"):
                            # For link elements, get the href attribute
                            business_data['website'] = website_element.get_attribute('href')
                        else:
                            # For text elements, get the text content
                            business_data['website'] = website_element.text.strip()
                        website_found = True
                        break
                    except:
                        continue
                
                if not website_found:
                    # Alternative website selector - look for any external links
                    try:
                        website_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'google.com'))]")
                        for link in website_links:
                            href = link.get_attribute('href')
                            if self._is_website_link(href):
                                business_data['website'] = href
                                break
                    except:
                        pass
                        
                    # If still no website found, check for Squarespace-hosted sites by looking for powered-by text
                    if not business_data['website']:
                        try:
                            # Look for any links that might be Squarespace-hosted (custom domains)
                            all_links = self.driver.find_elements(By.TAG_NAME, "a")
                            for link in all_links:
                                href = link.get_attribute('href')
                                if href and self._is_squarespace_hosted(href):
                                    business_data['website'] = href
                                    break
                        except:
                            pass
            except:
                pass
            
            # Extract description/overview with comprehensive selectors
            try:
                description_selectors = [
                    "[class*='review'] span",
                    "[class*='description'] span", 
                    "[data-section-id='overview'] span",
                    "[data-section-id='overview'] div",
                    "div[role='region'] span",
                    ".section-editorial-quote",
                    ".section-editorial-text",
                    "[class*='editorial'] span",
                    "[class*='about'] span",
                    "span[class*='text']",
                    "[class*='hours'] span",
                    "[class*='info'] span",
                    "[class*='contact'] span",
                    "[class*='details'] span",
                    "div[class*='text'] span",
                    "div[class*='content'] span"
                ]
                
                descriptions = []
                for selector in description_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if len(text) > 5 and text not in descriptions:  # Lower threshold for more content
                                descriptions.append(text)
                    except:
                        continue
                
                # Also check for any text that might contain Instagram handles, Squarespace, or Booksy mentions
                try:
                    # Look for Instagram handles
                    instagram_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '@') or contains(text(), 'instagram') or contains(text(), 'insta') or contains(text(), 'IG:')]")
                    for element in instagram_elements:
                        text = element.text.strip()
                        if len(text) > 3 and text not in descriptions:
                            descriptions.append(text)
                    
                    # Look for Squarespace mentions
                    squarespace_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'squarespace') or contains(text(), 'square space') or contains(text(), 'book online') or contains(text(), 'online booking')]")
                    for element in squarespace_elements:
                        text = element.text.strip()
                        if len(text) > 3 and text not in descriptions:
                            descriptions.append(text)
                    
                    # Look for Booksy mentions
                    booksy_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'booksy') or contains(text(), 'book appointment') or contains(text(), 'schedule online')]")
                    for element in booksy_elements:
                        text = element.text.strip()
                        if len(text) > 3 and text not in descriptions:
                            descriptions.append(text)
                except:
                    pass
                
                business_data['description'] = ' '.join(descriptions[:10])  # Take first 10 descriptions for more comprehensive data
            except:
                pass
            
            print(f"✅ Extracted data for: {business_data['name']}")
            return business_data
            
        except Exception as e:
            print(f"❌ Failed to extract business data: {e}")
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
        Complete scraping workflow: search and extract data from multiple businesses.
        
        Args:
            keyword (str): Business type to search for
            city (str): City to search in
            max_businesses (int): Maximum number of businesses to scrape
            retry_on_failure (bool): Whether to retry if browser session fails
            
        Returns:
            List[Dict]: List of business data dictionaries
        """
        print(f"🚀 Starting scrape for '{keyword}' in '{city}'")
        
        try:
            # Step 1: Search Google Maps
            if not self.search_google_maps(keyword, city):
                return []
            
            # Step 2: Get business listing URLs
            business_urls = self.get_business_listings()
            
            if not business_urls:
                print("❌ No business listings found")
                return []
            
            # Limit to max_businesses
            business_urls = business_urls[:max_businesses]
            
            # Step 3: Extract data from each business
            all_business_data = []
            
            for i, url in enumerate(business_urls, 1):
                print(f"\n📊 Processing business {i}/{len(business_urls)}")
                
                # Check if browser is still connected before processing
                if not self._is_browser_connected():
                    print("❌ Browser disconnected during data extraction.")
                    if retry_on_failure and len(all_business_data) == 0:
                        print("🔄 Attempting to restart browser session...")
                        try:
                            self.close()
                            self.setup_driver()
                            return self.scrape_businesses(keyword, city, max_businesses, False)
                        except:
                            print("❌ Failed to restart browser session")
                    break
                
                business_data = self.extract_business_data(url)
                if business_data:
                    all_business_data.append(business_data)
                
                # Brief delay between requests to be respectful
                time.sleep(0.5)
            
            print(f"\n✅ Scraping completed! Extracted data from {len(all_business_data)} businesses")
            return all_business_data
            
        except Exception as e:
            print(f"❌ Scraping failed with error: {e}")
            if retry_on_failure:
                print("🔄 Attempting retry...")
                try:
                    self.close()
                    self.setup_driver()
                    return self.scrape_businesses(keyword, city, max_businesses, False)
                except:
                    print("❌ Retry failed")
            return []
    
    def close(self):
        """Close the WebDriver and clean up resources."""
        if self.driver:
            self.driver.quit()
            print("�� Browser closed") 