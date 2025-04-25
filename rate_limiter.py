from fastapi import FastAPI, Request, Response, HTTPException, Depends
import time
import uvicorn


app = FastAPI()

WINDOW_SIZE = 5
MAX_REQUESTS = 3


class RateLimiter:
    def __init__(self):
        self.user_requests = {}
        self.window_size = WINDOW_SIZE
        self.max_requests = MAX_REQUESTS

    def purge(self, user_id, current_time):
        """Clean requests outside the current time window."""
        cutoff_time = current_time - self.window_size
        if user_id in self.user_requests:
            self.user_requests[user_id] = [timestamp for timestamp in self.user_requests[user_id] if timestamp > cutoff_time]

    def check(self, user_id):
        """Check if user is currently rate limited."""
        current_time = time.time()
        self.purge(user_id, current_time)
        # If new user
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        # Checking the limit
        if len(self.user_requests[user_id]) >= self.max_requests:
            return True
        # Save the user
        self.user_requests[user_id].append(current_time)
        return False


rate_limiter = RateLimiter()

async def rate_limit(request: Request, response: Response):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    
    if rate_limiter.check(user_id):
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests"
        )
    return user_id


@app.get("/api/example", dependencies=[Depends(rate_limit)])
async def example_endpoint(user_id: str = Depends(rate_limit)):
    return {"message": f"Hello, {user_id}!"}


if __name__ == "__main__":
    uvicorn.run("rate_limiter:app", host="0.0.0.0", port=8003, reload=True)