from backend.supabase_client import supabase


def save_candidate(data):
return supabase.table("candidates").insert(data).execute()
