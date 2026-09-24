import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint

async def check_last_jobs():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['voicedub_db']
    # Get the last 5 jobs
    cursor = db.jobs.find().sort('_id', -1).limit(5)
    jobs = await cursor.to_list(length=5)
    
    if not jobs:
        print("No jobs found in database.")
        return

    print("--- Last 5 Jobs Status ---")
    for job in jobs:
        print(f"ID: {job.get('job_id')} | Status: {job.get('status')} | Progress: {job.get('progress')}%")
        if "Error" in str(job.get('status')):
            print(f"  ❌ Detailed Error: {job.get('status')}")

if __name__ == "__main__":
    asyncio.run(check_last_jobs())
