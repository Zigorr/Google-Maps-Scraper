#!/usr/bin/env python3
"""
Google Maps Lead Scraper - Integrated Solution
Combines web scraping with intelligent filtering to find qualified business leads.
"""

import time
from typing import List, Dict
from scraper import GoogleMapsScraper
from data_filter import BusinessFilter


class LeadScraper:
    """
    Complete lead generation solution that scrapes Google Maps and filters for qualified leads.
    """
    
    def __init__(self, headless: bool = False, progress_callback=None):
        """
        Initialize the lead scraper.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            progress_callback: Optional callback function for progress updates
        """
        self.progress_callback = progress_callback
        if self.progress_callback:
            self.progress_callback("Initializing browser...")
        
        self.scraper = GoogleMapsScraper(headless=headless)
        self.filter = BusinessFilter()
        
        if self.progress_callback:
            self.progress_callback("Browser ready!")
        
    def find_leads(self, keyword: str, city: str, max_businesses: int = 50) -> Dict:
        """
        Complete lead finding workflow: scrape, filter, and return qualified leads.
        
        Args:
            keyword (str): Business type to search for (e.g., "tattoo shops")
            city (str): City to search in (e.g., "Nashville")
            max_businesses (int): Maximum number of businesses to scrape
            
        Returns:
            Dict: Complete results with qualified leads and analysis
        """
        print(f"🎯 LEAD GENERATION STARTED")
        print(f"🔍 Target: {keyword} in {city}")
        print(f"📊 Max businesses: {max_businesses}")
        print("=" * 60)
        
        try:
            # Step 1: Scrape businesses from Google Maps
            print("\n🚀 PHASE 1: Scraping Google Maps...")
            raw_businesses = self.scraper.scrape_businesses(keyword, city, max_businesses)
            
            if not raw_businesses:
                print("❌ No businesses found during scraping")
                return self._empty_result()
            
            print(f"✅ Successfully scraped {len(raw_businesses)} businesses")
            
            # Step 2: Filter for qualified leads
            print(f"\n🎯 PHASE 2: Analyzing for qualified leads...")
            filter_results = self.filter.filter_businesses(raw_businesses)
            
            # Step 3: Prepare final results
            results = {
                'keyword': keyword,
                'city': city,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_businesses': raw_businesses,
                'qualified_leads': filter_results['qualified_leads'],
                'statistics': filter_results['statistics'],
                'total_scraped': len(raw_businesses),
                'total_qualified': filter_results['qualified_count'],
                'qualification_rate': filter_results['qualification_rate']
            }
            
            # Print summary
            self._print_summary(results)
            
            return results
            
        except Exception as e:
            print(f"❌ Lead generation failed: {e}")
            return self._empty_result()
    
    def find_leads_detailed(self, keyword: str, city: str, max_businesses: int = 50) -> Dict:
        """
        Extended lead finding with detailed analysis of all businesses.
        
        Args:
            keyword (str): Business type to search for
            city (str): City to search in  
            max_businesses (int): Maximum number of businesses to scrape
            
        Returns:
            Dict: Complete results including detailed analysis of all businesses
        """
        results = self.find_leads(keyword, city, max_businesses)
        
        if results['total_scraped'] > 0:
            # Add detailed analysis
            filter_results = self.filter.filter_businesses(results['raw_businesses'])
            results['all_business_analysis'] = filter_results['all_analysis']
            results['detailed_statistics'] = filter_results['statistics']
        
        return results
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'keyword': '',
            'city': '',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_businesses': [],
            'qualified_leads': [],
            'statistics': {},
            'total_scraped': 0,
            'total_qualified': 0,
            'qualification_rate': 0.0
        }
    
    def _print_summary(self, results: Dict):
        """Print a summary of the lead generation results."""
        print("\n" + "=" * 60)
        print("🎯 LEAD GENERATION COMPLETE")
        print("=" * 60)
        
        print(f"📍 Search: {results['keyword']} in {results['city']}")
        print(f"⏰ Completed: {results['timestamp']}")
        print(f"📊 Total Businesses Scraped: {results['total_scraped']}")
        print(f"✅ Qualified Leads Found: {results['total_qualified']}")
        print(f"📈 Qualification Rate: {results['qualification_rate']:.1f}%")
        
        if results['qualified_leads']:
            print(f"\n🎯 QUALIFIED LEADS:")
            for i, lead in enumerate(results['qualified_leads'], 1):
                print(f"\n--- Lead {i} ---")
                print(f"📛 Name: {lead['business_name']}")
                print(f"📞 Phone: {lead['phone']}")
                print(f"📍 Address: {lead['address']}")
                print(f"🏷️ Reason: {lead['qualification_reason']}")
                
                # Show what was found
                found_items = []
                if lead.get('instagram_found'):
                    found_items.append(f"Instagram (@{lead.get('instagram_handle', 'found')})")
                if lead.get('squarespace_found'):
                    found_items.append("Squarespace booking")
                if lead.get('booksy_found'):
                    found_items.append("Booksy booking")
                
                if found_items:
                    print(f"🔗 Found: {', '.join(found_items)}")
                
                # Show notes if available
                if lead.get('notes'):
                    print(f"📝 Notes: {lead['notes']}")
        
        # Print statistics
        stats = results['statistics']
        if stats:
            print(f"\n📊 ANALYSIS BREAKDOWN:")
            print(f"🌐 Website Types:")
            for website_type, count in stats['website_types'].items():
                print(f"   • {website_type}: {count}")
            
            print(f"\n📱 Platform Usage:")
            print(f"   • Instagram: {stats.get('instagram_count', 0)}")
            print(f"   • Squarespace: {stats.get('squarespace_count', 0)}")
            print(f"   • Booksy: {stats.get('booksy_count', 0)}")
            print(f"   • No online presence: {stats.get('no_presence_count', 0)}")
    
    def close(self):
        """Clean up resources."""
        if self.scraper:
            self.scraper.close() 