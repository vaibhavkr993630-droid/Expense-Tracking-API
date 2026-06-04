from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.dependencies.auth import get_current_user, bcrypt_context
from app.dependencies.database import db_dependency
from app.models.user import User
from app.schemas.user import UpdateAccount


router = APIRouter(
    tags=["User Account"]
)


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


# Get current user profile
@router.get("/users/me", status_code=status.HTTP_200_OK)
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


# Change password
@router.patch("/users/change-password", status_code=status.HTTP_200_OK)
async def change_password(data: ChangePassword, db: db_dependency, current_user: User = Depends(get_current_user)):
    if not bcrypt_context.verify(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 8 characters.")
    current_user.hashed_password = bcrypt_context.hash(data.new_password)
    db.commit()
    return {"msg": "Password updated successfully."}


# Delete account (frontend calls /users/me)
@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(db: db_dependency, current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    db.delete(user)
    db.commit()


# Update account
@router.put("/user", status_code=status.HTTP_200_OK)
async def update_account(user_data: UpdateAccount, db: db_dependency, current_user: User = Depends(get_current_user)):
    """
    ***Update the authenticated user's username.***

    **Args:**
        user_data (UpdateAccount): Schema with the new username.
        db (db_dependency): Database session.
        current_user (User, optional): The currently authenticated user. Defaults to Depends(get_current_user).

    **Raises:**
        HTTPException: If the user isn't found.
        HTTPException: If the new username is already taken.

    **Returns:**
        dict: A message indicating the update was successful and the updated username.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if db.query(User).filter(User.username == user_data.username, User.id != current_user.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already in use.")

    user.username = user_data.username
    db.commit()
    db.refresh(user)

    return {"msg": "Username updated successfully.", "username": user.username}



# Delete account
@router.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(db: db_dependency, current_user: User = Depends(get_current_user)):
    """
    ***Delete the authenticated user's account.***

    **Args:**
        db (db_dependency): Database session.
        current_user (User, optional): The currently authenticated user. Defaults to Depends(get_current_user).

    **Raises:**
        HTTPException: If the user isn't found.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db.delete(user)
    db.commit()
