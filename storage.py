from backend.supabase_client import supabase


def upload_resume(file, filename):
supabase.storage.from_("resumes").upload(filename, file)
return f"resumes/{filename}"
