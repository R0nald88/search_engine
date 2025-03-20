# COMP4321 Project
UST COMP4321 Search Engine Project

## Installation
- Run `pip install -r requirements.txt` in command line to install necessary libraries and packages.
- Run `server/spider.py` and `spider_result.txt` will be generated in root directory.

### Library Used
- `nltk` for text tokenization and stemming
- `rake-nltk` for phrasal keyword extraction
- `sqlite` database for storing web crawling results
- `sqlalchemy` for accessing and manipulating with database
- `requests` for requesting webpage data
- `beautifulsoup4` for parsing webpage content

## Database Schemas
All database schemas are defined in `server/db/schemas.py`.

### Webpage Table
Storing webpage data and mapping between webpage ID and URL. Attributes include:
- `webpage_id`: ID of webpages. Primary key.
- `url`: URL to webpage.
- `title`: Webpage title.
- `last_modified_date`: Data of "Last-Modified" field in webpage header.
- `size`: Data of "Content-Length" field in webpage header.
- `is_active`: Check if the webpage is active. Broken link, uncrawled, safe-deleted or any webpage with error while requesting are marked as inactive and would not be shown in searching results.
- `is_crawled`: Check if the webpage is crawled. Uncrawled webpages are stored for recording the parent-child relationship in Relationship table and whould not be shown in searching results.

### Keyword Table
Storing keywords extracted from webpage and mapping between keyword ID and keywords. Attributes include:
- `word_id`: ID of keyword. Primary key.
- `word`: Keyword string.

### Relationship Table
Recording parent-child relationship between webpages. Attributes include:
- `relate_id`: ID of relationship composed of `parent_id` and `child_id`. Primary key.
- `parent_id`: ID of parent webpage. Foreign key from Webpage table.
- `child_id`: ID of child webpage. Foreign key from Webpage table.
- `is_active`: Check if current relationship is active. Set to false when the relationship is not found after crawling at least twice.

### Index Table
Storing the data of keywords in webpages that are used during searching. Used as forward or inverted index files. Attributes include:
- `index_id`: Unique ID composed of `webpage_id` and `word_id`. Primary key.
- `webpage_id`: ID of webpage. Foreign key from Webpage table.
- `word_id`: ID of keyword. Foreign key from Keyword table.
- `frequency`: Frequency of the keyword in the webpage. Zero frequency is seen as safe-deleted and would not use in searching.
- `is_title`: Check if current keyword is retrieved from page body or title.