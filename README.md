# COMP4321 Project
UST COMP4321 Search Engine Project

## Assumption
- Web crawler written in Python 3.11.5
- SQLite database is used to store all data crawled
- Children of the webpage includes all presented webpage URL in the webpage, no matter if the link redirects to the predecessor of the webpage or not.
- Phrasal keywords from webpages contains only 2-3 single words
- `extract_keywords_from_text` and `get_ranked_phrases` function from `rake-nltk` are used to extract phrasal keywords from webpages (For details, please visit `extract_keywords` function from `server/utils.py`)
- `PorterStemmer` from `nltk` is used to stem single keywords from webpages (For details, please visit `extract_keywords` function from `server/utils.py`)

## Server Setup
- Go to `server` folder by running `cd server` in command line
- Run `pip install -r requirements.txt` in command line to install necessary libraries and packages.
- Run `spider.py` to crawl 300 pages and computing PMI and PageRank for webpage crawled (bounus features). Normal crawling takes around 1 minute while bonus features takes several minutes.
- Run `uvicorn main:app --reload` to start the server.
- Record the server URL, which will be used in client setup.

## Client Setup
- Install Node.js and Next.js.
- Go to `client` folder by running `cd client` in command line.
- Open `utils/api.ts` file and replace `api_url` constant with the server URL.
- Run `npm run dev` and click on the URL in the command line to view the webpage (in developer mode).

### Parameters
Parameters can be adjusted in the bottom `if __name__ == '__main__':` part in `server/spider.py` to alter the `spider_result.txt` output. This includes:
- `create_database.restore`: Set if all database tables have to be dropped before running
- `bfs_crawl.remove_cyclic_relationship`: Set if remove all predecessor links in the child links retrieved in webpages
- `bfs_crawl.max_page`: Set the maximum number of webpage to be crawled
- `write_webpage_infos.write_parent`: Set if parent links of webpages has to be included in `spider_result.txt`
- `write_webpage_infos.limit`: Set the number of webpages to be included in `spider_result.txt`
- `write_webpage_infos.relationship_limit`: Set the maximum parent links and child links to be included for each webpages in `spider_result.txt`
- `write_webpage_infos.keyword_limit`: Set the maximum title keywords and body kewords and their frequencies to be included for each webpages in `spider_result.txt`

## Library Used
- `nltk` for text tokenization and stemming
- `rake-nltk` for phrasal keyword extraction
- `sqlite3` database for storing web crawling results
- `sqlalchemy` for accessing and manipulating with database
- `requests` for requesting webpage data
- `beautifulsoup4` for parsing webpage content

## Crawler File Description
- `server/utils.py`: Python file containing utility functions
- `server/stopwords.txt`: Text file storing stopwords to be removed while crawling and retrieval
- `server/spider.py`: Python file for web crawling and store to database
- `server/db/schemas.py`: Python file defining the schemas of database
- `server/db/database.py`: Python file containing functions interacting with the database, including inserting, updating and retrieving data
- `server/db/project.db`: SQLite database file for storing crawled data

## Database Schemas
All database schemas are defined in `server/db/schemas.py`.

### Entity Relationship Diagram
![ER Diagram](er_diagram.jpeg)

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

## Supporting Structures

### URL ⇄ Page-ID Mapping

-   Implemented via the **Webpage** table's **url** and **webpage_id**
    fields.

-   Lookup Process:

    -   For a given URL, query the **Webpage** table to retrieve its
        **webpage_id**.

    -   For a given **webpage_id**, retrieve the URL from the same
        table.

### Word ⇄ Word-ID Mapping

-   Implemented via the **Keyword** table's **word** and **word_id**
    fields.

-   Lookup Process:

    -   For a stemmed keyword, query the **Keyword** table to retrieve
        its **word_id**.

    -   For a given **word_id**, retrieve the original stemmed keyword.

## Indexing Workflow

### Crawling

-   BFS crawler fetches pages and populates the **Webpage** and
    **Relationship** tables.

-   Cyclic links are handled by checking **is_crawled** and
    **is_active** flags.

### Keyword Extraction

-   Stop words are removed, and remaining words are stemmed.

-   Phrasal keywords (2-3 words) are extracted using RAKE.

### Indexing

-   Keywords are stored in the **Keyword** table.

-   Frequencies and locations (title/body) are recorded in the
    **Index** table.