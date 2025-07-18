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
        Comprehensive business analysis matching client requirements.
        Looks for Instagram links, Squarespace/Booksy booking, and determines lead qualification.
        """
        name = business_data.get('name', '')
        phone = business_data.get('phone', '')
        address = business_data.get('address', '')
        website = business_data.get('website', '')
        website_type = business_data.get('website_type', 'none')
        description = business_data.get('description', '')
        
        # Initialize analysis structure
        analysis = {
            'business_name': name,
            'phone': phone,
            'address': address,
            'original_website': website,
            'url': business_data.get('url', ''),
            'website_type': website_type,
            'is_qualified_lead': False,
            'qualification_reason': '',
            'instagram_found': False,
            'instagram_handle': '',
            'squarespace_found': False,
            'squarespace_link': '',
            'booksy_found': False,
            'booksy_link': '',
            'notes': ''
        }
        
        # Step 1: Check if business has a real website (auto-disqualify)
        if website_type == 'real_website':
            analysis['qualification_reason'] = "Has established website"
            analysis['notes'] = "Business has a dedicated website"
            return analysis
        
        # Step 2: Look for Instagram links in description
        instagram_info = self._find_instagram_links(description)
        if instagram_info['found']:
            analysis['instagram_found'] = True
            analysis['instagram_handle'] = instagram_info['handle']
            analysis['notes'] += f"Instagram: @{instagram_info['handle']}. "
        
        # Step 3: Look for Squarespace booking links
        squarespace_info = self._find_squarespace_links(description, website)
        if squarespace_info['found']:
            analysis['squarespace_found'] = True
            analysis['squarespace_link'] = squarespace_info['link']
            analysis['notes'] += f"Squarespace booking: {squarespace_info['link']}. "
        
        # Step 4: Look for Booksy booking links
        booksy_info = self._find_booksy_links(description, website)
        if booksy_info['found']:
            analysis['booksy_found'] = True
            analysis['booksy_link'] = booksy_info['link']
            analysis['notes'] += f"Booksy booking: {booksy_info['link']}. "
        
        # Step 5: Check for Facebook/Instagram website
        if website_type in ['instagram', 'facebook']:
            if website_type == 'instagram':
                analysis['instagram_found'] = True
                analysis['notes'] += f"Instagram website: {website}. "
            analysis['notes'] += f"Uses {website_type.capitalize()} as website. "
        
        # Step 6: Determine qualification based on client criteria
        has_instagram = analysis['instagram_found']
        has_squarespace = analysis['squarespace_found']
        has_booksy = analysis['booksy_found']
        has_social_website = website_type in ['instagram', 'facebook']
        has_no_website = website_type in ['none', 'N/A'] or not website or website == 'N/A'
        
        # Client's filtering logic: Include ONLY businesses that:
        # ✅ Have an Instagram link
        # ✅ Have a Squarespace booking link
        # ✅ Have a Booksy link
        # ✅ Have nothing listed at all (no website or link — just phone/address)
        if has_instagram or has_squarespace or has_booksy or has_social_website or has_no_website:
            analysis['is_qualified_lead'] = True
            
            # Set qualification reason
            reasons = []
            if has_instagram:
                reasons.append("Instagram found")
            if has_squarespace:
                reasons.append("Squarespace booking")
            if has_booksy:
                reasons.append("Booksy booking")
            if has_social_website:
                reasons.append(f"Uses {website_type.capitalize()}")
            if has_no_website and not (has_instagram or has_squarespace or has_booksy or has_social_website):
                reasons.append("No online presence")
            
            analysis['qualification_reason'] = f"No online presence - prime candidate ({', '.join(reasons)})"
            
            # Add notes about what makes them a good lead
            if has_no_website and not (has_instagram or has_squarespace or has_booksy or has_social_website):
                analysis['notes'] += "Business has only phone/address listing. "
        else:
            analysis['qualification_reason'] = "Has established website"
            analysis['notes'] = "Business has a dedicated website"
        
        return analysis
    
    def _find_instagram_links(self, description: str) -> Dict:
        """Find Instagram handles in business description."""
        if not description:
            return {'found': False, 'handle': ''}
        
        # Try each Instagram pattern
        for pattern in self.instagram_patterns:
            match = pattern.search(description)
            if match:
                handle = match.group(1)
                # Validate handle (basic check)
                if len(handle) >= 3 and handle.replace('_', '').replace('.', '').isalnum():
                    return {'found': True, 'handle': handle}
        
        return {'found': False, 'handle': ''}
    
    def _find_squarespace_links(self, description: str, website: str) -> Dict:
        """Find Squarespace booking links."""
        # Check website first
        if website and any(domain in website.lower() for domain in self.booking_platforms['squarespace']):
            return {'found': True, 'link': website}
        
        # Check description for Squarespace keywords
        if description:
            desc_lower = description.lower()
            for keyword in self.booking_keywords['squarespace']:
                if keyword in desc_lower:
                    return {'found': True, 'link': f"Squarespace booking mentioned in description"}
        
        return {'found': False, 'link': ''}
    
    def _find_booksy_links(self, description: str, website: str) -> Dict:
        """Find Booksy booking links."""
        # Check website first
        if website and any(domain in website.lower() for domain in self.booking_platforms['booksy']):
            return {'found': True, 'link': website}
        
        # Check description for Booksy keywords
        if description:
            desc_lower = description.lower()
            for keyword in self.booking_keywords['booksy']:
                if keyword in desc_lower:
                    return {'found': True, 'link': f"Booksy booking mentioned in description"}
        
        return {'found': False, 'link': ''}
    
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