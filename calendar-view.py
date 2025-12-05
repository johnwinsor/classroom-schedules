#!/usr/bin/env python3
"""
Generate an interactive calendar/timeline view of course schedules
"""

import pandas as pd
import json
from datetime import datetime
from collections import defaultdict
from html import unescape

def parse_time(time_str):
    """Parse time string like '1150 - 1330' and return start and end in HH:MM format"""
    if pd.isna(time_str) or time_str == 'TBA':
        return None, None
    
    import re
    match = re.match(r'(\d{4})\s*-\s*(\d{4})', str(time_str))
    if match:
        start_str, end_str = match.groups()
        start_hour = int(start_str[:2])
        start_min = int(start_str[2:])
        end_hour = int(end_str[:2])
        end_min = int(end_str[2:])
        
        return f"{start_hour:02d}:{start_min:02d}", f"{end_hour:02d}:{end_min:02d}"
    
    return None, None

def parse_days(days_str):
    """Parse days string like 'MW' or 'TR' into full day names"""
    if pd.isna(days_str) or days_str == 'TBA':
        return []
    
    day_mapping = {
        'M': 'Monday',
        'T': 'Tuesday',
        'W': 'Wednesday',
        'R': 'Thursday',
        'F': 'Friday',
        'S': 'Saturday'
    }
    
    days = []
    for char in str(days_str):
        if char in day_mapping:
            days.append(day_mapping[char])
    
    return days

def get_subject_color(subject):
    """Assign colors to subjects for visual distinction"""
    # Generate a consistent color based on subject code
    colors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
        '#27ae60', '#d35400', '#8e44ad', '#2980b9', '#f1c40f'
    ]
    
    # Use hash to get consistent color for same subject
    hash_val = sum(ord(c) for c in subject)
    return colors[hash_val % len(colors)]

def generate_calendar_html(csv_file, output_file='course_calendar.html'):
    """Generate interactive calendar view HTML"""
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Prepare data structure
    events = []
    subjects = set()
    terms = set()
    
    for _, row in df.iterrows():
        days_str = row['Days']
        time_str = row['Time']
        
        # Get term information (with fallback for old CSV format)
        term = str(row.get('Term', 'Unknown Term'))
        term_code = str(row.get('Term Code', ''))
        terms.add(term)
        
        # Handle multiple meeting times (separated by semicolons)
        if pd.notna(days_str) and pd.notna(time_str):
            days_parts = str(days_str).split(';')
            time_parts = str(time_str).split(';')
            
            for i in range(max(len(days_parts), len(time_parts))):
                days_idx = min(i, len(days_parts) - 1)
                time_idx = min(i, len(time_parts) - 1)
                
                days = parse_days(days_parts[days_idx].strip())
                start_time, end_time = parse_time(time_parts[time_idx].strip())
                
                if days and start_time and end_time:
                    subject = str(row['Subject'])
                    subjects.add(subject)
                    
                    for day in days:
                        event = {
                            'title': f"{row['Subject']} {row['Course Number']}-{row['Section']}",
                            'courseName': unescape(str(row['Title'])),
                            'instructor': unescape(str(row['Instructor'])),
                            'classroom': unescape(str(row['Classroom'])),
                            'instructionalMethod': unescape(str(row['Instructional Method'])),
                            'enrollment': f"{row['Enrollment Actual']}/{row['Enrollment Maximum']}",
                            'day': day,
                            'start': start_time,
                            'end': end_time,
                            'subject': subject,
                            'term': term,
                            'termCode': term_code,
                            'color': get_subject_color(subject),
                            'crn': str(row['CRN'])
                        }
                        events.append(event)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Calendar View</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-group label {{
            font-weight: 600;
            color: #495057;
        }}
        
        .filter-group input,
        .filter-group select {{
            padding: 8px 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }}
        
        .filter-group input:focus,
        .filter-group select:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .calendar-container {{
            padding: 30px;
            overflow-x: auto;
        }}
        
        .calendar {{
            display: grid;
            grid-template-columns: 80px repeat(6, 1fr);
            gap: 1px;
            background: #dee2e6;
            border: 1px solid #dee2e6;
            min-width: 1200px;
        }}
        
        .calendar-header {{
            background: #343a40;
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: 700;
            font-size: 1.1em;
        }}
        
        .time-label {{
            background: #495057;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: 600;
            font-size: 0.9em;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .day-cell {{
            background: white;
            padding: 5px;
            min-height: 80px;
            position: relative;
        }}
        
        .event {{
            background: #3498db;
            border-radius: 8px;
            padding: 8px;
            margin-bottom: 5px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid rgba(0, 0, 0, 0.2);
        }}
        
        .event:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        
        .event-title {{
            font-weight: 700;
            font-size: 0.9em;
            color: white;
            margin-bottom: 3px;
        }}
        
        .event-details {{
            font-size: 0.75em;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.4;
        }}
        
        .event-time {{
            font-weight: 600;
            margin-bottom: 2px;
        }}
        
        .legend {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 2px solid #e9ecef;
        }}
        
        .legend-title {{
            font-weight: 700;
            margin-bottom: 15px;
            font-size: 1.1em;
            color: #343a40;
        }}
        
        .legend-items {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 12px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        
        .legend-label {{
            font-weight: 600;
            color: #495057;
            font-size: 0.9em;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        
        .modal.active {{
            display: flex;
        }}
        
        .modal-content {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .modal-header {{
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #343a40;
        }}
        
        .modal-body {{
            line-height: 1.8;
        }}
        
        .modal-row {{
            display: flex;
            margin-bottom: 12px;
        }}
        
        .modal-label {{
            font-weight: 700;
            width: 120px;
            color: #495057;
        }}
        
        .modal-value {{
            color: #212529;
        }}
        
        .modal-close {{
            margin-top: 20px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }}
        
        .modal-close:hover {{
            background: #764ba2;
        }}
        
        @media (max-width: 768px) {{
            .calendar {{
                min-width: 100%;
            }}
            
            .calendar-header,
            .time-label {{
                font-size: 0.8em;
                padding: 10px 5px;
            }}
            
            .event {{
                padding: 5px;
            }}
            
            .event-title {{
                font-size: 0.75em;
            }}
            
            .event-details {{
                font-size: 0.65em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Course Calendar</h1>
            <p>Interactive weekly schedule view</p>
        </div>
        
        <div class="controls">
            <div class="filter-group">
                <label for="searchInput">🔍 Search:</label>
                <input type="text" id="searchInput" placeholder="Course, instructor, room...">
            </div>
            
            <div class="filter-group">
                <label for="termFilter">📅 Term:</label>
                <select id="termFilter">
                    <option value="">All Terms</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="subjectFilter">📚 Subject:</label>
                <select id="subjectFilter">
                    <option value="">All Subjects</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="timeFilter">🕐 Time:</label>
                <select id="timeFilter">
                    <option value="">All Times</option>
                    <option value="morning">Morning (before 12pm)</option>
                    <option value="afternoon">Afternoon (12pm-5pm)</option>
                    <option value="evening">Evening (after 5pm)</option>
                </select>
            </div>
        </div>
        
        <div class="calendar-container">
            <div class="calendar" id="calendar">
                <!-- Calendar will be generated by JavaScript -->
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title">📊 Subject Legend</div>
            <div class="legend-items" id="legend">
                <!-- Legend will be generated by JavaScript -->
            </div>
        </div>
    </div>
    
    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header" id="modalTitle"></div>
            <div class="modal-body" id="modalBody"></div>
            <button class="modal-close" onclick="closeModal()">Close</button>
        </div>
    </div>
    
    <script>
        const events = {json.dumps(events, indent=8)};
        
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const timeSlots = [];
        
        // Generate time slots from 8:00 to 22:00 (10pm)
        for (let hour = 8; hour <= 21; hour++) {{
            timeSlots.push({{
                label: `${{hour.toString().padStart(2, '0')}}:00`,
                start: `${{hour.toString().padStart(2, '0')}}:00`,
                end: `${{(hour + 1).toString().padStart(2, '0')}}:00`
            }});
        }}
        
        function renderCalendar(filteredEvents = events) {{
            const calendar = document.getElementById('calendar');
            calendar.innerHTML = '';
            
            // Header row
            const timeHeader = document.createElement('div');
            timeHeader.className = 'calendar-header';
            timeHeader.textContent = 'Time';
            calendar.appendChild(timeHeader);
            
            days.forEach(day => {{
                const dayHeader = document.createElement('div');
                dayHeader.className = 'calendar-header';
                dayHeader.textContent = day;
                calendar.appendChild(dayHeader);
            }});
            
            // Time slot rows
            timeSlots.forEach(slot => {{
                const timeLabel = document.createElement('div');
                timeLabel.className = 'time-label';
                timeLabel.textContent = slot.label;
                calendar.appendChild(timeLabel);
                
                days.forEach(day => {{
                    const cell = document.createElement('div');
                    cell.className = 'day-cell';
                    
                    // Find events for this day and time slot
                    const cellEvents = filteredEvents.filter(event => {{
                        return event.day === day && 
                               event.start >= slot.start && 
                               event.start < slot.end;
                    }});
                    
                    cellEvents.forEach(event => {{
                        const eventDiv = document.createElement('div');
                        eventDiv.className = 'event';
                        eventDiv.style.background = event.color;
                        eventDiv.onclick = () => showEventDetails(event);
                        
                        eventDiv.innerHTML = `
                            <div class="event-title">${{event.title}}</div>
                            <div class="event-details">
                                <div class="event-time">${{event.start}} - ${{event.end}}</div>
                                <div>${{event.classroom}}</div>
                            </div>
                        `;
                        
                        cell.appendChild(eventDiv);
                    }});
                    
                    calendar.appendChild(cell);
                }});
            }});
        }}
        
        function renderLegend() {{
            const legend = document.getElementById('legend');
            const subjectFilter = document.getElementById('subjectFilter');
            const termFilter = document.getElementById('termFilter');
            const subjects = [...new Set(events.map(e => e.subject))].sort();
            const terms = [...new Set(events.map(e => e.term))].sort();
            
            subjects.forEach(subject => {{
                const item = document.createElement('div');
                item.className = 'legend-item';
                
                const color = events.find(e => e.subject === subject).color;
                
                item.innerHTML = `
                    <div class="legend-color" style="background: ${{color}}"></div>
                    <div class="legend-label">${{subject}}</div>
                `;
                
                legend.appendChild(item);
                
                // Add to subject filter
                const option = document.createElement('option');
                option.value = subject;
                option.textContent = subject;
                subjectFilter.appendChild(option);
            }});
            
            // Populate term filter
            terms.forEach(term => {{
                const option = document.createElement('option');
                option.value = term;
                option.textContent = term;
                termFilter.appendChild(option);
            }});
        }}
        
        function showEventDetails(event) {{
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modalTitle');
            const modalBody = document.getElementById('modalBody');
            
            modalTitle.textContent = event.title;
            modalBody.innerHTML = `
                <div class="modal-row">
                    <div class="modal-label">Term:</div>
                    <div class="modal-value">${{event.term}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Course:</div>
                    <div class="modal-value">${{event.courseName}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">CRN:</div>
                    <div class="modal-value">${{event.crn}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Instructor:</div>
                    <div class="modal-value">${{event.instructor}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Time:</div>
                    <div class="modal-value">${{event.day}}, ${{event.start}} - ${{event.end}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Classroom:</div>
                    <div class="modal-value">${{event.classroom}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Instuctional Method:</div>
                    <div class="modal-value">${{event.instructionalMethod}}</div>
                </div>
                <div class="modal-row">
                    <div class="modal-label">Enrollment:</div>
                    <div class="modal-value">${{event.enrollment}}</div>
                </div>
            `;
            
            modal.classList.add('active');
        }}
        
        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
        }}
        
        function applyFilters() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const termFilter = document.getElementById('termFilter').value;
            const subjectFilter = document.getElementById('subjectFilter').value;
            const timeFilter = document.getElementById('timeFilter').value;
            
            let filtered = events;
            
            // Search filter
            if (searchTerm) {{
                filtered = filtered.filter(event => 
                    event.title.toLowerCase().includes(searchTerm) ||
                    event.courseName.toLowerCase().includes(searchTerm) ||
                    event.instructor.toLowerCase().includes(searchTerm) ||
                    event.classroom.toLowerCase().includes(searchTerm)
                );
            }}
            
            // Term filter
            if (termFilter) {{
                filtered = filtered.filter(event => event.term === termFilter);
            }}
            
            // Subject filter
            if (subjectFilter) {{
                filtered = filtered.filter(event => event.subject === subjectFilter);
            }}
            
            // Time filter
            if (timeFilter) {{
                filtered = filtered.filter(event => {{
                    const hour = parseInt(event.start.split(':')[0]);
                    if (timeFilter === 'morning') return hour < 12;
                    if (timeFilter === 'afternoon') return hour >= 12 && hour < 17;
                    if (timeFilter === 'evening') return hour >= 17;
                    return true;
                }});
            }}
            
            renderCalendar(filtered);
        }}
        
        // Event listeners
        document.getElementById('searchInput').addEventListener('input', applyFilters);
        document.getElementById('termFilter').addEventListener('change', applyFilters);
        document.getElementById('subjectFilter').addEventListener('change', applyFilters);
        document.getElementById('timeFilter').addEventListener('change', applyFilters);
        
        // Close modal on background click
        document.getElementById('modal').addEventListener('click', (e) => {{
            if (e.target.id === 'modal') {{
                closeModal();
            }}
        }});
        
        // Initialize
        renderCalendar();
        renderLegend();
        
        console.log(`Loaded ${{events.length}} course events`);
    </script>
</body>
</html>"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✨ Calendar view generated: {output_file}")
    print(f"📊 Total events: {len(events)}")
    print(f"📚 Subjects: {len(subjects)}")

if __name__ == "__main__":
    # Ask user for CSV file
    csv_file = input("Enter the CSV file name [courses_combined_202630_202625.csv]: ").strip()
    if not csv_file:
        csv_file = 'courses_combined_202630_202625.csv'
    
    output_file = 'course_calendar.html'
    generate_calendar_html(csv_file, output_file)
