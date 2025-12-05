# Banner Course Schedule Scraper

A Python-based toolset for scraping course schedules from Northeastern University's Banner system and generating interactive web visualizations.

## Overview

This project consists of two main scripts:

1. **`bscraper-compare.py`** - Scrapes course data from Banner API and tracks changes
2. **`calendar-view.py`** - Generates an interactive HTML calendar visualization

## Scripts

### bscraper-compare.py

**Purpose:** Scrapes course schedule data from Northeastern University's Banner Student Registration system via reverse-engineered API calls.

**Features:**

- Fetches course data for multiple terms/semesters
- Filters by campus (default: Oakland)
- Automatic change detection and comparison
- Backs up previous data files
- Generates detailed comparison reports

**Output:**

- `courses_combined_XXXXXX_XXXXXX.csv` - Combined course data for all scraped terms
- `courses_combined_XXXXXX_XXXXXX_OLD.csv` - Backup of previous run (if exists)
- Console report showing added/removed courses and schedule changes

**CSV Columns:**

- Term, Term Code, CRN, Subject, Course Number, Title, Section
- Instructor, Days, Time, Campus, Classroom
- Credits, Enrollment Actual, Enrollment Maximum

**Usage:**

```bash
uv run bscraper-compare.py
```

The script will:

1. Connect to Banner API
2. Display available terms
3. Scrape the first 2 terms for Oakland campus
4. Save data to CSV
5. Compare with previous run (if exists) and show changes

### calendar-view.py

**Purpose:** Transforms CSV course data into an interactive web calendar with visual timeline grid.

**Features:**

- Weekly schedule grid (8 AM - 10 PM)
- Color-coded by subject
- Interactive filtering (search, term, subject, time of day)
- Click courses for detailed information modal
- Mobile-responsive design

**Output:**

- `course_calendar.html` - Self-contained interactive HTML file

**Usage:**

```bash
uv run calendar-view.py
```

When prompted, enter the CSV filename (or press Enter for default):

```
Enter the CSV file name [courses_combined_202630_202625.csv]: 
```

The generated HTML can be:

- Opened directly in any web browser
- Hosted on a web server
- Shared with colleagues

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Clone or download the project:**

```bash
cd ~/projects
git clone <repository-url> banner_scraper
cd banner_scraper
```

2. **Install dependencies:**

```bash
uv add requests beautifulsoup4 pandas
```

Or using a requirements file:

```bash
uv add -r requirements.txt
```

## Workflow

### Basic Usage

**Step 1: Scrape course data**

```bash
uv run bscraper-compare.py
```

This generates: `courses_combined_202630_202625.csv`

**Step 2: Generate calendar view**

```bash
uv run calendar-view.py
# Enter the CSV filename when prompted
```

This generates: `course_calendar.html`

**Step 3: Open the calendar**

```bash
open course_calendar.html  # macOS
# or
xdg-open course_calendar.html  # Linux
```

### Change Detection

When you re-run `bscraper-compare.py`, it automatically:

- Backs up the previous CSV (adds `_OLD` suffix)
- Compares new data with old data
- Reports changes:
  - 📚 Added courses
  - ❌ Removed courses  
  - 🔄 Time/location changes
  - 📊 Enrollment changes

This helps track schedule updates over time.

## Dependencies

- **requests** (≥2.31.0) - HTTP requests to Banner API
- **beautifulsoup4** (≥4.12.0) - HTML parsing
- **pandas** (≥2.0.0) - Data manipulation and CSV handling

## Configuration

### Scraper Settings

To modify which terms or campus to scrape, edit `bscraper-compare.py`:

```python
# Line ~1004: Change number of terms to scrape
terms_to_scrape = terms[:2]  # Scrape first 2 terms

# Line ~1010: Change campus filter
campus = ['OAK']  # Oakland campus
# Other options: ['BOS'], ['SEA'], ['SAN'], etc.
```

### Calendar View Settings

To modify the calendar time range, edit `calendar-view.py`:

```python
# Line ~485: Change time slot range
for hour in range(8, 22):  # 8 AM to 10 PM
```

## Files Generated

| File | Description | Keep? |
|------|-------------|-------|
| `courses_combined_*.csv` | Course data | ✓ Yes |
| `courses_combined_*_OLD.csv` | Previous version backup | Optional |
| `course_calendar.html` | Interactive calendar | ✓ Yes |

## Troubleshooting

**Problem:** `ModuleNotFoundError`

```bash
# Solution: Install dependencies
uv add requests beautifulsoup4 pandas
```

**Problem:** "No terms found"

```
# Solution: Check internet connection, Banner may be down
# Try again later
```

**Problem:** Empty CSV file

```
# Solution: Banner may have no courses for selected campus/term
# Check the campus filter in the script
```

**Problem:** Calendar shows "Unknown Term"

```
# Solution: Re-run scraper with updated version that includes Term column
# Old CSV files won't have term information
```

## Project Structure

```
banner_scraper/
├── bscraper-compare.py          # Main scraper script
├── calendar-view.py             # Calendar generator
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── courses_combined_*.csv       # Generated course data
└── course_calendar.html         # Generated calendar view
```

## Tips

1. **Run the scraper periodically** to track schedule changes over time
2. **Keep the CSV files** to maintain historical data
3. **Share the HTML file** with colleagues - it's self-contained and works offline
4. **Filter by term** in the calendar view when combining multiple semesters
5. **Use the search box** to quickly find specific courses or instructors

## Support

For issues with:

- **Banner API changes** - The API is reverse-engineered and may change
- **Script errors** - Check dependencies are installed with `uv pip list`
- **Data accuracy** - Always verify against official Banner schedule

## License

For internal use at F.W. Olin Library, Mills College at Northeastern University.

---

**Last Updated:** December 2024  
**Maintained by:** Technical Services, Olin Library

## Extending

Banner Course Model

```JSON
{
  "id": 502389,
  "term": "202630",
  "termDesc": "Spring 2026 Semester",
  "courseReferenceNumber": "40312",
  "partOfTerm": "1",
  "courseNumber": "7247",
  "subject": "EECE",
  "subjectDescription": "Electrical and Comp Engineerng",
  "sequenceNumber": "02",
  "campusDescription": "Oakland, CA",
  "scheduleTypeDescription": "Lecture",
  "courseTitle": "Radio Frequency Integrated Circuit Design",
  "creditHours": null,
  "maximumEnrollment": 10,
  "enrollment": 1,
  "seatsAvailable": 9,
  "waitCapacity": 0,
  "waitCount": 0,
  "waitAvailable": 0,
  "crossList": null,
  "crossListCapacity": null,
  "crossListCount": null,
  "crossListAvailable": null,
  "creditHourHigh": null,
  "creditHourLow": 4,
  "creditHourIndicator": null,
  "openSection": true,
  "linkIdentifier": null,
  "isSectionLinked": false,
  "subjectCourse": "EECE7247",
  "faculty": [],
  "meetingsFaculty": [
    {
      "category": "01",
      "class": "net.hedtech.banner.student.schedule.SectionSessionDecorator",
      "courseReferenceNumber": "40312",
      "faculty": [],
      "meetingTime": {
        "beginTime": "0650",
        "building": "M44",
        "buildingDescription": "Mills Hall",
        "campus": "OAK",
        "campusDescription": "Oakland, CA",
        "category": "01",
        "class": "net.hedtech.banner.general.overall.MeetingTimeDecorator",
        "courseReferenceNumber": "40312",
        "creditHourSession": 4.0,
        "endDate": "04/26/2026",
        "endTime": "0830",
        "friday": true,
        "hoursWeek": 3.33,
        "meetingScheduleType": "LEC",
        "meetingType": "CLAS",
        "meetingTypeDescription": "Class",
        "monday": false,
        "room": "133",
        "saturday": false,
        "startDate": "01/07/2026",
        "sunday": false,
        "term": "202630",
        "thursday": false,
        "tuesday": true,
        "wednesday": false
      },
      "term": "202630"
    }
  ],
  "reservedSeatSummary": null,
  "sectionAttributes": [
    {
      "class": "net.hedtech.banner.student.schedule.SectionDegreeProgramAttributeDecorator",
      "code": "GBEN",
      "courseReferenceNumber": "40312",
      "description": "GSEN Engineering",
      "isZTCAttribute": false,
      "termCode": "202630"
    }
  ],
  "instructionalMethod": "LC",
  "instructionalMethodDescription": "Live Cast"
}
```
## Extending bscraper-compare.py

1. Add new element to data model (line 27)
   - class CourseSection:
2. Add to course (line 763)
   - CourseSection object
3. Add to csv fieldnames (line 925)
   - fieldnames
4. Add to csv writer (line 932)
   - writer.writerow

## Extending calendar-view.py

1. Add to event array (line 101
2. Add to modalBody (line 586)