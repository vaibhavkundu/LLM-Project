from supabase import create_client
import os
from datetime import datetime

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"]
)

def log_resume_upload(session_id, file_type):
    supabase.table("resume_uploads").insert(
        {
            "session_id": session_id,
            "file_type": file_type,
            "created_at": datetime.utcnow().isoformat()
        }
    ).execute()

def log_chat(session_id, user_msg, ai_msg):
    supabase.table("chat_logs").insert(
        {
            "session_id": session_id,
            "user_message": user_msg,
            "assistant_message": ai_msg,
            "created_at": datetime.utcnow().isoformat()
        }
    ).execute()
