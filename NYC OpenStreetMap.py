
# coding: utf-8

# # NYC OpenStreetMap

# **Project:** Wrangle OpenStreetMap Data
# 
# **Submitted by:** Bharath Kumar

# ## 1 Introduction

# In the report, I will wrangle the OpenStreetMap data of Manhattan, New York, United States.
# 
# First, I will audit the dataset to find out if there is any problem within the dataset that needs to be fixed. Next, I will use SQL queries to obtain an overview of the dataset. Last, I will provide some ideas to further improve and analyze the dataset.

# ### Map Area
# 
# New York (Manhattan), New York, United States I've obtained [a custom map](NYC.osm) that includes the Manhattan borough of New York City through Mapzen. I have chosen this area because I am living in Jersey City and I use to visit NYC during my weekends. I would like to find out if I will be able to find some interesting facts about the city I love by investigating the OpenStreetMap data.

# In[1]:


OSM_FILE = 'NYC.osm'

from collections import defaultdict
import re
import pprint
import datetime as dt
import csv
import pandas as pd

import xml.etree.cElementTree as ET
import schema
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, ForeignKey


# ## 2 Auditing and Problems Encountered in the Map

# ### 2.1 Map Extracts Included Surrounding Areas and Inconsistent Zip Codes
# 
# **Examples: "10001", "10001-2062", "NY 11106", "New York, NY 10065"**
# 
# Because of the way in which the data extract is generated, areas that surrounding Manhattan are also included in this dataset. I suspect that the dataset includes parts of other New York City boroughs and some parts of New Jersey. To confirm this, I will look at the zip codes distribution of our dataset. 
# 
# Because there is inconsistency in the zip code formats, I will fix that before aggregate the zip codes. I will use a update_zip_code function to update the zip code formats to a 5-digit zip code format (e.g. "10001") for more consistent queries. If more than one zip code is listed for any given address,I will keep only the first one.

# In[2]:


# ================================================== #
#      Helper Functions for Auditing Zip Codes       #
# ================================================== #
def is_zip_code(elem):
    return (elem.attrib['k'] == 'addr:postcode')

def audit_zip_codes(zip_code_formats, zip_codes_distribution, zip_code):
    '''Audit zip codes
    
    This function updates two dictionaries showing the distribution of zip code formats
    and the distribution of zip code areas.
    
    Arg:
    zip_code_formats: A dictionary of zip code format: counts of zip code in that format
    zip_codes_distribution: A dictionary of zip code area name: counts of zip codes in that area
    zip_code: A zip code
    '''
    
    # Audit zip code formats
    # Convert any digit to an 'X' sign (e.g. 'NY 10001' becomes 'NY XXXXX')
    zip_code_format = re.sub('\d', 'X', zip_code)
    zip_code_formats[zip_code_format] += 1
    
    # Audit zip code areas
    # Convert zip code to its corresponding area name
    zip_code = re.sub('\D', '', zip_code) # Only look at zip code digits
    if re.match(r'^10[0-2]', zip_code): # Manhattan: 100XX, 101XX, 102XX
        zip_codes_distribution['Manhattan'] += 1
    elif re.match(r'^104', zip_code): # Bronx: 104XX
        zip_codes_distribution['Bronx'] += 1
    elif re.match(r'^112', zip_code): # Brooklyn: 112XX
        zip_codes_distribution['Brooklyn'] += 1
    elif re.match(r'^103', zip_code): # Staten Island: 103XX
        zip_codes_distribution['Staten Island'] += 1
    elif re.match(r'^11', zip_code): # Queens: 11XXX
        zip_codes_distribution['Queens'] += 1
    elif re.match(r'^07', zip_code): # New Jersey: 07XXX
        zip_codes_distribution['New Jersey'] += 1
    else:
        zip_codes_distribution['Other'] += 1
        
# ================================================== #
#         Functions for Updating Zip Codes           #
# ================================================== #
def update_zip_code(zip_code):
    '''Update zip code format to five digits only
    
    This funtion is used to correct inconsistent zip code formats during XML to csv conversion
    
    Arg:
    zip_code: a raw zip code from the dataset
    
    Return:
    zip_code: an updated zip code consists with 5 digits 
    '''
    # Update zip code format to five digits 'XXXXX'
    if re.search(r';', zip_code):
        zip_code = zip_code.split(';')[0] # Keep the first zip code for 'XXXXX;XXXXX' format
    digits = re.sub('\D', '', zip_code)
    if len(digits) ==  5: 
        zip_code = digits # 'XXXXX' stays the same
    elif len(digits) == 9: 
        zip_code = digits[:5] # 'XXXXX-XXXX' only keeps the first 5 digits
    return zip_code


# ## 2.2 Inconsistent Street Types
# 
# **Examples: "Street", "street", "St", "St."**
# 
# The street types of addresses in the dataset are inconstistent in terms of abbreviations and lower/upper cases. First by auditing the street types I will build a mapping to map different types of street type abbreviations and lower/upper cases to non-abbreviated street types with first letter capitalized (e.g. "Street", "Avenue"). Then I will use a update_name function to update the better updated addresses during XML to csv conversion.

# In[3]:


# ================================================== #
#     Helper Functions for Auditing Street Types     #
# ================================================== #
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Expected good street types
expected = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Court', 
            'Place', 'Square', 'Lane', 'Road', 'Trail', 
            'Parkway', 'Commons', 'Broadway', 'Highway', 'Crescent', 
            'Park', 'Plaza', 'Terrace', 'Way', 'Walk', 
            'East', 'South', 'West', 'North', 'Alley', 
            'Circle', 'Center']

# Mapping from bad street types to good street types
mapping = { 'Americas\n': 'Americas',
            'ave': 'Avenue',
            'avenue': 'Avenue',
            'Ave': 'Avenue',
            'Ave.': 'Avenue',
            'Avene': 'Avenue',
            'Aveneu': 'Avenue',
            'Blv': 'Boulevard',
            'Blvd': 'Boulevard',
            'Broadway.': 'Broadway',
            'Ctr': 'Center',
            'Plz': 'Plaza',
            'Rd.': 'Road',
            'S': 'South',
            'st': 'Street',
            'St': 'Street',
            'St.': 'Street',
            'Steet': 'Street',
            'street': 'Street',
            'Streeet': 'Street',
            'ST': 'Street'
            }

def is_street_name(elem):
    return (elem.attrib['k'] == 'addr:street')

def audit_street_type(street_types, street_name):
    '''Audit street type
    
    This function updates the dictionary showing the street type and its corresponding
    set of street names with that street type.
    
    Arg:
    street_types: A dictionary of street type: a set of street names wtih that street type
    street_name: A street name
    '''
    
    matched = street_type_re.search(street_name)
    if matched:
        street_type = matched.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            
# ================================================== #
#        Functions for Updating Street Types         #
# ================================================== # 
# Funtion to be used to correct inconsistent street types during XML to csv conversion
def update_name(name, mapping):
    '''Update street name to good format
    
    This funtion is used to correct inconsistent street name formats during XML to csv conversion
    
    Arg:
    name: a raw street name from the dataset
    mapping: a dictionary of bad street type: good street type
    
    Return:
    name: an updated street name of full street type name with the first letter capitalized
    '''
    street_kind = name.split(' ')[-1] # Last word of address is the street type
    if street_kind in mapping:
        street_kind_better = mapping[street_kind]
        name = name.replace(street_kind, street_kind_better)
    return name


# ## 2.3 Inconsistent Phone Number Formats
# 
# **Examples: "(212) 333-3100", "+1 212 228-7732", "2122391222", "718-731-3100"**
# 
# The phone number formats in the dataset are also inconsistent. I will update the phone number format to +1-XXX-XXX-XXXX by using a update_phone_number function, and later I will use this during XML to csv conversion. If more than one phone number is listed for any given address, I will only keep the first one for more consistent queries.

# In[4]:


# ================================================== #
#    Helper Functions for Auditing Phone Numbers     #
# ================================================== #            
def is_phone(elem):
    return (elem.attrib['k'] == "phone" or elem.attrib['k'] == "contact:phone")

def audit_phone_number_formats(phone_number_formats, phone_number):
    '''Audit phone numbers
    
    This function updates a dictionary showing the distribution of phone number formats.
    
    Arg:
    phone_number_formats: A dictionary of phone number format: counts of phone numbers of that format
    phone_number: A phone number
    '''
    
    # Convert any digit to an 'X' sign (e.g. '(212) 333-3100' becomes '(XXX) XXX-XXXX')
    phone_number_format = re.sub('\d', 'X', phone_number)
    phone_number_formats[phone_number_format] += 1

# ================================================== #
#       Functions for Updating Phone Numbers         #
# ================================================== # 
# Funtion to be used to correct inconsistent phone number formats during XML to csv conversion
def update_phone_number(phone_number):
    '''Update phone number format to '+1-XXX-XXX-XXXX'
    
    This funtion is used to correct inconsistent phone number formats during XML to csv conversion
    
    Arg:
    phone_number: a raw phone number from the dataset
    
    Return:
    phone_number: an updated phone number with the format '+1-XXX-XXX-XXXX'
    
    '''
    # Keep the first phone number if more than one is present
    if re.search(r';', phone_number):
        phone_number = phone_number.split(';')[0] # Phone numbers are separated by ';'
    elif re.search(r'/', phone_number):
        phone_number = phone_number.split('/')[0] # Phone numbers are separated by '/'
    
    digits = re.sub('\D', '', phone_number)
    if len(digits) == 11: # 1XXXXXXXXXX
        return '+' + digits[0] + '-' + digits[1:4] + '-' + digits[4:7] + '-' + digits[7:]
    elif len(digits) == 10: # XXXXXXXXXX
        return '+1' + '-' + digits[:3] + '-' + digits[3:6] + '-' + digits[6:]
    elif len(digits) == 12: # 01XXXXXXXXXX
        return '+' + digits[1] + '-' + digits[2:5] + '-' + digits[5:8] + '-' + digits[8:]
    elif len(digits) == 13: # 001XXXXXXXXXX
        return '+' + digits[2] + '-' + digits[3:6] + '-' + digits[6:9] + '-' + digits[9:]
    else:
        return phone_number


# In[6]:


# ================================================== #
#                      Auditing                      #
# ================================================== # 

def audit(osmfile):
    osm_file = open(osmfile, 'r', encoding="utf8")
    
    street_types = defaultdict(set)
    phone_number_formats = defaultdict(int)
    zip_codes_distribution = defaultdict(int)
    zip_code_formats = defaultdict(int)
    
    for event, elem in ET.iterparse(osm_file, events=('start',)):

        if elem.tag == 'node' or elem.tag == 'way':
            for tag in elem.iter('tag'):
                
                # Audit zip codes
                if is_zip_code(tag):
                    audit_zip_codes(zip_code_formats, zip_codes_distribution, tag.attrib['v'])
                    
                # Audit street types
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                    
                # Audit phone numbers
                if is_phone(tag):
                    audit_phone_number_formats(phone_number_formats, tag.attrib['v'])
                    
    osm_file.close()
    
    print('==================================================')
    print('Auditing zip codes:')
    print('==================================================')
    print('Zip code formats:')
    pprint.pprint(dict(zip_code_formats))
    print()
    print('--------------------------------------------------')
    print('Zip code distribution:')
    pprint.pprint(dict(zip_codes_distribution))
    print()
    
    print('==================================================')
    print('Auditing street types:')
    print('==================================================')
    pprint.pprint(dict(street_types))
    print()
    
    print('==================================================')
    print('Auditing phone number formats:')
    print('==================================================')
    pprint.pprint(dict(phone_number_formats))

audit(OSM_FILE)


# ## 3 Overview of the Data

# ### 3.1 Importing Data into SQL Database
# 
# I will start by parsing the elements in the XML file and update zip codes, street types and telephone numbers, then transform these elements from document format to
# tabular format and eventually into csv files. After that, I will import these csv files into a SQL database as tables for analysis.

# In[7]:


OSM_PATH = OSM_FILE

NODES_PATH = 'nodes.csv'
NODE_TAGS_PATH = 'nodes_tags.csv'
WAYS_PATH = 'ways.csv'
WAY_NODES_PATH = 'ways_nodes.csv'
WAY_TAGS_PATH = 'ways_tags.csv'

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]') # Tags with problematic characters

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# ================================================== #
#               Helper Functions                     #
# ================================================== #

def shape_element_attribs(element, attr_fields):
    '''Convert an XML element to a dictionary "node" or "way", with keys in attr_fields'''
    attribs = {}
    element_attribs = element.attrib
    for attr_field in attr_fields:
        attribs[attr_field] = element_attribs[attr_field]
    return attribs

def shape_element_tags(element, problem_chars, default_tag_type, id):
    '''Convert all tags of an XML element to a dictionary "node_tags" or "way_tags"'''
    tags = []
    element_tags = element.findall('tag')
    if element_tags:
        for element_tag in element_tags:
            k_value = element_tag.get('k')
            v_value = element_tag.get('v')
            
            # If the tag "k" value contains problematic characters, the tag should be ignored
            if not re.search(problem_chars, k_value):
                
                tag ={}
                tag['id'] = id 
                
                # If the tag "k" value contains a ":" 
                # the characters before the ":" should be set as the tag type
                # and characters after the ":" should be set as the tag key
                # If there are additional ":" in the "k" value
                # they should be ignored and kept as part of the tag key.
                # e.g. <tag k="addr:street:name" v="Lincoln"/> should be turned into
                # {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}
                
                if ':' in k_value:
                    tag['type'], tag['key'] = k_value.split(':', 1)
                else:
                    tag['key'] = k_value
                    tag['type'] = default_tag_type
                    
                if k_value == 'addr:street':
                    tag['value'] = update_name(v_value, mapping) # Update the street type
                elif k_value == "phone" or k_value == 'contact:phone':
                    tag['value'] = update_phone_number(v_value) # Update the phone number format
                else:
                    tag['value'] = v_value
                
                tags.append(tag)
    return tags

def shape_element_way_nodes(element, id):
    '''Convert an XML element of "way" into a dictionary "way_nodes"'''
    way_nodes = []
    way_nodes_tags = element.findall('nd')
    for index, way_node_tag in enumerate(way_nodes_tags):
        way_node = {}
        way_node['id'] = id
        way_node['node_id'] = way_node_tag.get('ref')
        way_node['position'] = index
        way_nodes.append(way_node)
    return way_nodes

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    '''Clean and shape node or way XML element to a dictionary'''

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        node_attribs = shape_element_attribs(element, node_attr_fields)
        node_id = node_attribs['id']
        tags = shape_element_tags(element, problem_chars, default_tag_type, node_id)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        way_attribs = shape_element_attribs(element, way_attr_fields)
        way_id = way_attribs['id']
        tags = shape_element_tags(element, problem_chars, default_tag_type, way_id)
        way_nodes = shape_element_way_nodes(element, way_id)           
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

def get_element(osm_file, tags=('node', 'way', 'relation')):
    '''Yield element if it is the right type of tag'''

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    '''Iteratively process each XML element and write to csv(s)
    
    Arg:
    file_in: an OSM XML file to be converted
    '''

    with open(NODES_PATH, 'w', encoding='utf-8') as nodes_file,          open(NODE_TAGS_PATH, 'w', encoding='utf-8') as nodes_tags_file,          open(WAYS_PATH, 'w', encoding='utf-8') as ways_file,          open(WAY_NODES_PATH, 'w', encoding='utf-8') as way_nodes_file,          open(WAY_TAGS_PATH, 'w', encoding='utf-8') as way_tags_file:

        nodes_writer = csv.DictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = csv.DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = csv.DictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = csv.DictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = csv.DictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

process_map(OSM_PATH)


# In[8]:


# ================================================== #
#                    Database                        #
# ================================================== #

engine = create_engine('sqlite:///manhattan.db') # Database connection

# Create tables
metadata = MetaData()

nodes = Table('nodes', metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('lat', Float),
    Column('lon', Float),
    Column('user', String),
    Column('uid', Integer),
    Column('version', String),
    Column('changeset', Integer),
    Column('timestamp', String)
)

nodes_tags = Table('nodes_tags', metadata,
    Column('id', Integer, ForeignKey('nodes.id'), nullable=False),
    Column('key', String),
    Column('value', String),
    Column('type', String),
)

ways = Table('ways', metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', String),
    Column('uid', Integer),
    Column('version', String),
    Column('changeset', Integer),
    Column('timestamp', String)
)

ways_tags = Table('ways_tags', metadata,
    Column('id', Integer, ForeignKey('ways.id'), nullable=False),
    Column('key', String),
    Column('value', String),
    Column('type', String),
)

ways_nodes = Table('ways_nodes', metadata,
    Column('id', Integer, ForeignKey('ways.id'), nullable=False),
    Column('node_id', Integer, ForeignKey('nodes.id'), nullable=False),
    Column('position', Integer, nullable=False)
)

metadata.create_all(engine)

# Load csv files in chunks into Pandas DataFrames, then append them into SQLite database 
# https://plot.ly/python/big-data-analytics-with-pandas-and-sqlite/
# http://www.mapfish.org/doc/tutorials/sqlalchemy.html

def csv_to_db(csvfile, table):
    print('Processing {}'.format(csvfile))
    start = dt.datetime.now()
    chunksize = 200000
    j = 0
    for df in pd.read_csv(csvfile, chunksize=chunksize, iterator=True, encoding='utf-8'):
        j+=1
        print('{} seconds: completed {} rows'.format((dt.datetime.now() - start).seconds, j*chunksize))
        df.to_sql(table, engine, if_exists='append', index=False)

csv_to_db('nodes.csv', 'nodes')
csv_to_db('nodes_tags.csv', 'nodes_tags')
csv_to_db('ways.csv', 'ways')
csv_to_db('ways_tags.csv', 'ways_tags')
csv_to_db('ways_nodes.csv', 'ways_nodes')


# ### 3.2 Overview Statistics of the Dataset

# #### File Size
# 
# | File Name                | File Size (MB) |
# |--------------------------|----------------|
# | NYC.osm                  | 477.565        |
# | manhattan.db             | 280.372        |
# | nodes.csv                | 169.271        |
# | nodes_tags.csv           |  10.277        |
# | ways.csv                 |  21.063        |
# | ways_tags.csv            |  64.331        |
# | ways_nodes.csv           |  54.527        |

# #### Number of unique users

# In[9]:


sql_query = '''
SELECT COUNT(*) AS "Number of Unique Users" FROM
(SELECT uid FROM nodes 
UNION
SELECT uid FROM ways) nodes_ways_uids;
'''
df = pd.read_sql_query(sql_query, engine)
df


# #### Number of nodes

# In[10]:


sql_query = '''
SELECT COUNT(*) AS "Number of Nodes" FROM nodes
'''
df = pd.read_sql_query(sql_query, engine)
df


# #### Number of ways

# In[11]:


sql_query = '''
SELECT COUNT(*) AS "Number of Ways" FROM ways
'''
df = pd.read_sql_query(sql_query, engine)
df


# #### Number of subway stations
# New York is famous for its spanning subway network that connects the city together. I would like to know how many subway stations out of the total 422 stations are included in our extract.

# In[12]:


sql_query = '''
SELECT COUNT(*) AS "Number of Subway Stations" 
FROM nodes_tags 
WHERE value="New York City Subway";
'''
df = pd.read_sql_query(sql_query, engine)
df


# #### Top 10 cuisines
# New York is also the heaven for foodies with all kinds of cuisines from around the world. It is interesting to figure out what are the most popular cuisines in the city.

# In[13]:


sql_query = '''
SELECT value AS "Cuisine Types", COUNT(*) AS Num 
FROM nodes_tags 
JOIN (SELECT DISTINCT id FROM nodes_tags WHERE value="restaurant") nodes_ids
ON nodes_tags.id=nodes_ids.id
WHERE key="cuisine" 
GROUP BY value 
ORDER BY COUNT(*) DESC
LIMIT 10;
'''
df = pd.read_sql_query(sql_query, engine)
df


# #### Top 10 cafes
# New Yorkers cannot live without their coffee. By looking at the top 10 cafe shops with most locations, I found out there are other problems in the dataset, such as Starbucks has "Starbucks" and "Starbucks Coffee" two different naming conventions, also Dunkin' Donuts has "Dunkin' Donuts" and "Dunkin Donuts" two different names.

# In[14]:


sql_query = '''
SELECT value AS "Cafe Shop Names", COUNT(*) AS Num 
FROM nodes_tags 
JOIN (SELECT DISTINCT id FROM nodes_tags WHERE value="cafe") nodes_ids
ON nodes_tags.id=nodes_ids.id
WHERE key="name" 
GROUP BY value 
ORDER BY COUNT(*) DESC  
LIMIT 10;'''

df = pd.read_sql_query(sql_query, engine)
df


# ## 4 Other Ideas about the Datasets

# ### User Ratings
# One piece of crucial information missing from the dataset is the ratings of places. By incorporating a node tag with user ratings can help user answer questions such as "What are some of the best restaurants in town?", "Which doctor in my neighborhood should I go to?".
# 
# I can think of two ways to gather this rating information:
# 1. User contribution. It's easy to implement this, but the problem is the number of active contributing users for our OpenStreetMap data is low, so the ratings will not have a sample size large enough to be representative.
# 2. Aggregate from other web sources. This approach can get good ratings information fast and more accurate than the first approach. But the problem is how to get permissions from other sources to provide their rating data, not to mention that those sources are probably OpenStreetMap's direct and indirect competitors.

# ## 5 Conclusion
# 
# This analysis of OpenStreetMap Manhattan extract has helped me dig into the problems and inconsistency of the OpenStreetMap data. After cleaning zip codes, address types and phone numbers of this dataset, I imported this dataset into a SQL database for further exploration. I obtained some statistics and answered some questions using SQL queries, but I also found some questions that couldn't be anwsered without incorporating user ratings into our dataset.
# 
# I really liked this project, and if all our Udacians can incorporate our cleaned data and other ideas to improve the dataset of OpenStreepMap, I believe it will make OpenStreepMap cleaner and more popular.
