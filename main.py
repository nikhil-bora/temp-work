#!/usr/bin/env python3
"""
FinOps Analyst Agent - Main Entry Point
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent import (
    anthropic, conversation_history, get_finops_system_prompt,
    handle_tool_call, Fore, Style
)
from tools import AVAILABLE_TOOLS


def process_message(user_message: str, include_history: bool = True) -> list:
    """Process a conversation message with Claude"""

    # Build messages array with history if requested
    messages = []
    if include_history and conversation_history:
        messages = conversation_history.copy()

    messages.append({"role": "user", "content": user_message})

    print(f"\n{Fore.BLUE}🤖 Agent is thinking...\n")
    if include_history and conversation_history:
        print(f"{Fore.LIGHTBLACK_EX}(Using context from {len(conversation_history) // 2} previous exchanges)\n")

    current_messages = messages
    continue_processing = True
    max_attempts = 50  # Increased from 5 to allow complex multi-step operations
    attempts = 0

    while continue_processing and attempts < max_attempts:
        attempts += 1

        response = anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=get_finops_system_prompt(),
            messages=current_messages,
            tools=AVAILABLE_TOOLS
        )

        # Check for tool calls
        tool_calls = [c for c in response.content if c.type == "tool_use"]
        text_content = [c for c in response.content if c.type == "text"]

        # Display any text
        if text_content:
            print(f"\n{Fore.GREEN}💬 Agent response:")
            for text in text_content:
                print(f"{Fore.GREEN}{text.text}")

        if tool_calls:
            print(f"\n{Fore.YELLOW}🔧 Executing {len(tool_calls)} tool(s)...\n")

            tool_results = []
            for tool_call in tool_calls:
                try:
                    print(f"\n{Fore.CYAN}▶ Calling {tool_call.name}...")
                    result = handle_tool_call(tool_call.name, tool_call.input)

                    result_str = str(result) if not isinstance(result, str) else result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result_str
                    })

                    print(f"{Fore.GREEN}✓ {tool_call.name} completed")
                    print(f"{Fore.LIGHTBLACK_EX}Result size: {len(result_str) / 1024:.2f} KB")

                except Exception as error:
                    print(f"{Fore.RED}✗ {tool_call.name} failed: {str(error)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str({"error": str(error)}),
                        "is_error": True
                    })

            # Add assistant response and tool results to messages
            current_messages = current_messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ]

            # Continue loop to process tool results
        else:
            # No tool calls, we're done
            continue_processing = False

            # Save final exchange to history (only text responses, not tool details)
            final_text_response = '\n'.join(t.text for t in text_content)

            if final_text_response:
                # Add user message and assistant response to history
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": final_text_response})

                # Keep only last 10 exchanges (20 messages)
                if len(conversation_history) > 20:
                    conversation_history[:] = conversation_history[-20:]

    return conversation_history


def main():
    """Main CLI loop"""
    print(f"{Fore.CYAN}{Style.BRIGHT}\n╔════════════════════════════════════════╗")
    print(f"{Fore.CYAN}{Style.BRIGHT}║   FinOps Analyst Agent v1.0           ║")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚════════════════════════════════════════╝\n")

    print(f"{Fore.GREEN}✓ AWS Cost Explorer connected")
    print(f"{Fore.GREEN}✓ Athena ready for CUR queries")
    print(f"{Fore.GREEN}✓ Claude AI ready\n")

    print(f"{Fore.CYAN}Ask me anything about your AWS costs!\n")
    print(f"{Fore.LIGHTBLACK_EX}Examples:")
    print(f"{Fore.LIGHTBLACK_EX}  - What were my top 5 services by cost last month?")
    print(f"{Fore.LIGHTBLACK_EX}  - Show me costs for the last 30 days")
    print(f"{Fore.LIGHTBLACK_EX}  - Analyze my RI coverage")
    print(f"{Fore.LIGHTBLACK_EX}  - Forecast costs for next quarter\n")

    print(f"{Fore.LIGHTBLACK_EX}Commands:")
    print(f"{Fore.LIGHTBLACK_EX}  - /clear    - Clear conversation history")
    print(f"{Fore.LIGHTBLACK_EX}  - /history  - Show conversation history")
    print(f"{Fore.LIGHTBLACK_EX}  - exit      - Quit the agent\n")

    while True:
        try:
            user_input = input(f"{Fore.BLUE}You: {Style.RESET_ALL}").strip()

            if user_input.lower() == 'exit':
                print(f"\n{Fore.CYAN}Goodbye! 👋\n")
                break

            # Handle commands
            if user_input.lower() == '/clear':
                conversation_history.clear()
                print(f"\n{Fore.GREEN}✓ Conversation history cleared\n")
                continue

            if user_input.lower() == '/history':
                if not conversation_history:
                    print(f"\n{Fore.YELLOW}No conversation history yet\n")
                else:
                    print(f"\n{Fore.CYAN}📜 Conversation History ({len(conversation_history) // 2} exchanges):\n")
                    for idx, msg in enumerate(conversation_history, 1):
                        role = f"{Fore.BLUE}You" if msg['role'] == 'user' else f"{Fore.GREEN}Agent"
                        content = msg['content'] if isinstance(msg['content'], str) else str(msg['content'])
                        preview = content[:100] + ('...' if len(content) > 100 else '')
                        print(f"{idx}. {role}: {Fore.LIGHTBLACK_EX}{preview}")
                    print()
                continue

            if not user_input:
                continue

            try:
                process_message(user_input)
            except Exception as error:
                print(f"\n{Fore.RED}Error: {str(error)}\n")
                if 'tool_use' in str(error) or 'tool_result' in str(error):
                    print(f"{Fore.YELLOW}💡 Tip: This was a conversation history error. Use /clear to reset.\n")
                    conversation_history.clear()

            print()

        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Goodbye! 👋\n")
            break
        except EOFError:
            print(f"\n\n{Fore.CYAN}Goodbye! 👋\n")
            break


if __name__ == "__main__":
    main()
