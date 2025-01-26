from typing import List

from pydantic import BaseModel, Field


class GeneralAnswer(BaseModel):
    result: bool = Field(
        ..., description="The result of the request execution. True if successful"
    )


class UserBasic(BaseModel):
    id: int = Field(..., description="The unique user ID")
    name: str = Field(..., description="Username")


class UserDetails(UserBasic):
    followers: List[UserBasic] = Field(
        ..., description="The list of users who are subscribed to this user"
    )
    following: List[UserBasic] = Field(
        ..., description="The list of users that this user is subscribed to"
    )


class UserResponse(BaseModel):
    result: bool = Field(
        ..., description="The result of the request execution. True if successful"
    )
    user: UserDetails = Field(
        ..., description="User data, including subscribers and subscriptions"
    )
