#!/usr/bin/env python3
"""
Device Refresh FY27 - Supabase Data Uploader
Uploads 82,195 device records to Supabase via REST API.

Usage:
    python3 upload_to_supabase.py

No pip installs needed — uses Python stdlib only.
Runs in ~30-60 seconds depending on connection speed.
"""
import urllib.request, urllib.error, json, sys, time

PROJECT_ID = 'kkiafzthropihnvmhixr'
SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtraWFmenRocm9waWhudm1oaXhyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDYwODU1OSwiZXhwIjoyMDk2MTg0NTU5fQ.ywNOqTblzVjZlUq41szzjRjo4qdf_cj2k_u8ea8KTmE'
BASE_URL = f'https://{PROJECT_ID}.supabase.co/rest/v1'
BATCH_SIZE = 500  # rows per REST call

HEADERS = {
    'apikey': SERVICE_KEY,
    'Authorization': f'Bearer {SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def post_batch(rows):
    payload = json.dumps(rows).encode()
    req = urllib.request.Request(
        f'{BASE_URL}/devices',
        data=payload,
        method='POST',
        headers=HEADERS
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status

def get_count():
    req = urllib.request.Request(
        f'{BASE_URL}/devices?select=id&limit=1',
        method='HEAD',
        headers={**HEADERS, 'Prefer': 'count=exact'}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.headers.get('Content-Range', '?')

def main():
    print("Device Refresh FY27 — Supabase Uploader")
    print("=" * 45)
    
    # Load row data from all_rows.json (must be in same directory)
    try:
        with open('all_rows.json') as f:
            all_rows = json.load(f)
    except FileNotFoundError:
        print("ERROR: all_rows.json not found in current directory.")
        sys.exit(1)
    
    total = len(all_rows)
    print(f"Rows to upload: {total:,}")
    print(f"Batch size:     {BATCH_SIZE}")
    print(f"Total batches:  {(total + BATCH_SIZE - 1) // BATCH_SIZE}")
    print()
    
    # Check current count
    try:
        count_info = get_count()
        print(f"Current table row count: {count_info}")
    except Exception as e:
        print(f"Warning: Could not get count: {e}")
    print()
    
    start = time.time()
    uploaded = 0
    errors = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = all_rows[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        pct = (i / total) * 100
        elapsed = time.time() - start
        if i > 0:
            rate = i / elapsed
            eta = (total - i) / rate
            eta_str = f"ETA {eta:.0f}s"
        else:
            eta_str = "..."
        
        print(f"\r  Batch {batch_num:3d}/{total_batches}  ({pct:5.1f}%)  {uploaded:,} rows  {eta_str}   ", end='', flush=True)
        
        try:
            status = post_batch(batch)
            uploaded += len(batch)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"\nHTTP {e.code} on batch {batch_num}: {body}")
            errors += 1
            if errors > 5:
                print("Too many errors, stopping.")
                sys.exit(1)
        except Exception as e:
            print(f"\nError on batch {batch_num}: {e}")
            errors += 1
            if errors > 5:
                sys.exit(1)
    
    elapsed = time.time() - start
    print(f"\r  Done!  {uploaded:,} rows uploaded in {elapsed:.1f}s                    ")
    print()
    
    # Final count
    try:
        count_info = get_count()
        print(f"Final table row count: {count_info}")
    except Exception as e:
        print(f"Warning: Could not get final count: {e}")
    
    if errors:
        print(f"\nCompleted with {errors} errors.")
    else:
        print("\n✓ Upload complete — no errors!")

if __name__ == '__main__':
    main()
