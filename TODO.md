## Sign up Feishu: Done
- Status: Done

### Create Feishu Bot: 
- Status:Done
- URL: https://open.feishu.cn/app/cli_a953bd3b98399bd4/bot

### Bot Setup:
- How to setup bot to receive and send message:
添加“接收消息”事件（前往“事件与回调”面板 > 添加事件 > 消息与群组）后，机器人便可接收用户发送的单聊消息。
获取用户在群组中@机器人的消息：开通该权限，并添加“接收消息”事件（前往“事件与回调”面板 > 添加事件 > 消息与群组）后，可接收用户在群聊中@机器人的消息。
- Steps:
    - 前往“事件与回调”面板 > 事件配置 -> 仅需使用 官方 SDK 启动长连接飞书客户端: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/long-connection-mode#1c227849: Completed
    - Test Receiving the message
    - Test Sending Message
- Status: Done

### Agent Buddy Design
#### Background & Goal: 
I want to launch a product for users. I call the project to be Feishu AI Weekend Buddy Agent. 
The goal of the product is to helps a user navigate the entire social friction loop: 
For example: “I want to do something this weekend people.”

##### Technical & Product RequirementsA. Core Interaction (Feishu)
A. Core Interaction (Feishu)
The primary interface must be within Feishu. The agent should:
- Capture Intent: Understand preferences (activity, availability, location, budget, group vibe).
- Execute Logic: Suggest activities, explain the "why" behind recommendations, and propose
suit buddy types.
- Drive Action: Draft invite messages or coordination cards to move the user toward a firm
confirmation.

B. Implementation Specs
- Real Integration: Use real Feishu components (Bots, Message Cards, Group Invites, or Event
Cards). Avoid using only mock screens.

- Web Context (Optional/Supporting): You may use a lightweight web dashboard to show
broader context (e.g., activity history, user trends, or recommendation insights).

C. Optional Extensions
Feel free to extend the demo in any direction that showcases your strengths:
Advanced agent reasoning/planning.
Multi-step coordination or memory/preference learning.
Unique agent-tool usage or new interaction patterns.

3. Constraints & Expectations
C. Optional Extensions
Feel free to extend the demo in any direction that showcases your strengths:
- Advanced agent reasoning/planning.
- Multi-step coordination or memory/preference learning.
- Unique agent-tool usage or new interaction patterns.
