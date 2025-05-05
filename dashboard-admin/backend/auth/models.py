from pydantic import BaseModel

class LoginForm(BaseModel):
    username: str
    password: str


admin_user = {"username": "admin", "password": "admin"}
