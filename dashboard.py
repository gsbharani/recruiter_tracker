import streamlit as st
from backend.supabase_client import supabase
import pandas as pd


st.title("Dashboard")
recruiter_id = st.text_input("Recruiter ID")


if recruiter_id:
res = supabase.table("candidates").select("*").eq("recruiter_id", recruiter_id).execute()
df = pd.DataFrame(res.data)
st.dataframe(df)
