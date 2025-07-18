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
        """
        website_type = business_data.get('website_type', 'none')
        website = business_data.get('website', '')

        analysis = {
            'business_name': business_data.get('name', ''),
            'phone': business_data.get('phone', ''),
            'address': business_data.get('address', ''),
            'original_website': website,
            'url': business_data.get('url', ''),
            'website_type': website_type,
            'is_qualified_lead': False,
            'qualification_reason': ''
        }
        
        # Qualification logic based on pre-classified website type
        if website_type in ['instagram', 'facebook', 'booksy', 'squarespace']:
            analysis['is_qualified_lead'] = True
            analysis['qualification_reason'] = f"Uses {website_type.capitalize()} instead of a dedicated website."
        elif website_type == 'none' or not website:
            analysis['is_qualified_lead'] = True
            analysis['qualification_reason'] = "No website found."
        elif website_type == 'real_website':
            analysis['qualification_reason'] = "Has established website."
        else:
            analysis['qualification_reason'] = "Website classification is not a direct lead source."

        return analysis
    
    def filter_businesses(self, businesses: List[Dict]) -> Dict:
        """
        Filters a list of businesses to find qualified leads and generates statistics.
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
                if analysis['website_type'] in ['instagram', 'facebook']:
                    platforms.append("Social Media")
                elif analysis['website_type'] in ['booksy', 'squarespace']:
                    platforms.append("Booking Platform")
                
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
            if analysis['website_type'] in ['instagram', 'facebook']:
                stats['instagram_count'] += 1
            elif analysis['website_type'] in ['booksy', 'squarespace']:
                stats['squarespace_count'] += 1
            elif analysis['website_type'] == 'real_website':
                stats['no_presence_count'] += 1
        
        return stats 