
from database import add_task, get_tasks, update_task, delete_task
from datetime import date
import json

TEST_USER_ID = "test_user_phase1"

def test_phase1_features():
    print("--- Starting Phase 1 Verification ---")
    
    # Clean up any existing test data
    existing_tasks = get_tasks(TEST_USER_ID)
    for t in existing_tasks:
        delete_task(TEST_USER_ID, t['id'])

    # 1. Test Adding Task with New Fields
    print("\n1. Testing Add Task with Notes and Due Date...")
    res = add_task(
        TEST_USER_ID, 
        "Test Task", 
        "daily", 
        notes="This is a test note", 
        due_date="2023-12-31"
    )
    
    if res['status'] != 'success':
        print("FAIL: Failed to add task")
        return

    task_id = res['data']['id']
    print("PASS: Task added successfully")

    # 2. Verify Data Persistence
    print("\n2. Verifying Data Persistence...")
    tasks = get_tasks(TEST_USER_ID)
    my_task = next((t for t in tasks if t['id'] == task_id), None)
    
    if my_task:
        print(f"   Notes: {my_task.get('notes')} " + ("PASS" if my_task.get('notes') == "This is a test note" else "FAIL"))
        print(f"   Due Date: {my_task.get('due_date')} " + ("PASS" if my_task.get('due_date') == "2023-12-31" else "FAIL"))
        print(f"   Starred: {my_task.get('starred')} " + ("PASS" if my_task.get('starred') == False else "FAIL"))
    else:
        print("FAIL: Could not find task")
        return

    # 3. Test Starring a Task
    print("\n3. Testing Star Toggle...")
    update_res = update_task(TEST_USER_ID, task_id, {"starred": True})
    
    if update_res['status'] == 'success':
        updated_tasks = get_tasks(TEST_USER_ID)
        my_updated_task = next((t for t in updated_tasks if t['id'] == task_id), None)
        print(f"   Starred (after update): {my_updated_task.get('starred')} " + ("PASS" if my_updated_task.get('starred') == True else "FAIL"))
    else:
        print("FAIL: Failed to update task")

    # Clean up
    delete_task(TEST_USER_ID, task_id)
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_phase1_features()
