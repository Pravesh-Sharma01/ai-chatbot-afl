import requests
from itertools import product
def call_planner_agent():
    # body = {
    #     "company_name_query": query
    # }
    body ={
   "session_id" : "123",
    "message" : "Show policies for customer CUST001"
}
 

    response = requests.post("http://127.0.0.1:8000/ask", json=body)

    print( response.json() )

call_planner_agent()