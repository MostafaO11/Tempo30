
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from analytics import generate_calendar_data

def test_generate_calendar_data():
    # Setup
    today = date.today()
    start_date = today - timedelta(days=6) # Start 6 days ago
    end_date = today + timedelta(days=2)   # End 2 days in future
    daily_goal = 100
    
    # Mock logs
    logs = [
        {"log_date": str(today), "score": 120},             # Achieved (Today)
        {"log_date": str(today - timedelta(days=1)), "score": 80},  # Missed
        {"log_date": str(today - timedelta(days=2)), "score": 0},   # Vacation (No logs or 0)
        # Days 3, 4, 5, 6 ago are also Vacation (No logs)
    ]
    
    # Execute
    data = generate_calendar_data(logs, daily_goal, start_date, end_date)
    
    # Verify Structure
    assert "days" in data
    assert "stats" in data
    assert len(data["days"]) == 9 # 6 past + today + 2 future
    
    # Verify Stats
    stats = data["stats"]
    assert stats["achieved"] == 1
    assert stats["missed"] == 1
    assert stats["vacation"] == 5 # 4 days + 1 day with 0 score
    
    # Verify Individual Days
    days_map = {d["date"]: d for d in data["days"]}
    
    # Check Achieved
    assert days_map[today]["status"] == "achieved"
    assert days_map[today]["difference"] == 20
    
    # Check Missed
    missed_date = today - timedelta(days=1)
    assert days_map[missed_date]["status"] == "missed"
    assert days_map[missed_date]["difference"] == -20
    
    # Check Vacation (Explicit 0 score)
    vacation_date_1 = today - timedelta(days=2)
    assert days_map[vacation_date_1]["status"] == "vacation"
    
    # Check Vacation (No logs)
    vacation_date_2 = today - timedelta(days=3)
    assert days_map[vacation_date_2]["status"] == "vacation"
    
    # Check Future
    future_date = today + timedelta(days=1)
    assert days_map[future_date]["status"] == "future"
    
    print("All calendar logic tests passed!")

if __name__ == "__main__":
    test_generate_calendar_data()
