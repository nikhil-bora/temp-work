# Conversation Context Feature

## Overview
The FinOps agent now maintains conversation history, allowing for contextual follow-up questions and more natural interactions.

## How It Works

### Memory Management
- **Automatic History**: The agent remembers the last 10 exchanges (20 messages)
- **Context-Aware**: Can reference previous queries, results, and analyses
- **Smart Storage**: Only stores text responses, not tool execution details (prevents errors)
- **Auto-Pruning**: Automatically keeps only the most recent 10 exchanges to avoid context overflow

### Example Conversations

#### Without Context (Old Behavior)
```
You: What were my top 5 AWS services by cost last month?
Agent: [Shows results: EC2 $1500, S3 $800, RDS $600, Lambda $200, CloudWatch $100]

You: Show me more details about the second one
Agent: ❌ I don't know what you're referring to
```

#### With Context (New Behavior)
```
You: What were my top 5 AWS services by cost last month?
Agent: [Shows results: EC2 $1500, S3 $800, RDS $600, Lambda $200, CloudWatch $100]

You: Show me more details about the second one
Agent: ✅ Looking at S3 costs... [executes detailed S3 cost query]

You: Are there any optimization opportunities?
Agent: ✅ Based on the S3 analysis above... [provides S3-specific recommendations]
```

## Commands

### `/clear` - Clear Conversation History
Resets the conversation history. Useful when:
- Starting a completely new topic
- The agent seems confused by previous context
- You want to free up memory

```
You: /clear
✓ Conversation history cleared
```

### `/history` - View Conversation History
Shows a preview of the conversation history:
```
You: /history

📜 Conversation History (3 exchanges):

1. You: What were my top 5 services by cost last month?
2. Agent: Based on CUR data, your top 5 services are: 1. EC2 ($1,500.23) 2. S3 ($800.45) 3. RDS ($600.8...
3. You: Show me more details about S3
4. Agent: Let me analyze your S3 costs in detail...
5. You: Are there optimization opportunities?
6. Agent: Yes, based on the S3 analysis, I found several optimization opportunities: 1. Move infrequent...
```

## Technical Details

### History Storage
```javascript
// History format
conversationHistory = [
  { role: 'user', content: 'What were my costs?' },
  { role: 'assistant', content: 'Your costs were...' },
  { role: 'user', content: 'Show me more details' },
  { role: 'assistant', content: 'Here are the details...' }
];
```

### Why Tool Details Aren't Stored
Tool execution details (tool_use/tool_result blocks) are NOT stored in history because:
1. **Error Prevention**: Avoids tool_use/tool_result mismatch errors when resuming
2. **Context Efficiency**: Tool results can be large (CUR queries, CloudWatch data)
3. **Clarity**: The final text response contains the meaningful information

### Context Window Management
- **Max History**: 10 exchanges (20 messages)
- **Auto-Pruning**: Oldest messages removed when limit exceeded
- **Manual Clear**: Use `/clear` command to reset at any time
- **Error Recovery**: Automatically clears on tool_use/tool_result errors

## Use Cases

### 1. Drill-Down Analysis
```
You: Show me EC2 costs for last month
Agent: [Shows total EC2 costs by instance type]

You: What about t3.large instances specifically?
Agent: [Uses context to know we're talking about EC2]

You: Any underutilized ones?
Agent: [Fetches utilization for t3.large instances]
```

### 2. Comparative Analysis
```
You: What were my costs in September?
Agent: [Shows September costs]

You: Compare that to August
Agent: [Uses context to compare both months]

You: Which services increased the most?
Agent: [Identifies services with largest increase]
```

### 3. Progressive Refinement
```
You: Find expensive resources
Agent: [Shows top resources by cost]

You: Filter to only running instances
Agent: [Refines previous query]

You: Show their utilization
Agent: [Adds CloudWatch metrics to the analysis]
```

## Best Practices

### When to Use `/clear`
- **New Topic**: Switching from EC2 analysis to S3 analysis
- **Confusion**: Agent references wrong context
- **Fresh Start**: Beginning of a new analysis session

### When Context Helps
- **Follow-ups**: "What about the others?", "Show more details"
- **Comparisons**: "Compare to last month", "How does that differ?"
- **Refinements**: "Filter to running only", "Exclude spot instances"

## Limitations

1. **No Tool Result Memory**: Agent doesn't remember raw data, only text summaries
2. **10 Exchange Limit**: Very long conversations may lose early context
3. **Single Session**: History doesn't persist between agent restarts

## Troubleshooting

### Agent Seems Confused
**Problem**: Agent references wrong context or seems confused
**Solution**: Use `/clear` to reset and start fresh

### Tool Use Errors
**Problem**: Errors mentioning "tool_use" or "tool_result"
**Solution**: History automatically clears. Try your query again.

### Lost Context
**Problem**: Agent doesn't remember something from 15 questions ago
**Solution**: This is expected - only last 10 exchanges are kept. Restate your question.

## Examples in Action

### Example 1: Cost Investigation
```bash
npm start

You: Show me my highest cost resources last month
Agent: [Shows top 10 resources]

You: What's the utilization of the top 3?
Agent: [Fetches CloudWatch metrics for those 3 resources]

You: Any savings opportunities?
Agent: [Provides rightsizing recommendations based on cost + utilization]
```

### Example 2: Budget Planning
```bash
You: What were my costs in Q3?
Agent: [Shows Q3 costs]

You: Break that down by service
Agent: [Shows service breakdown for Q3]

You: If this trend continues, what's my Q4 forecast?
Agent: [Provides forecast based on Q3 trends]
```

## Future Enhancements

Potential improvements being considered:
- [ ] Persistent history across sessions (save to file)
- [ ] Configurable history length
- [ ] Search within history
- [ ] Export conversation history
