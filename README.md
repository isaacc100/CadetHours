# Hour Tracker

A simple desktop application built with **PySide6** and **SQLite** to track hours worked, categorized by activity type, with optional travel time. Designed to help SJA volunteers or workers log their time easily.

## Features

- Add entries with:
  - Date
  - Activity type (preset categories plus custom tags)
  - Hours worked
  - Travel time (tracked separately but included in totals)
- Edit and delete existing entries
- View all entries in a table with totals per entry
- Summary display showing:
  - Total hours per category
  - Overall hours with and without travel time
- Data stored persistently using an SQLite database
- Export as a CSV or Excel spreadsheet
- Load a CSV

## Getting Started

### Prerequisites

- Python 3.7+
- [PySide6](https://pypi.org/project/PySide6/) (`pip install PySide6`)

### Installation

Clone the repo:

```bash
git clone https://github.com/yourusername/hour-tracker.git
cd hour-tracker
