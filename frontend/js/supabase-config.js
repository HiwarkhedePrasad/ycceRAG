// ── Supabase Client Initialization ────────────────────────
const SUPABASE_URL = 'https://jjftlcgylvgtqjeghupr.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqZnRsY2d5bHZndHFqZWdodXByIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwNzM4NjMsImV4cCI6MjA4NzY0OTg2M30.Jmw4-Pn9U9CMHrlGySoISy5-_zW8MYS0OUQeQm53lLM';

const _sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
