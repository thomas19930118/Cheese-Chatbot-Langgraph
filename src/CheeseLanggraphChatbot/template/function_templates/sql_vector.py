import json

function_list = [
    {
        "type": "function",
        "function": {
            "name": "determine_sql_or_vector_or_nodb_or_parallel",
            "description": "This function is using conversation between user and assistant as input and determine whether using sql is good or using vectordb is good or parallel search with sql and vector is good or it is good without db.",
            "parameters": {
                "type": "object",
                "properties": {
                    "which_db": {
                        "type": "string",
                        "enum": ["sql", "vector", "parallel", "nodb"],
                        "description": "If using SQL is good this property returns 'sql', and if using vectordb is good return 'vector', and if using parallel search is good with sql and vector return 'parallel', and if information is not provided and it is a common dialogue like greetings, return 'nodb'"
                    }
                },
                "required": ["which_db"]
            }
        }
    }
]

sql_vector_tool = json.loads(json.dumps(function_list))