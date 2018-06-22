# NYC OpenStreetMap

This is the Data Wrangling of NYC OpenStreetMap data. The map area consists of Manhattan, New York, NY, USA. It is my project of Udacity Data Analyst Nanodegree Program Project: Wrangle OpenStreetMap Data.

## Introduction
In the report, I will wrangle the OpenStreetMap data of Manhattan, New York, United States.

First, I will audit the dataset to find out if there is any problem within the dataset that needs to be fixed. Next, I will use SQL queries to obtain an overview of the dataset. Last, I will provide some ideas to further improve and analyze the dataset.

## Map Area
New York (Manhattan), New York, United States I've obtained a custom map that includes the Manhattan borough of New York City through Mapzen. I have chosen this area because I am living in Jersey City and I use to visit NYC during my weekends. I would like to find out if I will be able to find some interesting facts about the city I love by investigating the OpenStreetMap data.

## Overview Statistics of the Dataset

**File Size**
| File Name                | File Size (MB) |
|--------------------------|----------------|
| NYC.osm                  | 477.565        |
| manhattan.db             | 280.372        |
| nodes.csv                | 169.271        |
| nodes_tags.csv           |  10.277        |
| ways.csv                 |  21.063        |
| ways_tags.csv            |  64.331        |
| ways_nodes.csv           |  54.527        |

**Number of Unique Users:**    2163

**Number of Nodes:**           1884748

**Number of Ways:**            320048

**Number of Subway Stations:** 378

**Top 10 cuisines**
| | Cuisine  Types|	Num|
|-|---------------|----|
|0| italian	      | 134|
|1| pizza	      |  88|
|2| american	  |  85|
|3| mexican	      |  79|
|4| chinese	      |  62|
|5| japanese	  |  46|
|6| french	      |  44|
|7| indian	      |  43|
|8| thai	      |  43|
|9| burger	      |  42|

**Top 10 cafes**

| | Cafe Shop Names	            | Num|
|-|-----------------------------|----|
|0|	Starbucks	                | 114|
|1|	Dunkin' Donuts	            |  33|
|2|	Starbucks Coffee            |  24|
|3|	Le Pain Quotidien           |  13|
|4|	Cafe Grumpy	                |   4|
|5|	Dunkin Donuts	            |   4|
|6|	Piccolo Cafe	            |   4|
|7|	Pinkberry	                |   4|
|8|	Pret a Manger	            |   4|
|9|	The Coffee Bean & Tea Leaf	|   4|

## Other Ideas about the Datasets
**User Ratings**
One piece of crucial information missing from the dataset is the ratings of places. By incorporating a node tag with user ratings can help user answer questions such as "What are some of the best restaurants in town?", "Which doctor in my neighborhood should I go to?".

I can think of two ways to gather this rating information:
1. User contribution. It's easy to implement this, but the problem is the number of active contributing users for our OpenStreetMap data is low, so the ratings will not have a sample size large enough to be representative.
2. Aggregate from other web sources. This approach can get good ratings information fast and more accurate than the first approach. But the problem is how to get permissions from other sources to provide their rating data, not to mention that those sources are probably OpenStreetMap's direct and indirect competitors.

## Conclusion
This analysis of OpenStreetMap Manhattan extract has helped me dig into the problems and inconsistency of the OpenStreetMap data. After cleaning zip codes, address types and phone numbers of this dataset, I imported this dataset into a SQL database for further exploration. I obtained some statistics and answered some questions using SQL queries, but I also found some questions that couldn't be anwsered without incorporating user ratings into our dataset.

I really liked this project, and if all our Udacians can incorporate our cleaned data and other ideas to improve the dataset of OpenStreepMap, I believe it will make OpenStreepMap cleaner and more popular.