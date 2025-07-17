import re
from typing import List, Dict, Optional
from urllib.parse import urlparse


class BusinessFilter:
    """
    Optimized business filtering system for lead qualification.
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
        
        # Compiled regex patterns for better performance
        self.instagram_patterns = [
            re.compile(r'@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'ig:?\s*([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'follow.*?@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'insta:?\s*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'check.*?@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'find.*?@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'visit.*?@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'see.*?@([a-zA-Z0-9_.]+)', re.IGNORECASE),
            re.compile(r'on instagram:?\s*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
        ]
        
        # Compiled phone pattern
        self.phone_pattern = re.compile(r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        
        # Booking keywords for faster matching
        self.booking_keywords = {
            'squarespace': ['squarespace', 'square space', 'book online'],
            'booksy': ['booksy', 'book with booksy'],
            'general': ['book appointment', 'schedule online', 'online booking', 'appointment booking']
        }
    
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
        # Merge description analysis with website analysis
        for key in ['instagram_found', 'squarespace_found', 'booksy_found']:
            if description_analysis.get(key, False):
                analysis[key] = True
        for key in ['instagram_links', 'squarespace_links', 'booksy_links']:
            analysis[key].extend(description_analysis.get(key, []))
        
        # Add comprehensive Instagram detection across all fields
        instagram_analysis = self._comprehensive_instagram_detection(business_data)
        if instagram_analysis['instagram_found']:
            analysis['instagram_found'] = True
            analysis['instagram_links'].extend(instagram_analysis['instagram_links'])
        
        # Enhanced Squarespace detection
        squarespace_analysis = self._comprehensive_squarespace_detection(business_data)
        if squarespace_analysis['squarespace_found']:
            analysis['squarespace_found'] = True
            analysis['squarespace_links'].extend(squarespace_analysis['squarespace_links'])
        
        # Enhanced Booksy detection
        booksy_analysis = self._comprehensive_booksy_detection(business_data)
        if booksy_analysis['booksy_found']:
            analysis['booksy_found'] = True
            analysis['booksy_links'].extend(booksy_analysis['booksy_links'])
        
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
        
        # Check for Instagram (comprehensive detection)
        instagram_indicators = [
            'instagram.com',
            'instagr.am',
            'ig.me'
        ]
        
        if any(indicator in domain for indicator in instagram_indicators):
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
        
        # Look for Instagram mentions with comprehensive patterns
        for pattern in self.instagram_patterns:
            matches = pattern.findall(description)
            if matches:
                result['instagram_found'] = True
                for match in matches:
                    if match and len(match) > 2:  # Valid username length
                        result['instagram_links'].append(f"instagram.com/{match}")
        
        # Look for Squarespace mentions
        if any(term in description for term in self.booking_keywords['squarespace']):
            result['squarespace_found'] = True
            # Try to extract actual Squarespace links
            squarespace_matches = re.findall(r'([\w.-]+\.squarespace\.com)', description)
            result['squarespace_links'].extend(squarespace_matches)
        
        # Look for Booksy mentions
        if any(term in description for term in self.booking_keywords['booksy']):
            result['booksy_found'] = True
            booksy_matches = re.findall(r'(booksy\.com/[\w/.-]+)', description)
            result['booksy_links'].extend(booksy_matches)
        
        # Look for other booking platform mentions
        if any(keyword in description for keyword in self.booking_keywords['general']):
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
    
    def _comprehensive_instagram_detection(self, business: Dict) -> Dict:
        """
        Comprehensive Instagram detection across all business data fields.
        
        Args:
            business (Dict): Business data dictionary
            
        Returns:
            Dict: Instagram detection results
        """
        result = {
            'instagram_found': False,
            'instagram_links': [],
            'instagram_handles': []
        }
        
        # Check all fields for Instagram presence
        fields_to_check = [
            ('website', business.get('website', '')),
            ('description', business.get('description', '')),
            ('name', business.get('name', '')),
            ('address', business.get('address', ''))
        ]
        
        for field_name, field_value in fields_to_check:
            if not field_value:
                continue
                
            field_value = str(field_value).lower()
            
            # Direct Instagram URL detection
            if 'instagram.com' in field_value or 'instagr.am' in field_value:
                result['instagram_found'] = True
                result['instagram_links'].append(field_value)
                
                # Extract username from URL
                username_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', field_value)
                if username_match:
                    result['instagram_handles'].append(username_match.group(1))
            
            # Instagram handle detection with comprehensive patterns
            for pattern in self.instagram_patterns:
                matches = pattern.findall(field_value)
                if matches:
                    result['instagram_found'] = True
                    for match in matches:
                        if match not in result['instagram_handles']:
                            result['instagram_handles'].append(match)
        
        return result

    def _comprehensive_squarespace_detection(self, business: Dict) -> Dict:
        """
        Comprehensive Squarespace detection across all business data fields.
        
        Args:
            business (Dict): Business data dictionary
            
        Returns:
            Dict: Squarespace detection results
        """
        result = {
            'squarespace_found': False,
            'squarespace_links': []
        }
        
        # Check all fields for Squarespace presence
        fields_to_check = [
            ('website', business.get('website', '')),
            ('description', business.get('description', '')),
            ('name', business.get('name', '')),
            ('address', business.get('address', ''))
        ]
        
        for field_name, field_value in fields_to_check:
            if not field_value:
                continue
                
            field_value = str(field_value).lower()
            
            # Direct Squarespace domain detection
            squarespace_domains = [
                'squarespace.com', 'squarespace.net', 'squarespace.org',
                'squarespace.io', 'squarespace.co', 'squarespace.me',
                'squarespace.app', 'squarespace.dev', 'squarespace.test',
                'squarespace.local', 'static1.squarespace.com'
            ]
            
            for domain in squarespace_domains:
                if domain in field_value:
                    result['squarespace_found'] = True
                    result['squarespace_links'].append(field_value)
                    break
            
            # Text-based Squarespace detection
            squarespace_indicators = [
                'squarespace', 'square space', 'book online', 'online booking',
                'powered by squarespace', 'squarespace.com', 'schedule online',
                'appointment booking', 'book appointment online'
            ]
            
            for indicator in squarespace_indicators:
                if indicator in field_value:
                    result['squarespace_found'] = True
                    break
        
        return result

    def _comprehensive_booksy_detection(self, business: Dict) -> Dict:
        """
        Comprehensive Booksy detection across all business data fields.
        
        Args:
            business (Dict): Business data dictionary
            
        Returns:
            Dict: Booksy detection results
        """
        result = {
            'booksy_found': False,
            'booksy_links': []
        }
        
        # Check all fields for Booksy presence
        fields_to_check = [
            ('website', business.get('website', '')),
            ('description', business.get('description', '')),
            ('name', business.get('name', '')),
            ('address', business.get('address', ''))
        ]
        
        for field_name, field_value in fields_to_check:
            if not field_value:
                continue
                
            field_value = str(field_value).lower()
            
            # Direct Booksy domain detection
            booksy_domains = [
                'booksy.com', 'booksy.biz', 'booksy.net', 'booksy.org',
                'booksy.io', 'booksy.co', 'booksy.me', 'booksy.app'
            ]
            
            for domain in booksy_domains:
                if domain in field_value:
                    result['booksy_found'] = True
                    result['booksy_links'].append(field_value)
                    break
            
            # Text-based Booksy detection
            booksy_indicators = [
                'booksy', 'book with booksy', 'booksy.com', 'booksy app',
                'download booksy', 'book on booksy', 'booksy booking',
                'book appointment', 'schedule appointment', 'book online'
            ]
            
            for indicator in booksy_indicators:
                if indicator in field_value:
                    result['booksy_found'] = True
                    break
        
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
                # Show detected platforms in output
                platforms = []
                if analysis['instagram_found']:
                    platforms.append("IG")
                if analysis['squarespace_found']:
                    platforms.append("Squarespace")
                if analysis['booksy_found']:
                    platforms.append("Booksy")
                
                platform_info = f" ({', '.join(platforms)})" if platforms else ""
                print(f"✅ Lead {len(qualified_leads)}: {analysis['business_name']} - {analysis['qualification_reason']}{platform_info}")
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