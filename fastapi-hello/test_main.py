from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
# todo_list = [{"id": 1, "task": "Buy groceries", "completed": False},{"id": 2, "task": "Walk the dog", "completed": True},{"id": 3, "task": "Read a book", "completed": False}]

todo_list = [
  {
    "id": 1,
    "task": "Buy groceries",
    "time_estimate": 20,
    "completed": False
  },
  {
    "id": 2,
    "task": "Walk the dog",
    "time_estimate": 30,
    "completed": False
  },
  {
    "id": 3,
    "task": "Read a book",
    "time_estimate": 25,
    "completed": False
  }
]
    
def test_todo():
    response = client.get("/todo")
    assert response.status_code == 200
    # assert response.json() == {"todos": todo_list}
    assert response.json() == todo_list

def test_add_todo():
    new_todo = {"id": 4, "task": "Write tests", "time_estimate": 15}
    response = client.post("/todo", json=new_todo)
    assert response.status_code == 200
    # assert response.json() == {"message": "Todo item added", "item": new_todo}
    expected_response = {"id": 4, "task": "Write tests", "time_estimate": 15, "completed": False}
    assert response.json() == expected_response 
    
def test_delete_todo():
    item_id = 2
    response = client.delete(f"/todo/{item_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Todo item with id {item_id} deleted"}
    
def test_update_todo():
    item_id = 1
    updated_todo = {"id": item_id, "task": "Buy groceries and cook dinner", "time_estimate": 45}
    response = client.put(f"/todo/{item_id}", json=updated_todo)
    assert response.status_code == 200
    expected_response = {"id": item_id, "task": "Buy groceries and cook dinner", "time_estimate": 45, "completed": False}
    assert response.json() == expected_response       