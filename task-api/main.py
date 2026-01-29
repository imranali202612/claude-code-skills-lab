from fastapi import FastAPI

app = FastAPI(
    title="Task API",
    description="A simple task management API"
)

@app.get("/")
def read_root():
    return {"message": "Task API is running"}

@app.get("/tasks")
def todo() -> list[dict[str,int | str]]:
    return [{"id": 1, "task": "Buy LCD"},
            {"id": 2, "task": "Buy Grocery"},
            {"id": 3, "task": "Pay Bills"},
            {"id": 4, "task": "Write Code"}
    ]  


#@app.get("/tasks/1")
#def todo_one() -> dict[str,int | str]:
#    return {"id": 1, "task": "Buy LCD"}
    
#@app.get("/tasks/2")
#def todo_two() -> dict[str,int | str]:
#    return {"id": 2, "task": "Buy Grocery"}
 
@app.get("/tasks/{task_id}")
async def todo_one(task_id: int = 1, include_details: bool = False) -> dict[str,int | str]:
    if task_id < 1:
        return {"error": "Task not found"}
    if include_details:
        return {"id": task_id, "task": "Buy LCD", "details": "Purchase a 24-inch LCD monitor from the electronics store."}
    return {"id": task_id, "task": "Buy LCD"}

