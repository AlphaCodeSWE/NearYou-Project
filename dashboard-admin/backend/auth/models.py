from pydantic import BaseModel

class AdminUser(BaseModel):
    username: str
    password: str


admins = {
    "admin": AdminUser(username="admin", password="admin")
}
