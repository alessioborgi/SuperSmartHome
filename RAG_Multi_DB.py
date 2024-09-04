# Install necessary packages
# pip install llama-index sqlalchemy duckdb duckdb-engine openai

import os
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI
import duckdb

# Step 1: Set up OpenAI API key
def load_openai_key():
    with open('oaikey.txt') as keyfile:
        oaikey = keyfile.read().strip()
    os.environ["OPENAI_API_KEY"] = oaikey
    return oaikey

# Step 2: Create a DuckDB database and load CSV data
def create_and_load_database():
    # Set up DuckDB in memory
    engine = create_engine('duckdb:///:memory:')
    metadata_obj = MetaData()

    # Define table schema for rooms
    room_tables = {
        'room_QRITA': './MQTT Client/Room MQTT Client/data/airQRITA.csv',
        'room_QFOYER': './MQTT Client/Room MQTT Client/data/airQFOYER.csv',
        'room_QDORO': './MQTT Client/Room MQTT Client/data/airQDORO.csv',
        'room_QHANS': './MQTT Client/Room MQTT Client/data/airQHANS.csv',
        'room_QMOMO': './MQTT Client/Room MQTT Client/data/airQMOMO.csv',
        'room_QROB': './MQTT Client/Room MQTT Client/data/airQROB.csv'
    }

    for room, file_path in room_tables.items():
        room_table = Table(
            room, metadata_obj,
            Column('timestamp', String, primary_key=True),
            Column('temperature', Float),
            Column('humidity', Float),
            Column('health', Integer),
        )
        metadata_obj.create_all(engine)

        # Load data from CSV and insert into DuckDB
        df_room = pd.read_csv(file_path)
        df_room.to_sql(room, con=engine, if_exists='replace', index=False)

    return engine

# Step 3: Define the SQLDatabase in LlamaIndex
def setup_llamaindex_sql_database(engine):
    # Create an OpenAI LLM instance
    llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")

    # Define the SQLDatabase to include all room tables
    sql_database = SQLDatabase(engine, include_tables=[
        "room_QRITA", "room_QFOYER", "room_QDORO", "room_QHANS", "room_QMOMO", "room_QROB"
    ])

    return llm, sql_database

# Step 4: Set up the Natural Language SQL Query Engine
def setup_query_engine(llm, sql_database):
    query_engine = NLSQLTableQueryEngine(llm=llm, sql_database=sql_database)
    return query_engine

# Step 5: Query the SQL database with natural language
def run_query(query_engine, query):
    response = query_engine.query(query)
    print("Query Result: ")
    print(response)

# Main function to tie everything together
def main():
    # Load OpenAI API key
    load_openai_key()

    # Create and load data into DuckDB database
    engine = create_and_load_database()

    # Set up LlamaIndex SQLDatabase
    llm, sql_database = setup_llamaindex_sql_database(engine)

    # Set up the Natural Language SQL Query Engine
    query_engine = setup_query_engine(llm, sql_database)

    # Example query - fetch health values from QRITA during the first day
    query = "What are the health values in QRITA room during the first day?"
    run_query(query_engine, query)

    # Example query - fetch temperature data from QFOYER for the last 24 hours
    query = "What is the air temperature in QFOYER room during the last 24 hours?"
    run_query(query_engine, query)

if __name__ == "__main__":
    main()