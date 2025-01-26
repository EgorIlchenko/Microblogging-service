from typing import List, Optional

from pydantic import BaseModel, Field


class GeneralAnswer(BaseModel):
    result: bool = Field(
        ..., description="The result of the request execution. True if successful"
    )


class TweetCreate(BaseModel):
    tweet_data: str = Field(..., description="Content for a new tweet")
    tweet_media_ids: Optional[list[int]] = Field(
        None, description="Media file IDs for the tweet"
    )


class TweetBasic(BaseModel):
    tweet_id: int = Field(..., description="The unique tweet ID")


class AuthorBasic(BaseModel):
    id: int = Field(..., description="The unique user ID")
    name: str = Field(..., description="Username")


class MediaBasic(BaseModel):
    media_id: int = Field(..., description="The unique media ID")


class LikeBasic(BaseModel):
    user_id: int = Field(..., description="The unique user ID")
    name: str = Field(..., description="Username")


class TweetOut(GeneralAnswer, TweetBasic):
    pass


class MediaResponse(GeneralAnswer, MediaBasic):
    pass


class TweetDetails(BaseModel):
    id: int = Field(..., description="The unique tweet ID")
    content: str = Field(..., description="The content of the tweet")
    attachments: List[str] = Field(
        ..., description="List of paths to the media files of the tweet"
    )
    author: AuthorBasic = Field(..., description="Id and name of the tweet author")
    likes: List[LikeBasic] = Field(
        ..., description="The list of users who rated the tweet"
    )


class TweetResponse(BaseModel):
    result: bool = Field(
        ..., description="The result of the request execution. True if successful"
    )
    tweets: List[TweetDetails] = Field(
        ..., description="A list of complete data for each tweet"
    )
