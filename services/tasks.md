## july 26
Update the code base to read in the first page of results from techccrunch.
- scrape the article title
   - create a new agents directory ✅
   - abstract the code from `	process_the_scrape.py` and name it 'is_funding_agent.py`:x 
- ask the agent if the title is in fact about funding ✅
- if it is about funding, scrape it, ask another agent to structure the data, then write it

YES, finished above. Now, I need to see the results of the scrape (make sure its tight and keep track of file artificats resulting from scrape)
- i need to write to the db after the scrape  ✅
- abstract out the agent `enhacne_With_ai` which is used to structure the data  ✅
- keep clean code along the way !!:x

NOW lets work on the rag_agent

GOAL
(1) Lets get the Streamlit app up and running. 

   - Afterwards, we can impl each of the event driven actions on the agent (scrape, embeded, etc)

