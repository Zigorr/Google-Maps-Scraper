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
            
            # Anti-detection measures
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent to appear more human-like
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Setup Chrome service
            service = ChromeService(ChromeDriverManager().install())
            
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
            
            # Wait for search results to load
            time.sleep(3)
            
            # Check if results loaded successfully
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
            
            # Scroll multiple times to load more results
            for i in range(5):
                try:
                    # Check if browser is still connected
                    if not self._is_browser_connected():
                        print("⚠️ Browser disconnected during scrolling")
                        break
                        
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_panel)
                    time.sleep(2)
                    print(f"📜 Scrolling... ({i+1}/5)")
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
            time.sleep(2)
            
            business_data = {
                'name': '',
                'phone': '',
                'address': '',
                'website': '',
                'description': '',
                'url': business_url
            }
            
            # Extract business name
            try:
                name_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
                business_data['name'] = name_element.text.strip()
            except:
                print("⚠️ Could not find business name")
            
            # Extract phone number
            try:
                phone_element = self.driver.find_element(By.CSS_SELECTOR, "[data-item-id*='phone']")
                business_data['phone'] = phone_element.text.strip()
            except:
                # Alternative phone selector
                try:
                    phone_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '(') and contains(text(), ')')]")
                    for element in phone_elements:
                        text = element.text.strip()
                        if re.search(r'\(\d{3}\)\s?\d{3}-?\d{4}', text):
                            business_data['phone'] = text
                            break
                except:
                    pass
            
            # Extract address
            try:
                address_element = self.driver.find_element(By.CSS_SELECTOR, "[data-item-id*='address']")
                business_data['address'] = address_element.text.strip()
            except:
                print("⚠️ Could not find address")
            
            # Extract website
            try:
                website_element = self.driver.find_element(By.CSS_SELECTOR, "[data-item-id*='authority']")
                business_data['website'] = website_element.text.strip()
            except:
                # Alternative website selector
                try:
                    website_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'google.com'))]")
                    for link in website_links:
                        href = link.get_attribute('href')
                        if self._is_website_link(href):
                            business_data['website'] = href
                            break
                except:
                    pass
            
            # Extract description/overview
            try:
                description_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='review'] span, [class*='description'] span")
                descriptions = []
                for element in description_elements:
                    text = element.text.strip()
                    if len(text) > 20:  # Only include substantial text
                        descriptions.append(text)
                
                business_data['description'] = ' '.join(descriptions[:3])  # Take first 3 substantial descriptions
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
                
                # Add delay between requests to be respectful
                time.sleep(1)
            
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
            print("🔒 Browser closed")


# Example usage and testing
if __name__ == "__main__":
    # Test the scraper
    scraper = GoogleMapsScraper(headless=False)
    
    try:
        # Test search
        businesses = scraper.scrape_businesses("tattoo shops", "Nashville", max_businesses=5)
        
        # Print results
        for i, business in enumerate(businesses, 1):
            print(f"\n--- Business {i} ---")
            for key, value in business.items():
                print(f"{key}: {value}")
                
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        scraper.close() 