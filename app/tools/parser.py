"""
parser.py

@author: Emotu Balogun
@created: December 11, 2024

Functionality for parsing NACE activity codes and descriptions from text.

This module provides utilities to extract structured data from NACE classification
documents, including section, division, group and class level information along
with included/excluded activities.

Key Features:
    - Parses hierarchical NACE code structure
    - Extracts activity descriptions and metadata
    - Handles included/excluded activity lists
    - Validates code format and relationships

Usage:
    >>> from app.tools.parser import parse_nace_activities
    >>> activities = parse_nace_activities(nace_text)
    >>> print(activities[0]["section_code"])  # "A"
    >>> print(activities[0]["division_name"]) # "Crop production"

Notes:
    - Developed with AI assistance to standardize NACE document parsing
    - Follows official NACE Rev.2 classification structure
    - Validates hierarchical relationships between codes
"""

import re
import pathlib


def parse_nace_activities(text):
    """Parse NACE activity codes and descriptions from text.

    This function processes text containing NACE classification data and extracts structured
    information about economic activities at different hierarchical levels (section,
    division, group, class).

    Args:
        text (str): Raw text containing NACE classification data in markdown format

    Returns:
        list[dict]: List of dictionaries containing parsed NACE activities. Each dictionary has:
            - section_name (str): Name of the NACE section (e.g. "Agriculture")
            - section_code (str): Single letter code for section (e.g. "A")
            - section_description (str): Description of section scope
            - division_name (str): Name of division within section
            - division_code (str): Two digit code for division (e.g. "01")
            - division_description (str): Description of division scope
            - group_name (str): Name of group within division
            - group_code (str): Four digit code for group (e.g. "01.1")
            - group_description (str): Description of group scope
            - class_name (str): Name of class within group
            - class_code (str): Four digit code for class (e.g. "01.11")
            - class_description (str): Description of class scope
            - included_activities (list): Activities included in this class
            - excluded_activities (list): Activities excluded from this class

    Example:
        >>> text = "# Section A - Agriculture\\n###### 01 Crop production\\n..."
        >>> activities = parse_nace_activities(text)
        >>> print(activities[0]["section_code"])
        'A'
        >>> print(activities[0]["division_name"])
        'Crop production'
    """
    activities = []
    processed_codes = set()
    
    # Track parent information
    current_section = {"code": "", "name": "", "description": ""}
    current_division = {"code": "", "name": "", "description": ""}
    current_group = {"code": "", "name": "", "description": ""}
    
    # Regex patterns
    section_pattern = r"^# Section ([A-Z])\s*[–—-]\s*(.+)$"
    division_pattern = r"^(?:######\s*)?(\d{2})\s+(.+)$"
    group_pattern = r"^(?:######\s*)?(\d{2}\.\d{1})\s+(.+)$"
    class_pattern = r"^(?:######\s*)?(\d{2}\.\d{2})\s+(.+)$"

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.isdigit():
            i += 1
            continue

        # Match section
        if section_match := re.match(section_pattern, line):
            current_section = {
                "code": section_match.group(1),
                "name": section_match.group(2),
                "description": ""
            }
            for j in range(i + 1, min(i + 10, len(lines))):
                desc_text = " ".join(lines[j : j + 3])
                if "This section includes" in desc_text:
                    current_section["description"] = (
                        desc_text.split("This section includes")[1]
                        .split("\n")[0]
                        .strip()
                    )
                    break

        # Match division
        elif division_match := re.match(division_pattern, line):
            div_code = division_match.group(1)
            if len(div_code) == 2 and div_code.isdigit():
                current_division = {
                    "code": div_code,
                    "name": division_match.group(2),
                    "description": ""
                }
                for j in range(i + 1, min(i + 10, len(lines))):
                    desc_text = " ".join(lines[j : j + 3])
                    if "This division includes" in desc_text:
                        current_division["description"] = (
                            desc_text.split("This division includes")[1]
                            .split("\n")[0]
                            .strip()
                        )
                        break

        # Match group
        elif group_match := re.match(group_pattern, line):
            group_code = group_match.group(1)
            # Allow group matching if it matches the division code or we're about to process a matching class
            if group_code.split('.')[0] == current_division["code"]:
                current_group = {
                    "code": group_code,
                    "name": group_match.group(2),
                    "description": ""
                }
                for j in range(i + 1, min(i + 10, len(lines))):
                    desc_text = " ".join(lines[j : j + 3])
                    if "This group includes" in desc_text:
                        current_group["description"] = (
                            desc_text.split("This group includes")[1]
                            .split("\n")[0]
                            .strip()
                        )
                        break

        # Match class
        elif class_match := re.match(class_pattern, line):
            class_code = class_match.group(1)
            if len(class_code) == 5 and class_code[2] == "." and class_code not in processed_codes:
                division_code = class_code.split('.')[0]
                group_code = class_code[:4]
                
                # Important: Update division and group if needed based on the class code
                if division_code != current_division["code"]:
                    current_division = {
                        "code": division_code,
                        "name": "",
                        "description": ""
                    }
                
                if group_code != current_group["code"]:
                    current_group = {
                        "code": group_code,
                        "name": "",
                        "description": ""
                    }
                
                # Always process if we have a section
                if current_section["code"]:
                    activity = {
                        "section_code": current_section["code"],
                        "section_name": current_section["name"],
                        "section_description": current_section["description"],
                        "division_code": division_code,
                        "division_name": current_division["name"],
                        "division_description": current_division["description"],
                        "group_code": group_code,
                        "group_name": current_group["name"],
                        "group_description": current_group["description"],
                        "class_code": class_code,
                        "class_name": class_match.group(2),
                        "class_description": "",
                        "included_activities": [],
                        "excluded_activities": []
                    }

                    # Process includes/excludes
                    j = i + 1
                    mode = None
                    current_activity = None

                    while j < len(lines) and j < i + 50:
                        next_line = lines[j].strip()

                        if (re.match(class_pattern, next_line) and 
                            len(next_line.split()[0]) == 5) or next_line.startswith("#"):
                            break

                        if "This class includes:" in next_line:
                            mode = "includes"
                        elif "This class excludes:" in next_line:
                            mode = "excludes"
                        elif not next_line:
                            j += 1
                            continue

                        if mode:
                            if next_line.startswith("-"):
                                current_activity = next_line.lstrip("- ").rstrip(":")
                                if mode == "includes":
                                    activity["included_activities"].append({
                                        "activity": current_activity,
                                        "subactivities": [],
                                    })
                                else:
                                    activity["excluded_activities"].append({
                                        "activity": current_activity,
                                        "subactivities": [],
                                    })
                            elif next_line.startswith("*") and current_activity:
                                subactivity = next_line.lstrip("* ").strip()
                                if mode == "includes":
                                    activity["included_activities"][-1]["subactivities"].append(subactivity)
                                else:
                                    activity["excluded_activities"][-1]["subactivities"].append(subactivity)

                        j += 1

                    activities.append(activity)
                    processed_codes.add(class_code)

        i += 1

    # Sort activities by class code for consistent ordering
    activities.sort(key=lambda x: x["class_code"])
    
    return activities


def validate_nace_activities(activities):
    """
    Validates the extracted NACE activities data structure for completeness and accuracy.

    This function performs validation checks on the extracted NACE Rev.2 activity codes
    by comparing against expected totals and structure. It verifies:
    - Total number of activity classes (should be 615)
    - Number of unique sections (should be 21, A-U)
    - Number of unique divisions (should be 88)
    - Number of unique groups (should be 272)
    - Distribution of classes across sections

    Args:
        activities (list): List of dictionaries containing parsed NACE activities data.
                         Each dict should have section_code, division_code, group_code,
                         and class_code fields.

    Returns:
        bool: True if validation passes (615 total classes found), False otherwise.

    Prints:
        Detailed validation statistics including:
        - Total activities found vs expected
        - Breakdown of unique codes at each level
        - Distribution of classes per section
    """
    # Count total activities
    total_classes = len(activities)

    # Get unique counts at each level
    sections = set(a["section_code"] for a in activities)
    divisions = set(a["division_code"] for a in activities)
    groups = set(a["group_code"] for a in activities)
    classes = set(a["class_code"] for a in activities)

    print(f"Total activities extracted: {total_classes}")
    print("Expected activities: 615")
    print("\nBreakdown:")
    print(f"Sections: {len(sections)} - {sorted(sections)}")  # Should be 21 (A-U)
    print(
        f"Divisions: {len(divisions)} - First 5: {sorted(divisions)[:5]}"
    )  # Should be 88
    print(f"Groups: {len(groups)} - First 5: {sorted(groups)[:5]}")  # Should be 272
    print(f"Classes: {len(classes)} - First 5: {sorted(classes)[:5]}")  # Should be 615

    # Print distribution of classes per section
    print("\nClasses per section:")
    section_counts = {}
    for activity in activities:
        section = activity["section_code"]
        section_counts[section] = section_counts.get(section, 0) + 1

    for section in sorted(section_counts):
        print(f"Section {section}: {section_counts[section]} classes")

    return total_classes == 615


def split_nace_by_sections(text):
    """
    Splits NACE document into sections and returns list of section objects.

    Args:
        text (str): Full NACE document text

    Returns:
        list: List of dicts with structure:
            {
                "name": "Section X",
                "content": "... section content ..."
            }
    """
    # More flexible pattern - allow any whitespace and any dash-like character
    section_pattern = r"^# Section [A-Z][ \t]*[–—-]"

    # Split text into lines
    lines = text.split("\n")

    # Initialize variables
    sections = []
    current_section = None
    current_content = []

    # Process line by line
    for line in lines:
        line = line.strip()
        # Check if line starts a new section
        if re.match(section_pattern, line):
            # Save previous section if exists
            if current_section:
                sections.append({
                    "name": current_section,
                    "content": "\n".join(current_content),
                })

            # Start new section - handle various dash types
            for separator in ['–', '—', '-']:  # Try different dash types
                if separator in line:
                    current_section = line.split(separator)[0].strip()
                    break
            current_content = [line]

            # Debug print
            print(f"Found section: {current_section}")  # You can remove this after debugging

        # Add line to current section
        elif current_section:
            current_content.append(line)

    # Add final section
    if current_section and current_content:
        sections.append({
            "name": current_section,
            "content": "\n".join(current_content),
        })

    return sections


def write_section_files(sections, output_dir="data/sections"):
    """
    Writes each section to a separate markdown file using pathlib.
    
    Args:
        sections (list): List of section objects
        output_dir (pathlib.Path): Directory to write files to
    """
    # Convert string to Path if needed
    output_dir = pathlib.Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write each section to a file
    for section in sections:
        # Create filename from section name (e.g., "Section A" -> "section_a.md")
        filename = section["name"].lower().replace("Section ", "") + ".md"
        filepath = output_dir / filename
        
        # Write content to file
        filepath.write_text(section["content"], encoding="utf-8")
        
        print(f"Written: {filepath}")
