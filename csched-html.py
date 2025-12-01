import pandas as pd
from collections import defaultdict
import re
from datetime import datetime

def parse_time_range(time_str):
    """Parse time range string and return start and end times in minutes from midnight"""
    if pd.isna(time_str) or time_str == 'TBA':
        return None, None
    
    # Handle format like "1150 - 1330"
    match = re.match(r'(\d{4})\s*-\s*(\d{4})', time_str)
    if match:
        start_str, end_str = match.groups()
        start_hour = int(start_str[:2])
        start_min = int(start_str[2:])
        end_hour = int(end_str[:2])
        end_min = int(end_str[2:])
        
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        return start_minutes, end_minutes
    
    return None, None

def minutes_to_time_str(minutes):
    """Convert minutes from midnight to time string"""
    if minutes is None:
        return "TBA"
    
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def parse_days(days_str):
    """Parse days string and return list of individual days"""
    if pd.isna(days_str) or days_str == 'TBA':
        return []
    
    # Handle formats like "MW", "TR", "MWF", "WF", etc.
    day_mapping = {
        'M': 'Monday',
        'T': 'Tuesday', 
        'W': 'Wednesday',
        'R': 'Thursday',  # R is used for Thursday in academic scheduling
        'F': 'Friday',
        'S': 'Saturday'
    }
    
    days = []
    for char in days_str:
        if char in day_mapping:
            days.append(day_mapping[char])
    
    return days

def generate_html_header(csv_file):
    """Generate HTML header with CSS styling"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Classroom Schedules</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .navigation {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #ecf0f1, #bdc3c7);
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .classroom-selector {
            font-size: 16px;
            padding: 10px 15px;
            border: 2px solid #3498db;
            border-radius: 6px;
            background-color: white;
            color: #2c3e50;
            cursor: pointer;
            min-width: 250px;
        }
        
        .classroom-selector:focus {
            outline: none;
            border-color: #2980b9;
            box-shadow: 0 0 8px rgba(52, 152, 219, 0.3);
        }
        
        .nav-label {
            font-weight: bold;
            color: #2c3e50;
            margin-right: 15px;
            font-size: 16px;
        }
        
        .classroom-section {
            margin-bottom: 50px;
            break-inside: avoid;
        }
        
        .classroom-title {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 15px;
            margin: 20px 0 10px 0;
            border-radius: 8px;
            font-size: 1.5em;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .schedule-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .schedule-table th {
            background: linear-gradient(135deg, #34495e, #2c3e50);
            color: white;
            padding: 12px 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #2c3e50;
        }
        
        .schedule-table th.time-header {
            width: 100px;
            min-width: 100px;
        }
        
        .schedule-table td {
            border: 1px solid #ddd;
            padding: 8px;
            vertical-align: top;
            background-color: #fff;
            min-height: 60px;
        }
        
        .schedule-table td.time-cell {
            background-color: #ecf0f1;
            font-weight: bold;
            text-align: center;
            white-space: nowrap;
            width: 100px;
            min-width: 100px;
        }
        
        .schedule-table td.empty-cell {
            background-color: #f8f9fa;
            text-align: center;
            color: #bdc3c7;
            font-style: italic;
        }
        
        .course-block {
            background: linear-gradient(135deg, #e8f4fd, #d1ecf1);
            border: 1px solid #3498db;
            border-radius: 6px;
            padding: 6px;
            margin: 2px 0;
            font-size: 11px;
            line-height: 1.2;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .course-code {
            font-weight: bold;
            color: #2c3e50;
            font-size: 12px;
        }
        
        .course-title {
            color: #34495e;
            font-size: 10px;
            margin: 2px 0;
            font-style: italic;
        }
        
        .course-instructor {
            color: #7f8c8d;
            font-size: 10px;
        }
        
        .course-enrollment {
            color: #e74c3c;
            font-weight: bold;
            font-size: 10px;
            float: right;
        }
        
        .generation-info {
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
        }
        
        @media print {
            .classroom-section {
                break-inside: avoid;
                page-break-inside: avoid;
                page-break-before: always;
            }
            
            .schedule-table {
                font-size: 10px;
            }
        }
        
        @media (max-width: 768px) {
            .schedule-table {
                font-size: 10px;
            }
            
            .schedule-table th, .schedule-table td {
                padding: 4px;
            }
        }
    </style>
    <script>
        function jumpToClassroom() {
            const selector = document.getElementById('classroomSelector');
            const selectedClassroom = selector.value;
            if (selectedClassroom) {
                document.getElementById(selectedClassroom).scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h2>Northeastern University Oakland: Winter/Spring 2026 Classroom Schedules</h2>
        <h4>Schedules are subject to change and not all classes may be shown.  <a href=
        "{csv_file}">CSV data file available.</a></h4>
        <h4>Please see the <a href="https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search">Online Course Schedule</a> for the latest updates.</h4>
"""

def generate_navigation_menu(sorted_classrooms):
    """Generate navigation dropdown menu"""
    nav_html = '        <div class="navigation">\n'
    nav_html += '            <span class="nav-label">Jump to Classroom:</span>\n'
    nav_html += '            <select id="classroomSelector" class="classroom-selector" onchange="jumpToClassroom()">\n'
    nav_html += '                <option value="">-- Select a Classroom --</option>\n'
    
    for classroom in sorted_classrooms:
        # Create a safe ID for the classroom (replace spaces and special characters)
        safe_id = classroom.replace(' ', '_').replace('/', '_').replace('-', '_').replace('.', '_')
        nav_html += f'                <option value="classroom_{safe_id}">{classroom}</option>\n'
    
    nav_html += '            </select>\n'
    nav_html += '        </div>\n'
    
    return nav_html
    
def generate_html_footer():    
    """Generate HTML footer"""
    generation_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return f"""
        <div class="generation-info">
            Generated on {generation_time}
        </div>
    </div>
    </body>
    </html>"""

def generate_classroom_schedules_html(csv_file, output_file='classroom_schedules.html'):
    """Generate HTML schedule tables for each classroom"""
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Group courses by classroom
    classroom_data = defaultdict(list)
    
    for _, row in df.iterrows():
        classroom_str = row['Classroom']
        if pd.isna(classroom_str) or classroom_str == 'TBA':
            continue
            
        days_str = row['Days']
        time_str = row['Time']
        
        # Handle multiple classrooms separated by semicolons
        classroom_parts = str(classroom_str).split(';')
        
        # Handle multiple day/time combinations separated by semicolons
        if pd.notna(days_str) and pd.notna(time_str):
            days_parts = str(days_str).split(';')
            time_parts = str(time_str).split(';')
            
            # Make sure we have matching classroom/day/time combinations
            max_parts = max(len(classroom_parts), len(days_parts), len(time_parts))
            
            for i in range(max_parts):
                # Use the last available value if we run out of parts
                classroom_idx = min(i, len(classroom_parts) - 1)
                days_idx = min(i, len(days_parts) - 1)
                time_idx = min(i, len(time_parts) - 1)
                
                classroom = classroom_parts[classroom_idx].strip()
                days = parse_days(days_parts[days_idx].strip())
                start_time, end_time = parse_time_range(time_parts[time_idx].strip())
                
                if classroom and classroom != 'TBA' and days and start_time is not None and end_time is not None:
                    course_info = {
                        'subject': row['Subject'],
                        'course_num': row['Course Number'],
                        'title': row['Title'],
                        'section': row['Section'],
                        'instructor': row['Instructor'],
                        'days': days,
                        'start_time': start_time,
                        'end_time': end_time,
                        'actual_enrollment': row['Enrollment Actual'],
                        'max_enrollment': row['Enrollment Maximum']
                    }
                    classroom_data[classroom].append(course_info)
    
    # Start building HTML
    html_content = generate_html_header(csv_file)
    
    # Sort classrooms for consistent output
    sorted_classrooms = sorted(classroom_data.keys())
        
    # Add navigation menu
    html_content += generate_navigation_menu(sorted_classrooms)

    # Generate tables for each classroom
    for classroom in sorted_classrooms:
        courses = classroom_data[classroom]
        
        # Create a safe ID for the classroom
        safe_id = classroom.replace(' ', '_').replace('/', '_').replace('-', '_').replace('.', '_')
        
        html_content += f'        <div class="classroom-section" id="classroom_{safe_id}">\n'
        html_content += f'            <div class="classroom-title">CLASSROOM: {classroom}</div>\n'
        
        # Create a schedule grid
        schedule_grid = defaultdict(lambda: defaultdict(list))
        
        # Get all unique time slots
        time_slots = set()
        for course in courses:
            time_slots.add((course['start_time'], course['end_time']))
        
        # Sort time slots by start time
        time_slots = sorted(time_slots)
        
        # Fill the grid
        for course in courses:
            time_slot = (course['start_time'], course['end_time'])
            for day in course['days']:
                schedule_grid[time_slot][day].append(course)
        
        # Build the HTML table
        html_content += '            <table class="schedule-table">\n'
        
        # Header
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        html_content += '                <thead>\n                    <tr>\n'
        html_content += '                        <th class="time-header">Time</th>\n'
        for day in days_order:
            html_content += f'                        <th>{day}</th>\n'
        html_content += '                    </tr>\n                </thead>\n'
        
        html_content += '                <tbody>\n'
        
        # Rows for each time slot
        for start_time, end_time in time_slots:
            time_range = f"{minutes_to_time_str(start_time)}-{minutes_to_time_str(end_time)}"
            html_content += '                    <tr>\n'
            html_content += f'                        <td class="time-cell">{time_range}</td>\n'
            
            for day in days_order:
                courses_in_slot = schedule_grid[(start_time, end_time)][day]
                if courses_in_slot:
                    html_content += '                        <td>\n'
                    for course in courses_in_slot:
                        course_code = f"{course['subject']} {course['course_num']}-{course['section']}"
                        course_title = str(course['title'])[:50] + ('...' if len(str(course['title'])) > 50 else '')
                        instructor = str(course['instructor'])
                        actual_enrollment = course['actual_enrollment']
                        max_enrollment = course['max_enrollment']
                        
                        html_content += '                            <div class="course-block">\n'
                        html_content += f'                                <div class="course-code">{course_code}</div>\n'
                        html_content += f'                                <div class="course-title">{course_title}</div>\n'
                        html_content += f'                                <div class="course-instructor">{instructor}</div>\n'
                        html_content += f'                                <div class="course-enrollment">{actual_enrollment}/{max_enrollment}</div>\n'
                        html_content += '                            </div>\n'
                    html_content += '                        </td>\n'
                else:
                    html_content += '                        <td class="empty-cell">—</td>\n'
            
            html_content += '                    </tr>\n'
        
        html_content += '                </tbody>\n'
        html_content += '            </table>\n'
        html_content += '        </div>\n'
    
    # Add footer
    html_content += generate_html_footer()
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML schedule file generated: {output_file}")
    print(f"Found schedules for {len(sorted_classrooms)} classrooms:")
    for classroom in sorted_classrooms:
        course_count = len(classroom_data[classroom])
        print(f"  - {classroom}: {course_count} course sections")

# Example usage
if __name__ == "__main__":
    # Ask user for CSV file name with default option
    csv_file = input("Enter the CSV file name [courses_combined_202615_202610.csv]: ").strip()
    if not csv_file:  # If user just pressed Enter
        csv_file = 'courses_combined_202615_202610.csv'
    output_file = 'classroom_schedules.html'
    generate_classroom_schedules_html(csv_file, output_file)