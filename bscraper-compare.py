#!/usr/bin/env python3
"""
Banner API Course Schedule Scraper for Northeastern University
Based on reverse-engineered API documentation
Enhanced with file backup and comparison features
"""

import requests
import json
import time
import re
import os
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import csv
import logging
import pandas as pd
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CourseSection:
    """Data class to represent a course section"""
    course_reference_number: str
    subject: str
    course_number: str
    title: str
    section: str
    instructor: str
    meeting_times: str  # Keep original for JSON export
    days: str           # New field for CSV
    time: str           # New field for CSV
    campus: str         # New field for CSV
    classroom: str      # New field for CSV
    enrollment_info: Dict
    credit_hour_low: str
    credit_hour_high: str
    credits_formatted: str
    instructional_method: str

@dataclass
class CourseComparison:
    """Data class to represent changes between course versions"""
    added_courses: List[Dict]
    removed_courses: List[Dict]
    time_location_changes: List[Dict]
    enrollment_changes: List[Dict]

class FileManager:
    """Handles file operations including backup and comparison"""
    
    @staticmethod
    def backup_existing_file(filename: str) -> bool:
        """
        Backup existing file by renaming it with _OLD suffix
        Returns True if backup was created, False if no existing file
        """
        if os.path.exists(filename):
            base_name, ext = os.path.splitext(filename)
            backup_name = f"{base_name}_OLD{ext}"
            
            # If backup already exists, remove it first
            if os.path.exists(backup_name):
                os.remove(backup_name)
                logger.info(f"Removed existing backup: {backup_name}")
            
            # Create new backup
            shutil.move(filename, backup_name)
            logger.info(f"Backed up existing file: {filename} -> {backup_name}")
            return True
        return False
    
    @staticmethod
    def compare_course_files(old_file: str, new_file: str) -> CourseComparison:
        """
        Compare two CSV course files and return changes
        """
        if not os.path.exists(old_file):
            logger.warning(f"Old file {old_file} does not exist, cannot compare")
            return CourseComparison([], [], [], [])
        
        try:
            # Read both files
            old_df = pd.read_csv(old_file)
            new_df = pd.read_csv(new_file)
            
            # Create unique identifiers for courses (CRN is the primary key)
            old_courses = {row['CRN']: row.to_dict() for _, row in old_df.iterrows()}
            new_courses = {row['CRN']: row.to_dict() for _, row in new_df.iterrows()}
            
            # Find added and removed courses
            old_crns = set(old_courses.keys())
            new_crns = set(new_courses.keys())
            
            added_crns = new_crns - old_crns
            removed_crns = old_crns - new_crns
            common_crns = old_crns & new_crns
            
            added_courses = [new_courses[crn] for crn in added_crns]
            removed_courses = [old_courses[crn] for crn in removed_crns]
            
            # Find time/location and enrollment changes
            time_location_changes = []
            enrollment_changes = []
            
            for crn in common_crns:
                old_course = old_courses[crn]
                new_course = new_courses[crn]
                
                # Check for time/location changes
                time_location_fields = ['Days', 'Time', 'Campus', 'Classroom']
                time_location_changed = False
                changes = {}
                
                for field in time_location_fields:
                    old_val = str(old_course.get(field, 'N/A')).strip()
                    new_val = str(new_course.get(field, 'N/A')).strip()
                    if old_val != new_val:
                        time_location_changed = True
                        changes[field] = {'old': old_val, 'new': new_val}
                
                if time_location_changed:
                    change_record = {
                        'CRN': crn,
                        'Subject': new_course.get('Subject', ''),
                        'Course Number': new_course.get('Course Number', ''),
                        'Title': new_course.get('Title', ''),
                        'Section': new_course.get('Section', ''),
                        'changes': changes
                    }
                    time_location_changes.append(change_record)
                
                # Check for enrollment changes
                enrollment_fields = ['Enrollment Actual', 'Enrollment Maximum']
                enrollment_changed = False
                enroll_changes = {}
                
                for field in enrollment_fields:
                    old_val = str(old_course.get(field, 'N/A')).strip()
                    new_val = str(new_course.get(field, 'N/A')).strip()
                    if old_val != new_val and old_val != 'N/A' and new_val != 'N/A':
                        enrollment_changed = True
                        enroll_changes[field] = {'old': old_val, 'new': new_val}
                
                if enrollment_changed:
                    change_record = {
                        'CRN': crn,
                        'Subject': new_course.get('Subject', ''),
                        'Course Number': new_course.get('Course Number', ''),
                        'Title': new_course.get('Title', ''),
                        'Section': new_course.get('Section', ''),
                        'changes': enroll_changes
                    }
                    enrollment_changes.append(change_record)
            
            return CourseComparison(
                added_courses=added_courses,
                removed_courses=removed_courses,
                time_location_changes=time_location_changes,
                enrollment_changes=enrollment_changes
            )
            
        except Exception as e:
            logger.error(f"Error comparing files: {e}")
            return CourseComparison([], [], [], [])
    
    @staticmethod
    def print_comparison_report(comparison: CourseComparison):
        """Print a detailed comparison report"""
        print("\n" + "="*80)
        print("COURSE SCHEDULE COMPARISON REPORT")
        print("="*80)
        
        # Added courses
        if comparison.added_courses:
            print(f"\n📚 ADDED COURSES ({len(comparison.added_courses)})")
            print("-" * 40)
            for course in comparison.added_courses:
                print(f"  + {course.get('Subject', '')} {course.get('Course Number', '')} "
                      f"({course.get('Section', '')}) - {course.get('Title', '')}")
                print(f"    CRN: {course.get('CRN', '')}, {course.get('Days', '')} "
                      f"{course.get('Time', '')}, {course.get('Classroom', '')}")
        else:
            print(f"\n📚 ADDED COURSES (0)")
            print("-" * 40)
            print("  No new courses added")
        
        # Removed courses
        if comparison.removed_courses:
            print(f"\n❌ REMOVED COURSES ({len(comparison.removed_courses)})")
            print("-" * 40)
            for course in comparison.removed_courses:
                print(f"  - {course.get('Subject', '')} {course.get('Course Number', '')} "
                      f"({course.get('Section', '')}) - {course.get('Title', '')}")
                print(f"    CRN: {course.get('CRN', '')}")
        else:
            print(f"\n❌ REMOVED COURSES (0)")
            print("-" * 40)
            print("  No courses removed")
        
        # Time/Location changes
        if comparison.time_location_changes:
            print(f"\n🏫 TIME/LOCATION CHANGES ({len(comparison.time_location_changes)})")
            print("-" * 40)
            for course in comparison.time_location_changes:
                print(f"  🔄 {course.get('Subject', '')} {course.get('Course Number', '')} "
                      f"({course.get('Section', '')}) - CRN: {course.get('CRN', '')}")
                for field, change in course['changes'].items():
                    print(f"    {field}: '{change['old']}' → '{change['new']}'")
        else:
            print(f"\n🏫 TIME/LOCATION CHANGES (0)")
            print("-" * 40)
            print("  No time/location changes")
        
        # Enrollment changes
        if comparison.enrollment_changes:
            print(f"\n👥 ENROLLMENT CHANGES ({len(comparison.enrollment_changes)})")
            print("-" * 40)
            for course in comparison.enrollment_changes:
                print(f"  📊 {course.get('Subject', '')} {course.get('Course Number', '')} "
                      f"({course.get('Section', '')}) - CRN: {course.get('CRN', '')}")
                for field, change in course['changes'].items():
                    print(f"    {field}: {change['old']} → {change['new']}")
        else:
            print(f"\n👥 ENROLLMENT CHANGES (0)")
            print("-" * 40)
            print("  No enrollment changes")
        
        # Summary
        total_changes = (len(comparison.added_courses) + len(comparison.removed_courses) + 
                        len(comparison.time_location_changes) + len(comparison.enrollment_changes))
        
        print(f"\n📋 SUMMARY")
        print("-" * 40)
        print(f"  Total changes detected: {total_changes}")
        print(f"  Added courses: {len(comparison.added_courses)}")
        print(f"  Removed courses: {len(comparison.removed_courses)}")
        print(f"  Time/location changes: {len(comparison.time_location_changes)}")
        print(f"  Enrollment changes: {len(comparison.enrollment_changes)}")
        print("="*80)

class BannerScraper:
    """Class to scrape course data from NU Banner API"""
    
    def __init__(self):
        self.base_url = "https://nubanner.neu.edu/StudentRegistrationSsb/ssb"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Initialize session by visiting the main page
        self._initialize_session()
        
    def _initialize_session(self):
        """Initialize session by visiting the main Banner page"""
        try:
            main_url = "https://nubanner.neu.edu/StudentRegistrationSsb/"
            response = self.session.get(main_url)
            response.raise_for_status()
            logger.info("Session initialized successfully")
        except requests.RequestException as e:
            logger.warning(f"Failed to initialize session: {e}")
    
    def get_terms(self, max_terms: int = 5) -> List[Dict]:
        """Get available terms/semesters"""
        url = f"{self.base_url}/classSearch/getTerms"
        params = {
            'offset': 1,
            'max': max_terms,
            'searchTerm': ''
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            terms = response.json()
            logger.info(f"Retrieved {len(terms)} terms")
            return terms
        except requests.RequestException as e:
            logger.error(f"Error fetching terms: {e}")
            return []
   
   
    def authorize_session(self, term_code: str) -> bool:
        """Authorize session by declaring term (required before searching)"""
        try:
            # Step 1: Visit the class search page first
            class_search_url = f"{self.base_url}/classSearch/classSearch"
            response = self.session.get(class_search_url)
            response.raise_for_status()
            logger.info("Visited class search page")
            
            # Step 2: Visit the term selection page
            term_selection_url = f"{self.base_url}/term/termSelection?mode=search"
            response = self.session.get(term_selection_url)
            response.raise_for_status()
            logger.info("Visited term selection page")
            
            # Step 3: Submit the term selection
            term_search_url = f"{self.base_url}/term/search"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': term_selection_url
            }
            
            data = {'term': term_code}
            response = self.session.post(term_search_url, data=data, headers=headers)
            response.raise_for_status()
            
            # Check the response
            try:
                result = response.json()
                logger.info(f"Authorization response: {result}")
                
                # Check for success indicators
                if result.get('success', False):
                    logger.info(f"Session authorized for term {term_code}")
                    return True
                elif 'regAllowed' in result:
                    logger.info(f"Session authorized for term {term_code} (regAllowed present)")
                    return True
                elif 'fwdURL' in result:
                    fwd_url = result['fwdURL']
                    logger.info(f"Got forward URL: {fwd_url}")
                    
                    # Handle the forward URL properly
                    if fwd_url and fwd_url != '/StudentRegistrationSsb/ssb/null/null':
                        if not fwd_url.startswith('http'):
                            fwd_url = f"https://nubanner.neu.edu{fwd_url}"
                        
                        # Visit the forward URL
                        response = self.session.get(fwd_url)
                        response.raise_for_status()
                        logger.info(f"Visited forward URL: {fwd_url}")
                        
                        # Try authorization again
                        response = self.session.post(term_search_url, data=data, headers=headers)
                        result = response.json()
                        
                        if result.get('success', False) or 'regAllowed' in result:
                            logger.info(f"Session authorized for term {term_code} after redirect")
                            return True
                    else:
                        # If we get null/null, try going directly to class search
                        logger.info("Got null forward URL, trying direct class search approach")
                        class_search_url = f"{self.base_url}/classSearch/classSearch"
                        response = self.session.get(class_search_url)
                        
                        if response.status_code == 200:
                            logger.info(f"Successfully accessed class search page for term {term_code}")
                            return True
                    
                    logger.error(f"Failed to handle forward URL properly")
                    return False
                else:
                    logger.error(f"Unexpected authorization response: {result}")
                    return False
                    
            except ValueError as e:
                # Not JSON response
                logger.info(f"Got non-JSON response: {response.status_code}")
                if response.status_code == 200:
                    # Sometimes a successful redirect gives HTML instead of JSON
                    logger.info(f"Session likely authorized for term {term_code} (HTML response)")
                    return True
                else:
                    logger.error(f"Unexpected response: {response.text[:200]}")
                    return False
                    
        except requests.RequestException as e:
            logger.error(f"Error during authorization: {e}")
            return False
    
    def search_courses(self, term_code: str, campus: str = 'OAK', page_max_size: int = 100, max_pages: int = 5):
        """Search for courses with pagination support"""
        url = f"{self.base_url}/searchResults/searchResults"
        
        params = {
            'txt_subject': '',
            'txt_courseNumber': '',
            'txt_term': term_code,
            'txt_campus': 'OAK',
            'startDatepicker': '',
            'endDatepicker': '',
            'pageOffset': 0,
            'pageMaxSize': page_max_size,
            'sortColumn': 'subjectDescription',
            'sortDirection': 'asc'
        }
        
        all_courses = []
        page_offset = 0
        page_count = 0
        
        while True:
            params['pageOffset'] = page_offset
            page_count += 1
            
            logger.info(f"Fetching page {page_count} (offset: {page_offset})")
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                
                if result.get('success', False):
                    courses = result.get('data', [])
                    
                    if not courses:
                        logger.info("No more courses found - finished")
                        break
                    
                    all_courses.extend(courses)
                    logger.info(f"Found {len(courses)} courses on this page, total: {len(all_courses)}")
                    
                    # Stop if we've reached max_pages (if specified)
                    if max_pages and page_count >= max_pages:
                        logger.info(f"Reached maximum pages limit ({max_pages})")
                        break
                    
                    # Check if we got fewer courses than requested (indicates last page)
                    if len(courses) < page_max_size:
                        logger.info("Reached last page")
                        break
                    
                    page_offset += page_max_size
                    time.sleep(0.5)  # Rate limiting between pages
                    
                else:
                    logger.error(f"Search failed: {result}")
                    break
                    
            except requests.RequestException as e:
                logger.error(f"Error searching courses: {e}")
                break
        
        logger.info(f"Total courses found: {len(all_courses)}")
        return all_courses

    
    def get_meeting_times(self, term_code: str, course_reference_number: str) -> Dict:
        """Get meeting times and instructor info for a course"""
        url = f"{self.base_url}/searchResults/getFacultyMeetingTimes"
        params = {
            'term': term_code,
            'courseReferenceNumber': course_reference_number
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching meeting times: {e}")
            return {}
            
    def parse_meeting_times_for_csv(self, meeting_data: Dict) -> Dict:
        """Parse meeting times data into separate components for CSV export"""
        if not meeting_data or 'fmt' not in meeting_data:
            return {
                'days': 'TBA',
                'time': 'TBA',
                'campus': 'TBA',
                'classroom': 'TBA'
            }
        
        # Initialize lists to collect data from multiple meetings
        all_days = []
        all_times = []
        all_campuses = []
        all_classrooms = []
        
        for meeting in meeting_data['fmt']:
            meeting_time = meeting.get('meetingTime', {})
            
            # Extract days of the week
            days = self.extract_days_of_week(meeting_time)
            all_days.append(days)
            
            # Extract time range
            begin_time = meeting_time.get('beginTime', '')
            end_time = meeting_time.get('endTime', '')
            if begin_time:
                time_str = begin_time
                if end_time:
                    time_str += f" - {end_time}"
                all_times.append(time_str)
            else:
                all_times.append('TBA')
            
            # Extract campus
            campus = meeting_time.get('campus', '')
            all_campuses.append(campus if campus else 'TBA')
            
            # Extract classroom (building + room)
            building = meeting_time.get('building', '')
            building_description = meeting_time.get('buildingDescription', '')
            room = meeting_time.get('room', '')
            
            # Use building description if available, otherwise fall back to building code
            if building_description:
                building_str = building_description
            elif building:
                building_str = building
            else:
                building_str = ""
            
            if building_str and room:
                classroom = f"{building_str} {room}"
            elif building_str:
                classroom = building_str
            elif room:
                classroom = room
            else:
                classroom = 'TBA'
            
            all_classrooms.append(classroom)
        
        # Combine multiple meetings with semicolon separator
        return {
            'days': '; '.join(filter(lambda x: x != 'TBA', all_days)) or 'TBA',
            'time': '; '.join(filter(lambda x: x != 'TBA', all_times)) or 'TBA',
            'campus': '; '.join(filter(lambda x: x != 'TBA', all_campuses)) or 'TBA',
            'classroom': '; '.join(filter(lambda x: x != 'TBA', all_classrooms)) or 'TBA'
        }

    
    def get_enrollment_info(self, term_code: str, course_reference_number: str) -> Dict:
        """Get enrollment and waitlist information"""
        url = f"{self.base_url}/searchResults/getEnrollmentInfo"
        data = {
            'term': term_code,
            'courseReferenceNumber': course_reference_number
        }
        
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            # Check if response is JSON or HTML
            try:
                json_response = response.json()
                # If it's JSON, it might contain HTML in a field
                if isinstance(json_response, dict):
                    # Look for HTML content in various possible fields
                    html_content = None
                    for key, value in json_response.items():
                        if isinstance(value, str) and '<span' in value:
                            html_content = value
                            break
                    
                    if html_content:
                        return self.parse_enrollment_html(html_content)
                    else:
                        # If no HTML found, return the JSON as-is (might be structured data)
                        return json_response
                else:
                    return {}
            except ValueError:
                # Response is not JSON, treat as HTML
                return self.parse_enrollment_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching enrollment info: {e}")
            return {}

    def parse_enrollment_html(self, html_content: str) -> Dict:
        """Parse enrollment information from HTML content"""
        enrollment_info = {
            'enrollment_actual': 'N/A',
            'enrollment_maximum': 'N/A',
            'enrollment_seats_available': 'N/A',
            'waitlist_capacity': 'N/A',
            'waitlist_actual': 'N/A',
            'waitlist_seats_available': 'N/A'
        }
        
        if not html_content:
            return enrollment_info
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all status-bold spans and their corresponding values
            status_spans = soup.find_all('span', class_='status-bold')
            
            for span in status_spans:
                label = span.get_text(strip=True).lower()
                
                # Find the next span with dir="ltr" which contains the value
                next_span = span.find_next_sibling('span', attrs={'dir': 'ltr'})
                if next_span:
                    value = next_span.get_text(strip=True)
                    
                    # Map labels to our dictionary keys
                    if 'enrollment actual' in label:
                        enrollment_info['enrollment_actual'] = value
                    elif 'enrollment maximum' in label:
                        enrollment_info['enrollment_maximum'] = value
                    elif 'enrollment seats available' in label:
                        enrollment_info['enrollment_seats_available'] = value
                    elif 'waitlist capacity' in label:
                        enrollment_info['waitlist_capacity'] = value
                    elif 'waitlist actual' in label:
                        enrollment_info['waitlist_actual'] = value
                    elif 'waitlist seats available' in label:
                        enrollment_info['waitlist_seats_available'] = value
            
            # If BeautifulSoup parsing didn't work, try regex as fallback
            if enrollment_info['enrollment_actual'] == 'N/A':
                enrollment_info = self.parse_enrollment_regex(html_content)
                
        except Exception as e:
            logger.warning(f"Error parsing enrollment HTML with BeautifulSoup: {e}")
            # Fallback to regex parsing
            enrollment_info = self.parse_enrollment_regex(html_content)
        
        return enrollment_info

    def parse_enrollment_regex(self, html_content: str) -> Dict:
        """Fallback method to parse enrollment info using regex"""
        enrollment_info = {
            'enrollment_actual': 'N/A',
            'enrollment_maximum': 'N/A',
            'enrollment_seats_available': 'N/A',
            'waitlist_capacity': 'N/A',
            'waitlist_actual': 'N/A',
            'waitlist_seats_available': 'N/A'
        }
        
        if not html_content:
            return enrollment_info
        
        try:
            # Define regex patterns for each field
            patterns = {
                'enrollment_actual': r'Enrollment Actual:.*?<span dir="ltr">\s*(\d+)\s*</span>',
                'enrollment_maximum': r'Enrollment Maximum:.*?<span dir="ltr">\s*(\d+)\s*</span>',
                'enrollment_seats_available': r'Enrollment Seats Available:.*?<span dir="ltr">\s*(\d+)\s*</span>',
                'waitlist_capacity': r'Waitlist Capacity:.*?<span dir="ltr">\s*(\d+)\s*</span>',
                'waitlist_actual': r'Waitlist Actual:.*?<span dir="ltr">\s*(\d+)\s*</span>',
                'waitlist_seats_available': r'Waitlist Seats Available:.*?<span dir="ltr">\s*(\d+)\s*</span>'
            }
            
            # Extract values using regex
            for key, pattern in patterns.items():
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    enrollment_info[key] = match.group(1)
                    
        except Exception as e:
            logger.warning(f"Error parsing enrollment HTML with regex: {e}")
        
        return enrollment_info

    
    def reset_form(self):
        """Reset the search form to clear previous searches"""
        url = f"{self.base_url}/classSearch/resetDataForm"
        try:
            response = self.session.post(url)
            response.raise_for_status()
            logger.info("Form reset successfully")
        except requests.RequestException as e:
            logger.error(f"Error resetting form: {e}")
    
    def format_credit_hours(self, course: Dict) -> tuple:
        """Format credit hours from creditHourLow and creditHourHigh fields"""
        credit_low = course.get('creditHourLow', '')
        credit_high = course.get('creditHourHigh', '')
        
        # Handle various credit hour scenarios
        if credit_low and credit_high:
            if credit_low == credit_high:
                # Fixed credit hours (e.g., both are "3")
                formatted = credit_low
            else:
                # Variable credit hours (e.g., "1-4" or "3-6")
                formatted = f"{credit_low}-{credit_high}"
        elif credit_low:
            # Only low value available
            formatted = credit_low
        elif credit_high:
            # Only high value available
            formatted = credit_high
        else:
            # No credit information available
            formatted = "TBA"
        
        return credit_low, credit_high, formatted

    def scrape_course_schedule(self, term_code: str, campus: str = 'OAK', 
                              page_max_size: int = 500, max_pages: int = None) -> List[CourseSection]:
        """Main method to scrape course schedule data for a specific campus"""
        all_courses = []
        
        # Authorize session first - retry up to 3 times
        auth_success = False
        for attempt in range(3):
            logger.info(f"Attempting to authorize session (attempt {attempt + 1}/3)")
            if self.authorize_session(term_code):
                auth_success = True
                break
            else:
                logger.warning(f"Authorization attempt {attempt + 1} failed")
                time.sleep(2)  # Wait before retry
        
        if not auth_success:
            logger.error("Failed to authorize session after 3 attempts")
            return []

        
        # Search for courses on the specified campus
        logger.info(f"Starting course search for campus: {campus}")
        courses = self.search_courses(term_code, campus, page_max_size, max_pages)
        all_courses.extend(courses)
        
        logger.info(f"Found {len(all_courses)} total courses. Starting data enrichment...")
        
        # Enrich with additional data
        enriched_courses = []
        for i, course in enumerate(all_courses, 1):
            crn = course.get('courseReferenceNumber', '')
            subject = course.get('subject', '')
            course_num = course.get('courseNumber', '')
            instructional_method = course.get('instructionalMethodDescription', 'TBA')
            
            # Progress update every 10 courses or for the last course
            if i % 10 == 0 or i == len(all_courses):
                logger.info(f"Processing course {i}/{len(all_courses)}: {subject} {course_num}")
            
            # Get meeting times
            logger.debug(f"Fetching meeting times for {subject} {course_num} (CRN: {crn})")
            meeting_data = self.get_meeting_times(term_code, crn)
            meeting_times = self.format_meeting_times(meeting_data)
            
            # Parse meeting times into separate components
            meeting_components = self.parse_meeting_times_for_csv(meeting_data)
            
            # Get enrollment info
            logger.debug(f"Fetching enrollment info for {subject} {course_num} (CRN: {crn})")
            enrollment_data = self.get_enrollment_info(term_code, crn)
            
            # Extract instructor
            instructor = self.extract_instructor(meeting_data)
            
            # Format credit hours
            credit_low, credit_high, credits_formatted = self.format_credit_hours(course)
            
            # Create CourseSection object
            course_section = CourseSection(
                course_reference_number=crn,
                subject=subject,
                course_number=course_num,
                title=course.get('courseTitle', 'TBA'),
                section=course.get('sequenceNumber', 'TBA'),
                instructor=instructor,
                meeting_times=meeting_times,  # Keep original for JSON export
                days=meeting_components['days'],  # New field for CSV
                time=meeting_components['time'],  # New field for CSV  
                campus=meeting_components['campus'],  # New field for CSV
                classroom=meeting_components['classroom'],  # New field for CSV
                instructional_method=instructional_method,
                enrollment_info=enrollment_data,
                credit_hour_low=credit_low,
                credit_hour_high=credit_high,
                credits_formatted=credits_formatted
            )
            
            # Add to enriched courses list
            enriched_courses.append(course_section)
            
            time.sleep(0.2)  # Rate limiting
        
        logger.info(f"Data enrichment complete. Successfully processed {len(enriched_courses)} course sections")
        return enriched_courses
    
    def format_meeting_times(self, meeting_data: Dict) -> str:
        """Format meeting times data into readable string with campus, building description, and days"""
        if not meeting_data or 'fmt' not in meeting_data:
            return "TBA"
        
        meetings = []
        for meeting in meeting_data['fmt']:
            meeting_time = meeting.get('meetingTime', {})
            
            # Extract days of the week
            days = self.extract_days_of_week(meeting_time)
            
            # Extract time range
            begin_time = meeting_time.get('beginTime', '')
            end_time = meeting_time.get('endTime', '')
            time_str = ""
            if begin_time:
                time_str = begin_time
                if end_time:
                    time_str += f" - {end_time}"
            
            # Extract location information
            campus = meeting_time.get('campus', '')
            building = meeting_time.get('building', '')
            building_description = meeting_time.get('buildingDescription', '')
            room = meeting_time.get('room', '')
            
            # Format location string
            location_parts = []
            if campus:
                location_parts.append(f"{campus} |")
            
            # Use building description if available, otherwise fall back to building code
            if building_description:
                building_str = building_description
            elif building:
                building_str = building
            else:
                building_str = ""
            
            if building_str:
                if room:
                    location_parts.append(f"{building_str} {room}")
                else:
                    location_parts.append(building_str)
            elif room:
                location_parts.append(room)
            
            location = ", ".join(location_parts) if location_parts else "TBA"
            
            # Combine all parts
            meeting_parts = []
            if days:
                meeting_parts.append(days)
            if time_str:
                meeting_parts.append(time_str)
            if location != "TBA":
                meeting_parts.append(location)
            
            meeting_str = " | ".join(meeting_parts) if meeting_parts else "TBA"
            meetings.append(meeting_str)
        
        return "; ".join(meetings) if meetings else "TBA"

    def extract_days_of_week(self, meeting_time: Dict) -> str:
        """Extract days of the week from boolean fields"""
        if not meeting_time:
            return "TBA"
        
        # Day mapping with proper abbreviations
        day_mapping = {
            'monday': 'M',
            'tuesday': 'T', 
            'wednesday': 'W',
            'thursday': 'R',  # R is commonly used for Thursday to avoid confusion with Tuesday
            'friday': 'F',
            'saturday': 'S',
            'sunday': 'U'  # U is commonly used for Sunday
        }
        
        # Extract active days
        active_days = []
        for day, abbrev in day_mapping.items():
            if meeting_time.get(day, False):
                active_days.append(abbrev)
        
        # Return formatted string
        if active_days:
            return "".join(active_days)
        else:
            # Fallback to meetingTimeType if no individual days found
            return meeting_time.get('meetingTimeType', 'TBA')
    
    def extract_instructor(self, meeting_data: Dict) -> str:
        """Extract instructor name from meeting data"""
        if not meeting_data or 'fmt' not in meeting_data:
            return "TBA"
        
        instructors = []
        for meeting in meeting_data['fmt']:
            if 'faculty' in meeting:
                for faculty in meeting['faculty']:
                    name = faculty.get('displayName', 'TBA')
                    if name not in instructors:
                        instructors.append(name)
        
        return "; ".join(instructors) if instructors else "TBA"
    
    def save_to_csv(self, courses: List[CourseSection], filename: str, compare_with_existing: bool = True):
        """Save course data to CSV file with simplified field selection and optional comparison"""
        
        # Check for existing file and backup if needed
        comparison_result = None
        if compare_with_existing and FileManager.backup_existing_file(filename):
            # Get the backup filename
            base_name, ext = os.path.splitext(filename)
            backup_filename = f"{base_name}_OLD{ext}"
            
            # Write new file first
            self._write_csv_file(courses, filename)
            
            # Compare with backup
            comparison_result = FileManager.compare_course_files(backup_filename, filename)
            
            # Print comparison report
            FileManager.print_comparison_report(comparison_result)
        else:
            # No existing file to compare with, just write the new file
            self._write_csv_file(courses, filename)
            logger.info(f"No existing file found for comparison. Created new file: {filename}")
        
        return comparison_result
    
    def _write_csv_file(self, courses: List[CourseSection], filename: str):
        """Write courses to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Term', 'Term Code', 'CRN', 'Subject', 'Course Number', 'Title', 'Section', 
                         'Instructor', 'Days', 'Time', 'Campus', 'Classroom', 'Instructional Method', 
                         'Credits', 'Enrollment Actual', 'Enrollment Maximum']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for course in courses:
                writer.writerow({
                    'Term': getattr(course, 'term_description', 'N/A'),
                    'Term Code': getattr(course, 'term_code', 'N/A'),
                    'CRN': course.course_reference_number,
                    'Subject': course.subject,
                    'Course Number': course.course_number,
                    'Title': course.title,
                    'Section': course.section,
                    'Instructor': course.instructor,
                    'Days': course.days,
                    'Time': course.time,
                    'Campus': course.campus,
                    'Classroom': course.classroom,
                    'Instructional Method': course.instructional_method,
                    'Credits': course.credits_formatted,
                    'Enrollment Actual': course.enrollment_info.get('enrollment_actual', 'N/A'),
                    'Enrollment Maximum': course.enrollment_info.get('enrollment_maximum', 'N/A')
                })
        
        logger.info(f"Data saved to {filename}")
        

    # Helper method to get enrollment summary for quick reference
    def get_enrollment_summary(self, enrollment_info: Dict) -> str:
        """Get a quick enrollment summary string"""
        actual = enrollment_info.get('enrollment_actual', 'N/A')
        maximum = enrollment_info.get('enrollment_maximum', 'N/A')
        waitlist = enrollment_info.get('waitlist_actual', 'N/A')
        
        if actual != 'N/A' and maximum != 'N/A':
            summary = f"{actual}/{maximum}"
            if waitlist != 'N/A' and waitlist != '0':
                summary += f" (+{waitlist} waitlist)"
            return summary
        else:
            return "N/A"
    
    def save_to_json(self, courses: List[CourseSection], filename: str):
        """Save course data to JSON file"""
        data = []
        for course in courses:
            data.append({
                'course_reference_number': course.course_reference_number,
                'subject': course.subject,
                'course_number': course.course_number,
                'title': course.title,
                'section': course.section,
                'instructor': course.instructor,
                'meeting_times': course.meeting_times,
                'credit_hour_low': course.credit_hour_low,
                'credit_hour_high': course.credit_hour_high,
                'credits_formatted': course.credits_formatted,
                'enrollment_info': course.enrollment_info
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {filename}")

def main():
    """Example usage of the Banner scraper - scrapes first two terms"""
    scraper = BannerScraper()
    
    # Get available terms
    terms = scraper.get_terms()
    if not terms:
        logger.error("No terms found")
        return
    
    print("Available terms:")
    for i, term in enumerate(terms[:10]):  # Show first 10 terms
        print(f"{i+1}. {term['description']} ({term['code']})")
    
    # Use the first two terms
    terms_to_scrape = terms[:2]  # Get first two terms
    print(f"\nScraping terms:")
    for term in terms_to_scrape:
        print(f"- {term['description']} ({term['code']})")
    
    # Campus
    campus = ['OAK']
    
    all_courses = []  # List to store courses from all terms
    
    # Scrape each term
    for term in terms_to_scrape:
        term_code = term['code']
        print(f"\nScraping term: {term['description']} ({term_code})")
        
        courses = scraper.scrape_course_schedule(
            term_code=term_code,
            campus=campus,
            # subjects=subjects,
            # course_numbers=course_numbers  # Uncomment to search specific courses
        )
        
        if courses:
            # Add term information to each course for identification
            for course in courses:
                # Use attribute assignment instead of item assignment
                course.term_code = term_code
                course.term_description = term['description']
            
            all_courses.extend(courses)
            print(f"Found {len(courses)} courses for {term['description']}")
        else:
            print(f"No courses found for {term['description']}")
    
    if all_courses:
        # Create combined filename with both term codes
        term_codes = "_".join([term['code'] for term in terms_to_scrape])
        combined_filename = f'courses_combined_{term_codes}.csv'
        
        # Save combined data to CSV with comparison enabled
        comparison_result = scraper.save_to_csv(all_courses, combined_filename, compare_with_existing=True)
        
        # Optional: Also save to JSON
        # scraper.save_to_json(all_courses, f'courses_combined_{term_codes}.json')
        
        print(f"\nScraped {len(all_courses)} courses total from {len(terms_to_scrape)} terms!")
        print(f"Combined data saved to {combined_filename}")
        
        # Print summary by term
        from collections import Counter
        term_counts = Counter([course.term_description for course in all_courses])
        print("\nCourses by term:")
        for term_desc, count in term_counts.items():
            print(f"- {term_desc}: {count} courses")
    else:
        print("No courses found in any term")

if __name__ == "__main__":
    main()