### Implementation Details: 

1 - Build A loop to received the Feishu message event: based on the testing file demonstrated to receive message from websocket: test/test_event_subscription.py
    - Check the date type of the event, only to be message event
    - print them message only
2 - create single langchain agent to process the message. 
    - Create a system prompt base on the product description on AGENTS.md
3 - We don't use the database, we simply store the message under folder ./memory/{open_id}/messages/{create_timestamp}, open_id is the unique id of the user.

4 - the folder under /memory/${open_id}/knowledge/ to manage the long-term agent memory, including but not limited to the user history, activity history, preference, schedule, etc.
5 - Design the long-term memory storage mechanism to create folder and write the memory to the file, and read the memory from the file, and navigate the files by show the file structure.
- When writing the memory to the file, we need to ensure the file, and folder are well organized, and easy to under what it stores based on the folder name, and file_name, when it's created.
