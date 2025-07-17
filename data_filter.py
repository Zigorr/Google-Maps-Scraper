import re
from typing import List, Dict, Optional
from urllib.parse import urlparse


class BusinessFilter:
    """
    Intelligent business filtering system for lead qualification.
    Identifies businesses without established websites that are ideal for outreach.
    """
    
    def __init__(self):
        # Define social media and booking platform domains
        self.social_domains = [
            'instagram.com', 'facebook.com', 'twitter.com', 'tiktok.com',
            'linkedin.com', 'youtube.com', 'snapchat.com', 'pinterest.com'
        ]
        
        self.booking_platforms = {
            'squarespace': ['squarespace.com', 'static1.squarespace.com', 'squareup.com'],
            'booksy': ['booksy.com', 'booksy.biz'],
            'acuity': ['acuityscheduling.com'],
            'schedulicity': ['schedulicity.com'],
            'vagaro': ['vagaro.com'],
            'styleseat': ['styleseat.com']
        }
        
        # Google/Maps domains to exclude
        self.google_domains = [
            'google.com', 'maps.google.com', 'googleusercontent.com',
            'gstatic.com', 'googleapis.com'
        ]
    
    def analyze_business(self, business_data: Dict) -> Dict:
        """
        Analyze a single business and determine if it's a qualified lead.
        
        Args:
            business_data (Dict): Business information from scraper
            
        Returns:
            Dict: Analysis results with qualification status
        """
        analysis = {
            'business_name': business_data.get('name', ''),
            'phone': business_data.get('phone', ''),
            'address': business_data.get('address', ''),
            'original_website': business_data.get('website', ''),
            'description': business_data.get('description', ''),
            'url': business_data.get('url', ''),
            
            # Analysis fields
            'has_real_website': False,
            'website_type': 'none',
            'instagram_found': False,
            'instagram_links': [],
            'squarespace_found': False,
            'squarespace_links': [],
            'booksy_found': False,
            'booksy_links': [],
            'other_booking_found': False,
            'other_booking_links': [],
            'is_qualified_lead': False,
            'qualification_reason': '',
            'notes': ''
        }
        
        # Analyze website presence
        website_analysis = self._analyze_website(business_data.get('website', ''))
        analysis.update(website_analysis)
        
        # Analyze description for social media and booking links
        description_analysis = self._analyze_description(business_data.get('description', ''))
        analysis.update(description_analysis)
        
        # Determine if this is a qualified lead
        qualification = self._determine_qualification(analysis)
        analysis.update(qualification)
        
        return analysis
    
    def _analyze_website(self, website: str) -> Dict:
        """Analyze the website field to determine type and legitimacy."""
        result = {
            'has_real_website': False,
            'website_type': 'none',
            'instagram_found': False,
            'instagram_links': [],
            'squarespace_found': False,
            'squarespace_links': [],
            'booksy_found': False,
            'booksy_links': [],
            'other_booking_found': False,
            'other_booking_links': []
        }
        
        if not website or website.strip() == '':
            result['website_type'] = 'none'
            return result
        
        # Clean and normalize the website URL
        website = website.strip().lower()
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            domain = urlparse(website).netloc.lower()
            domain = domain.replace('www.', '')
        except:
            return result
        
        # Check if it's a Google/Maps domain (ignore these)
        if any(google_domain in domain for google_domain in self.google_domains):
            result['website_type'] = 'google'
            return result
        
        # Check for Instagram
        if 'instagram.com' in domain:
            result['website_type'] = 'instagram'
            result['instagram_found'] = True
            result['instagram_links'].append(website)
            return result
        
        # Check for other social media
        if any(social_domain in domain for social_domain in self.social_domains):
            result['website_type'] = 'social_media'
            return result
        
        # Check for booking platforms
        for platform, domains in self.booking_platforms.items():
            if any(booking_domain in domain for booking_domain in domains):
                result['website_type'] = f'{platform}_booking'
                if platform == 'squarespace':
                    result['squarespace_found'] = True
                    result['squarespace_links'].append(website)
                elif platform == 'booksy':
                    result['booksy_found'] = True
                    result['booksy_links'].append(website)
                else:
                    result['other_booking_found'] = True
                    result['other_booking_links'].append(website)
                return result
        
        # If we get here, it's likely a real website
        result['has_real_website'] = True
        result['website_type'] = 'real_website'
        
        return result
    
    def _analyze_description(self, description: str) -> Dict:
        """Analyze business description for social media and booking links."""
        result = {
            'instagram_found': False,
            'instagram_links': [],
            'squarespace_found': False,
            'squarespace_links': [],
            'booksy_found': False,
            'booksy_links': [],
            'other_booking_found': False,
            'other_booking_links': []
        }
        
        if not description:
            return result
        
        description = description.lower()
        
        # Look for Instagram mentions
        instagram_patterns = [
            r'@([a-zA-Z0-9_.]+)',  # @username
            r'instagram\.com/([a-zA-Z0-9_.]+)',  # instagram.com/username
            r'ig:?\s*([a-zA-Z0-9_.]+)',  # IG: username or ig username
            r'follow.*?@([a-zA-Z0-9_.]+)',  # follow us @username
        ]
        
        for pattern in instagram_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                result['instagram_found'] = True
                for match in matches:
                    if match and len(match) > 2:  # Valid username length
                        result['instagram_links'].append(f"instagram.com/{match}")
        
        # Look for Squarespace mentions
        if any(term in description for term in ['squarespace', 'square space', 'book online']):
            result['squarespace_found'] = True
            # Try to extract actual Squarespace links
            squarespace_matches = re.findall(r'([\w.-]+\.squarespace\.com)', description)
            result['squarespace_links'].extend(squarespace_matches)
        
        # Look for Booksy mentions
        if any(term in description for term in ['booksy', 'book with booksy']):
            result['booksy_found'] = True
            booksy_matches = re.findall(r'(booksy\.com/[\w/.-]+)', description)
            result['booksy_links'].extend(booksy_matches)
        
        # Look for other booking platform mentions
        booking_keywords = ['book appointment', 'schedule online', 'online booking', 'appointment booking']
        if any(keyword in description for keyword in booking_keywords):
            result['other_booking_found'] = True
        
        return result
    
    def _determine_qualification(self, analysis: Dict) -> Dict:
        """Determine if this business is a qualified lead based on analysis."""
        result = {
            'is_qualified_lead': False,
            'qualification_reason': '',
            'notes': ''
        }
        
        # Disqualify if they have a real website
        if analysis['has_real_website']:
            result['qualification_reason'] = 'Has established website'
            result['notes'] = f"Real website found: {analysis['original_website']}"
            return result
        
        # Disqualify if it's just social media (but not Instagram-only businesses)
        if analysis['website_type'] in ['social_media'] and not analysis['instagram_found']:
            result['qualification_reason'] = 'Uses social media platform (non-Instagram)'
            return result
        
        # QUALIFY: No website at all
        if analysis['website_type'] == 'none' and not analysis['instagram_found']:
            result['is_qualified_lead'] = True
            result['qualification_reason'] = 'No online presence - prime candidate'
            result['notes'] = 'Business has only phone/address listing'
            return result
        
        # QUALIFY: Instagram-only presence
        if analysis['instagram_found'] and not analysis['has_real_website']:
            result['is_qualified_lead'] = True
            result['qualification_reason'] = 'Instagram-only presence'
            instagram_links = analysis['instagram_links']
            if instagram_links:
                result['notes'] = f"Instagram: {', '.join(instagram_links[:2])}"
            return result
        
        # QUALIFY: Uses booking platforms instead of real website
        if analysis['squarespace_found'] or analysis['booksy_found'] or analysis['other_booking_found']:
            result['is_qualified_lead'] = True
            result['qualification_reason'] = 'Uses booking platform instead of website'
            
            notes = []
            if analysis['squarespace_found']:
                notes.append('Squarespace booking')
            if analysis['booksy_found']:
                notes.append('Booksy booking')
            if analysis['other_booking_found']:
                notes.append('Other booking platform')
            result['notes'] = ', '.join(notes)
            return result
        
        # Default: Not qualified
        result['qualification_reason'] = 'Has sufficient online presence'
        return result
    
    def filter_businesses(self, businesses: List[Dict]) -> Dict:
        """
        Filter a list of businesses and return qualified leads.
        
        Args:
            businesses (List[Dict]): List of business data from scraper
            
        Returns:
            Dict: Filtered results with qualified leads and statistics
        """
        qualified_leads = []
        all_analysis = []
        
        print(f"🔍 Analyzing {len(businesses)} businesses for lead qualification...")
        
        for i, business in enumerate(businesses, 1):
            analysis = self.analyze_business(business)
            all_analysis.append(analysis)
            
            if analysis['is_qualified_lead']:
                qualified_leads.append(analysis)
                print(f"✅ Lead {len(qualified_leads)}: {analysis['business_name']} - {analysis['qualification_reason']}")
            else:
                print(f"❌ Skip: {analysis['business_name']} - {analysis['qualification_reason']}")
        
        # Generate statistics
        stats = self._generate_statistics(all_analysis)
        
        result = {
            'qualified_leads': qualified_leads,
            'all_analysis': all_analysis,
            'statistics': stats,
            'total_businesses': len(businesses),
            'qualified_count': len(qualified_leads),
            'qualification_rate': (len(qualified_leads) / len(businesses) * 100) if businesses else 0
        }
        
        print(f"\n📊 FILTERING COMPLETE:")
        print(f"📈 Total Businesses: {result['total_businesses']}")
        print(f"🎯 Qualified Leads: {result['qualified_count']}")
        print(f"📋 Qualification Rate: {result['qualification_rate']:.1f}%")
        
        return result
    
    def _generate_statistics(self, all_analysis: List[Dict]) -> Dict:
        """Generate statistics about the business analysis."""
        stats = {
            'website_types': {},
            'qualification_reasons': {},
            'instagram_count': 0,
            'squarespace_count': 0,
            'booksy_count': 0,
            'no_presence_count': 0
        }
        
        for analysis in all_analysis:
            # Count website types
            website_type = analysis['website_type']
            stats['website_types'][website_type] = stats['website_types'].get(website_type, 0) + 1
            
            # Count qualification reasons
            reason = analysis['qualification_reason']
            stats['qualification_reasons'][reason] = stats['qualification_reasons'].get(reason, 0) + 1
            
            # Count specific platforms
            if analysis['instagram_found']:
                stats['instagram_count'] += 1
            if analysis['squarespace_found']:
                stats['squarespace_count'] += 1
            if analysis['booksy_found']:
                stats['booksy_count'] += 1
            if analysis['website_type'] == 'none':
                stats['no_presence_count'] += 1
        
        return stats


# Testing function
def test_filter():
    """Test the BusinessFilter with sample data."""
    # Sample business data (based on our Nashville tattoo shop results)
    sample_businesses = [
        {
            'name': 'Circa Tattoo',
            'phone': '',
            'address': '2605 8th Ave S, Nashville, TN 37204',
            'website': 'circatattoos.com',
            'description': '',
            'url': 'https://maps.google.com/test1'
        },
        {
            'name': 'Instagram Only Tattoo',
            'phone': '+1 615-555-0123',
            'address': '123 Music Row, Nashville, TN 37203',
            'website': 'instagram.com/instagramonlytattoo',
            'description': 'Follow us @instagramonlytattoo for latest work',
            'url': 'https://maps.google.com/test2'
        },
        {
            'name': 'No Website Tattoo',
            'phone': '+1 615-555-0124',
            'address': '456 Broadway, Nashville, TN 37203',
            'website': '',
            'description': 'Call for appointments',
            'url': 'https://maps.google.com/test3'
        },
        {
            'name': 'Booksy Booking Tattoo',
            'phone': '+1 615-555-0125',
            'address': '789 Main St, Nashville, TN 37203',
            'website': '',
            'description': 'Book online with Booksy or call us directly',
            'url': 'https://maps.google.com/test4'
        },
        {
            'name': 'Squarespace Booking Shop',
            'phone': '+1 615-555-0126',
            'address': '321 Art St, Nashville, TN 37203',
            'website': 'mybooking.squarespace.com',
            'description': 'Online booking available',
            'url': 'https://maps.google.com/test5'
        }
    ]
    
    # Test the filter
    filter_engine = BusinessFilter()
    results = filter_engine.filter_businesses(sample_businesses)
    
    print(f"\n🧪 TEST RESULTS:")
    print(f"Should have 4 qualified leads (all except 'Circa Tattoo')")
    print(f"Actual qualified leads: {results['qualified_count']}")
    
    for lead in results['qualified_leads']:
        print(f"✅ {lead['business_name']}: {lead['qualification_reason']}")


if __name__ == "__main__":
    # Uncomment the line below to run tests
    # test_filter()
    pass 