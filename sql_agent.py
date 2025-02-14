from textwrap import dedent
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import Engine, create_engine
from load_models import OPENAI_MODEL
from sql import list_tables, describe_table, run_sql_query

system_prompt = dedent("""
    You an AI agent are equipped with SQLite tools. Your goal is to help users interact with a SQLite database.'

    To run a SQL, follow the steps:
    1. first, run the `list_tables` tool to get a list of tables in the database.
    2. then, run the `describe_table` tool to get a description of the target tables) in the database.
    3. finally, construct the SQL statement and run the `run_sql` tool to run the SQL query on the database.
        
    When returning the results, please return the entire result
""")

@dataclass
class Dependencies:
    db_engine: Engine

class ResponseModel(BaseModel):
    detail: str = Field(name='Detail', description='The result of the query.')

agent = Agent(
    name='SQLite Agent',
    model=OPENAI_MODEL,
    system_prompt=[system_prompt],
    result_type=ResponseModel
)

@agent.tool
def list_tables_tool(ctx: RunContext) -> str:
    print('list_tables_tool called')
    """Use this function to get a list of table names in the database."""
    return list_tables(ctx.deps.db_engine)

@agent.tool
def describe_table_tool(ctx: RunContext, table_name: str) -> str:
    print('describe_table_tool called', table_name)
    """Use this function to get a description of a table in the database."""
    return describe_table(ctx.deps.db_engine, table_name)

@agent.tool
def run_sql_tool(ctx: RunContext, query: str, limit: int = 10) -> str:
    print('run_sql_tool called', query)
    """Use this function to run a SQL query on the database."""
    return run_sql_query(ctx.deps.db_engine, query, limit)

if __name__ == "__main__":
    db_engine = create_engine('sqlite:///./Chinook_Sqlite.sqlite')
    deps = Dependencies(db_engine=db_engine)

    response1 = agent.run_sync(
        'Add a new Artist called "Josh Smith"',
        deps=deps
    )

    response2 = agent.run_sync(
        'What was the last query called',
        deps=deps,
        message_history=response1.new_messages()
    )
    
    print(response2.data.detail)