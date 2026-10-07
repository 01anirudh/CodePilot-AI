import argparse
import asyncio
import uuid
import sys

from app.agents.graph import workflow_graph

async def main():
    parser = argparse.ArgumentParser(description="CodePilot AI CLI")
    parser.add_argument("--task", type=str, required=True, help="Task description (e.g., 'Fix the login bug')")
    parser.add_argument("--repo", type=str, default="local/repo", help="Repository format owner/repo")
    
    args = parser.parse_args()
    
    owner = args.repo.split('/')[0] if '/' in args.repo else ''
    repo_name = args.repo.split('/')[1] if '/' in args.repo else args.repo

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "workflow_id": thread_id,
        "repository_id": args.repo,
        "task_description": args.task,
        "workflow_type": "full",
        "owner": owner,
        "repo": repo_name,
        "completed_steps": [],
        "errors": [],
        "logs": [],
        "human_approved": False
    }
    
    print(f"\n🚀 Starting CodePilot Workflow for task: '{args.task}'")
    print("-" * 60)
    
    # We use a loop to support resuming after interrupts (e.g. human approval)
    is_first_run = True
    while True:
        # Start or resume the stream
        input_data = initial_state if is_first_run else None
        is_first_run = False
        
        async for event in workflow_graph.astream(input_data, config, stream_mode="updates"):
            for node_name, state_update in event.items():
                print(f"✅ [{node_name}] completed.")
                if "logs" in state_update and state_update["logs"]:
                    msg = state_update["logs"][-1].get("message", "")
                    if msg: 
                        print(f"   💬 {msg}")
                if "errors" in state_update and state_update["errors"]:
                    err = state_update["errors"][-1].get("error", "")
                    if err:
                        print(f"   ❌ ERROR: {err}")

        # Check if we hit an interrupt
        current_state = workflow_graph.get_state(config)
        if not current_state.next:
            print("\n🎉 Workflow Finished!")
            break
            
        if "human_approval" in current_state.next:
            print("\n" + "="*60)
            print("🛑 Workflow paused for Human Approval")
            print("="*60)
            user_input = input("Do you want to approve the changes? (y/n): ")
            approved = user_input.lower().strip() == 'y'
            
            # Update state with the human decision
            workflow_graph.update_state(config, {"human_approved": approved})
            print("\nResuming workflow...")
        else:
            break

if __name__ == "__main__":
    # Fix for Windows asyncio event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
