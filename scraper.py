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
        
        self.setup_driver()
    
    def setup_driver(self):
        """Sets up Chrome WebDriver with optimized options for maximum performance."""
        try:
            chrome_options = Options()
            
            # Performance optimization flags
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading without images
            chrome_options.add_argument("--disable-javascript")  # Faster page loads
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Memory optimization
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            chrome_options.add_argument("--aggressive-cache-discard")
            
            # Network optimization
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-features=MediaRouter")
            
            # Headless mode for GUI
            if self.headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
                chrome_options.add_argument("--window-size=1920,1080")
            else:
                chrome_options.add_argument("--start-maximized")
            
            # Suppress all logging and errors
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-gpu-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            
            # Anti-detection measures (lightweight)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Optimized user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Setup Chrome service with optimized settings
            service = ChromeService(ChromeDriverManager().install())
            service.log_path = None
            
            # Initialize driver with optimized settings
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set optimized timeouts
            self.driver.set_page_load_timeout(15)  # Faster timeout
            self.driver.implicitly_wait(2)  # Reduced implicit wait
            self.wait = WebDriverWait(self.driver, 8)  # Faster explicit wait
            
            # Execute performance optimization scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome WebDriver optimized for maximum performance")
            
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
        try:
            # Construct search query
            query = f"{keyword} in {city}"
            print(f"🔍 Searching for: {query}")
            
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
                return True
            except TimeoutException:
                # Fallback: check for any business listings
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/maps/place/']"))
                    )
                    print("✅ Search results loaded (fallback detection)")
                    return True
                except TimeoutException:
                    print("⚠️ Search results timeout - no businesses found")
                    return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
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
            
            # Get initial listings
            try:
                listings = self.driver.find_elements(By.CSS_SELECTOR, listing_selector)
                for listing in listings:
                    href = listing.get_attribute('href')
                    if href and '/maps/place/' in href and href not in business_urls:
                        business_urls.append(href)
                
                print(f"📍 Found {len(business_urls)} initial business listings")
            except Exception as e:
                print(f"⚠️ Error extracting initial listings: {e}")
            
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
            max_scrolls = 3  # Reduced from 5 for faster execution
            
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
                    
                    # Smart wait with shorter timeout
                    try:
                        WebDriverWait(self.driver, 2).until(
                            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']")) > current_count
                        )
                        new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "[role='feed'] a[href*='/maps/place/']"))
                        print(f"📜 Scroll {i+1}/{max_scrolls}: {current_count} → {new_count} businesses")
                    except TimeoutException:
                        print(f"📜 Scroll {i+1}/{max_scrolls}: No new content loaded")
                        # If no new content for 2 consecutive scrolls, stop
                        if i > 0:
                            break
                        time.sleep(0.3)  # Brief pause before next scroll
                        
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
        """Enhanced browser connection check."""
        try:
            # Quick connectivity test
            self.driver.current_url
            return True
        except:
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
        
        try:
            self.driver.get(business_url)
            
            # Optimized wait for critical elements only
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, [data-section-id='hero']")))
            except TimeoutException:
                print("⚠️ Page load timeout, proceeding with extraction")
            
            business_data = {
                'name': '',
                'phone': '',
                'address': '',
                'website': '',
                'description': '',
                'url': business_url
            }
            
            # Optimized parallel extraction with priority selectors
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
            
            # Extract basic info in parallel
            for field, selectors in extraction_map.items():
                for selector in selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        text = element.get_attribute('aria-label') or element.text
                        if text and text.strip():
                            business_data[field] = text.strip()
                            break
                    except:
                        continue
                
                # Fallback for phone extraction
                if field == 'phone' and not business_data['phone']:
                    self._extract_phone_fallback(business_data)
            
            # Extract website with comprehensive selectors
            try:
                website_selectors = [
                    "[data-item-id*='authority'] a",
                    "[data-item-id*='website'] a",
                    "a[href*='instagram.com']",
                    "a[href*='facebook.com']",
                    "a[href*='twitter.com']",
                    "a[href*='squarespace.com']",
                    "a[href*='booksy.com']",
                    "a[href*='acuityscheduling.com']",
                    "a[href*='schedulicity.com']",
                    "a[href*='vagaro.com']",
                    "a[href*='styleseat.com']",
                    "a[data-value*='http']"
                ]
                
                for selector in website_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
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
                print(f"⚠️ Website extraction failed: {e}")
            
            # Extract description with enhanced selectors
            try:
                description_selectors = [
                    "[data-section-id='overview'] span",
                    "[data-section-id='overview'] div",
                    ".section-editorial-quote",
                    ".section-editorial-text",
                    "[class*='editorial'] span",
                    "[class*='about'] span",
                    "[class*='description'] span",
                    "div[role='region'] span",
                    "span[class*='text']"
                ]
                
                description_texts = []
                for selector in description_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 10 and text not in description_texts:
                                description_texts.append(text)
                    except:
                        continue
                
                if description_texts:
                    business_data['description'] = ' '.join(description_texts[:3])  # Limit to avoid bloat
                    
            except Exception as e:
                print(f"⚠️ Description extraction failed: {e}")
            
            # Validate extracted data
            if not business_data['name']:
                print("⚠️ No business name found - may be invalid listing")
                self.failed_urls.add(business_url)
                return None
            
            # Cache successful extraction
            self.business_cache[business_url] = business_data
            return business_data
            
        except Exception as e:
            print(f"❌ Failed to extract business data: {e}")
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
            print(f"📍 Processing {len(business_urls)} businesses...")
            
            # Step 3: Extract data from each business with optimized processing
            all_business_data = []
            failed_extractions = 0
            
            for i, url in enumerate(business_urls, 1):
                # Check browser connectivity before processing
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
                
                # Progress indicator
                print(f"📊 Processing {i}/{len(business_urls)} - {(i/len(business_urls)*100):.1f}%")
                
                business_data = self.extract_business_data(url)
                if business_data:
                    all_business_data.append(business_data)
                    print(f"✅ {business_data['name']}")
                else:
                    failed_extractions += 1
                    print(f"⚠️ Failed to extract data from business {i}")
                
                # Minimal delay - reduced from 0.5s to 0.2s
                time.sleep(0.2)
            
            # Summary
            success_rate = (len(all_business_data) / len(business_urls)) * 100 if business_urls else 0
            print(f"\n✅ Scraping completed!")
            print(f"📊 Successfully extracted: {len(all_business_data)}/{len(business_urls)} ({success_rate:.1f}%)")
            if failed_extractions > 0:
                print(f"⚠️ Failed extractions: {failed_extractions}")
            
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