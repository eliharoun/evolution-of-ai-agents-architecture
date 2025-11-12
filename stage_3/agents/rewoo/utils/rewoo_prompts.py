"""
Prompts for ReWOO (Reasoning Without Observation) pattern.
"""

# Planner prompt: Creates complete plan with tool placeholders
PLANNER_PROMPT = """For the following task, make plans that can solve the problem step by step. For each plan, indicate \
which external tool together with tool input to retrieve evidence. You can store the evidence into a \
variable #E that can be called by later tools. (Plan, #E1, Plan, #E2, Plan, ...)

Tools can be one of the following:
(1) OrderStatus[order_id]: Check the status of an order by order ID.
(2) SearchFAQ[query]: Search the FAQ knowledge base for answers.
(3) CustomerAccount[identifier, lookup_type]: Get customer account info (lookup_type: "order_id", "email", or "customer_id").
(4) ProcessRefund[order_id, reason, amount]: Initiate refund (amount optional, defaults to full order amount).
(5) ModifyShipping[order_id, modification_type, new_value]: Modify shipping (modification_type: "expedite", "address", "standard"; new_value: new address if changing address).
(6) CheckInventory[product_name, color, size]: Check product availability (color and size optional).
(7) CreateTicket[customer_info, issue_summary, priority, category]: Create support ticket (priority: "low"/"medium"/"high"/"urgent", category: "billing"/"shipping"/"product"/"technical"/"complaint").
(8) LLM[input]: A pretrained LLM like yourself. Useful when you need to act with general \
world knowledge and common sense. Prioritize it when you are confident in solving the problem \
yourself. Input can be any instruction.

For example:
Task: My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, \
and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. \
Also, do you have the same item in blue instead of red for future reference?

Plan: Check the current status and location of order #12345. #E1 = OrderStatus[12345]
Plan: Analyze the order status to determine if it will arrive on time. #E2 = LLM[Will order #12345 arrive by tomorrow based on #E1?]
Plan: If delayed, check available shipping options to expedite. #E3 = ModifyShipping[12345, expedite]
Plan: Check if refund is possible for this order. #E4 = ProcessRefund[12345, Customer request]
Plan: Search for the same item in blue color. #E5 = CheckInventory[same item as #E1 but in blue]

Begin!
IMPORTANT: You must follow the format exactly as shown in the example above.
Each line must start with "Plan:" followed by the description, then the evidence variable assignment.
Format: Plan: <description> #E<number> = <ToolName>[<parameters>]
Do NOT use markdown formatting, bullet points, or numbered lists.

Task: {task}"""

# Solver prompt: Integrates evidence into final answer
SOLVER_PROMPT = """You are a friendly customer service agent in a CHAT conversation. Based on the investigation below, \
provide a brief, conversational response.

{plan}

IMPORTANT - Chat Format Guidelines:
- Keep it SHORT and conversational (2-4 sentences max)
- NO email formatting (no "Subject:", "Hi there!", signatures, or formal closings)
- NO bullet points or lengthy lists
- Write naturally as if chatting in real-time
- Be warm but concise
- Get straight to the point

Task: {task}
Response:"""
