"""
Global Timer Notification Component
Handles background timer alerts and browser notifications across all pages.
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from config import get_current_time_slot, get_time_slot_label
from database import get_logs_by_date
from datetime import date
from auth import get_current_user

def render_global_timer():
    """
    Injects invisible timer logic to handle notifications 
    when the current time slot ends, regardless of the active page.
    """
    
    # Check if user is logged in
    user = get_current_user()
    if not user:
        return

    # Calculate time remaining
    now = datetime.now()
    if now.minute < 30:
        end_minute = 30
        end_hour = now.hour
    else:
        end_minute = 0
        end_hour = now.hour + 1
    
    # End timestamp in milliseconds for JS
    import time
    end_timestamp = int(time.mktime(now.replace(hour=end_hour % 24, minute=end_minute, second=0, microsecond=0).timetuple()) * 1000)
    
    # Check if previous slot is logged (to stop alert)
    # We need to fetch logs for today to know this.
    # This adds a database call on every rerun, but it's lightweight.
    today = date.today()
    logs = get_logs_by_date(user.id, today)
    
    logged_slots_set = {log.get("time_slot") for log in logs}
    
    current_slot = get_current_time_slot()
    prev_slot = max(0, current_slot - 1)
    prev_slot_logged = prev_slot in logged_slots_set
    
    # Calculate remaining minutes for Python-side check (optional, mostly for specific UI warnings)
    if now.minute < 30:
        remaining_minutes = 29 - now.minute
    else:
        remaining_minutes = 59 - now.minute
        
    # Logic: Alert if previous slot not logged AND time is up (handled in JS by checking timestamp)
    # If prev_slot IS logged, we tell JS to NOT alert even if time is up.
    
    js_should_alert = "true" if not prev_slot_logged else "false"
    
    # Invisible HTML component with JS logic
    # This is a stripped down version of the dashboard timer, focusing only on alerts.
    
    timer_script = f"""
    <div style="display: none;" id="global-timer-hidden"></div>
    <script>
    (function() {{
        var endTime = {end_timestamp};
        var alertStarted = false;
        var shouldAlertFromServer = {js_should_alert};
        
        // Request notification permission on load
        if ('Notification' in window && Notification.permission === 'default') {{
            Notification.requestPermission();
        }}
        
        function playAlertSound() {{
            try {{
                var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                var osc = audioCtx.createOscillator();
                var gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.frequency.value = 800;
                gain.gain.value = 0.1; // Lower volume for background alert
                osc.start();
                osc.stop(audioCtx.currentTime + 0.2);
            }} catch(e) {{}}
        }}
        
        function sendNotification() {{
            if ('Notification' in window && Notification.permission === 'granted') {{
                var n = new Notification('⏰ Tempo 30', {{
                    body: 'انتهت الفترة! سجّل إنتاجيتك الآن.',
                    icon: 'https://cdn-icons-png.flaticon.com/512/2921/2921226.png', // Generic clock icon or app logo URL
                    requireInteraction: true
                }});
                setTimeout(function() {{ n.close(); }}, 8000);
            }}
        }}
        
        function checkTimer() {{
            var now = Date.now();
            var remaining = endTime - now;
            
            // If time is up (or just passed) AND we haven't alerted yet AND server says we should
            if (remaining <= 0 && !alertStarted && shouldAlertFromServer) {{
                alertStarted = true;
                playAlertSound();
                sendNotification();
                
                // Repeat alert every minute if still ignore? 
                // Or just once? The dashboard has a persistent alarm. 
                // Global one maybe just once per slot end to be less annoying?
                // Let's make it alert once, then maybe remind correctly.
                // For now: Just once when time hits 0.
            }}
            
            // Allow reset if we move to next slot?
            // If remaining is largely negative (e.g. > 30 mins passed), we might be in next-next slot.
            // But page reload handles "current slot" updates.
        }}
        
        // Check every second
        setInterval(checkTimer, 1000);
        
    }})();
    </script>
    """
    
    components.html(timer_script, height=0)
