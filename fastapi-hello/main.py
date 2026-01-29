from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException, status

app = FastAPI()

# For post request body validation
class TodoItem(BaseModel):
    id: int
    task: str = "temp task"
    time_estimate: int = None
    # completed: bool


class TodoItemResponse(BaseModel):
    id: int
    task: str = "temp task"
    time_estimate: int = None
    completed: bool = False   

@app.get("/")
def read_root():
    """ root end point"""
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check():
    """ Health Check End Point"""
    return {"status": "healthy"}


@app.get("/hello/{name}")
def read_hello(name: str):
    return {"message": f"Hello, {name}!"}

@app.get("/todo")
# def todo():
# def todo() -> list[TodoItem]:
def todo() -> list[TodoItemResponse]:
    # todo_list = [
    #     {"id": 1, "task": "Buy groceries", "completed": False},
    #     {"id": 2, "task": "Walk the dog", "completed": True},
    #     {"id": 3, "task": "Read a book", "completed": False},
    # ]
    # my_todo_list = [
    #     TodoItem(id=1, task="Buy groceries", time_estimate=20),
    #     TodoItem(id=2, task="Walk the dog", time_estimate=30),
    #     TodoItem(id=3, task="Read a book", time_estimate=25),
    # ]    
    my_todo_list = [
        TodoItemResponse(id=1, task="Buy groceries", time_estimate=20),
        TodoItemResponse(id=2, task="Walk the dog", time_estimate=30),
        TodoItemResponse(id=3, task="Read a book", time_estimate=25),
    ]     
    # return {"todos": todo_list}
    return my_todo_list

@app.post("/todo")
# def add_todo(item: dict):
def add_todo(item: TodoItem) -> TodoItemResponse:
    if item.id == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID cannot be zero"
        )
    
    todo_response = TodoItemResponse(**item.dict(), completed=False) 
    # return {"message": "Todo item added", "item": item} 
    # return item
    return todo_response


@app.delete("/todo/{item_id}")
def delete_todo(item_id: int):
    return {"message": f"Todo item with id {item_id} deleted"}  

@app.put("/todo/{item_id}")
def update_todo(item_id: int, item: TodoItem) -> TodoItemResponse:
    todo_response = TodoItemResponse(**item.dict(), completed=False)   
    return todo_response

@app.patch("/todo/{item_id}/complete")
def todo_complete(item_id: int) -> TodoItemResponse:
    todo_response = TodoItemResponse(id=item_id, task="temp task", completed=True)   
    return todo_response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)