sql_vector = """
You need to select one proper database, Pinecone VectorDB or MySQL Database to gather information that related to following query.
And you need to use both two search-sql and vector search with parrel.
And for the common dialogue like greetings and the information which is not related to cheese, We don't need to use the DB.
But use parral search extremly rare. So, almose use sql query. 
for popularity(ex: what is the most popular cheese?), use parrel search.

The query is as follows.
{query}

Here is the original conversation.
{conversation}

Here is SQL Query that is used to create table.
```
CREATE TABLE IF NOT EXISTS cheese_data (
    id INT PRIMARY KEY,
    showimage VARCHAR(255),
    name VARCHAR(255),
    brand VARCHAR(255),
    category VARCHAR(255),
    itemcount_case VARCHAR(255),
    itemcount_each VARCHAR(255),
    dimension_case VARCHAR(255),
    dimension_each VARCHAR(255),
    weight_case DECIMAL(10,2),
    weight_each DECIMAL(10,2),
    image TEXT,
    related VARCHAR(255),
    price_case DECIMAL(10,2),
    price_each DECIMAL(10,2),
    price_per_lb DECIMAL(10,2),
    sku VARCHAR(255),
    wholesale VARCHAR(255),
    out_of_stock BOOLEAN,
    product_url VARCHAR(255),
    priceorder INT,
    popularityorder INT
)
```
If a customer asks, "How many different kinds of cheese products do you have in total?", respond with the total number of different cheese categories available in your store. If you don't have an actual list, give a reasonable example number and mention that it's an approximate count of cheese varieties and cheese-based products (like spreads, blocks, slices, etc.). Always make sure your answer is directly about cheese products.
"""