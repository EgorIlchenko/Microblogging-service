from typing import Any, Dict

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship

from ..database import Base


class Users(Base):
    """
    ORM model for the 'users' table.

    Attributes:
        id (int): Primary key, unique identifier for each user.
        name (str): Name of the user.
        api_key (str): Unique API key for the user.
        created_at (datetime): Timestamp of user creation.

    Relationships:
        tweets: One-to-many relationship with the `Tweets` model.
        followers: Many-to-one relationship with the `Follower` model, representing users following
        this user.
        following: Many-to-one relationship with the `Follower` model, representing users this user
        follows.
    """

    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name = mapped_column(String, nullable=True)
    api_key = mapped_column(String, nullable=True, unique=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    tweets = relationship("Tweets", back_populates="author", cascade="all, delete")
    followers = relationship(
        "Follower",
        foreign_keys="[Follower.followee_id]",
        back_populates="followee",
        cascade="all, delete",
    )
    following = relationship(
        "Follower",
        foreign_keys="[Follower.follower_id]",
        back_populates="follower",
        cascade="all, delete",
    )

    def __repr__(self):
        return f"Пользователь {self.name}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweets(Base):
    """
    ORM model for the 'tweets' table.

    Attributes:
        id (int): Primary key, unique identifier for each tweet.
        user_id (int): Foreign key referencing the user who created the tweet.
        content (str): Content of the tweet.
        created_at (datetime): Timestamp of tweet creation.

    Relationships:
        author: Many-to-one relationship with the `Users` model.
        media: One-to-many relationship with the `TweetMedia` model.
        likes: One-to-many relationship with the `Like` model.
    """

    __tablename__ = "tweets"

    id = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    content = mapped_column(String, nullable=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    author = relationship("Users", back_populates="tweets")
    media = relationship(
        "TweetMedia", back_populates="tweet", cascade="all, delete", lazy="selectin"
    )
    likes = relationship("Like", back_populates="tweet", cascade="all, delete")

    @hybrid_property
    def likes_count(self):
        return len(self.likes)

    @likes_count.expression  # type: ignore
    def likes_count(cls):
        return (
            select(func.count(Like.id))
            .where(Like.tweet_id == cls.id)
            .correlate(cls)
            .label("likes_count")
        )

    def __repr__(self):
        return f"Содержание: {self.content}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    """
    ORM model for the 'media' table.

    Attributes:
        id (int): Primary key, unique identifier for each media file.
        file_path (str): Path to the stored media file.
        user_id (int): Foreign key referencing the user who uploaded the media file.
        created_at (datetime): Timestamp of media upload.

    Relationships:
        user: Many-to-one relationship with the `Users` model.
        tweet_media: One-to-many relationship with the `TweetMedia` model.
    """

    __tablename__ = "media"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path = mapped_column(String, nullable=True)
    user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())

    user = relationship("Users", backref="media")
    tweet_media = relationship(
        "TweetMedia", back_populates="media", cascade="all, delete", lazy="selectin"
    )

    def __repr__(self):
        return f"{self.file_path}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TweetMedia(Base):
    """
    ORM model for the 'tweet_media' table, representing associations between tweets and media files.

    Attributes:
        id (int): Primary key, unique identifier for each association.
        tweet_id (int): Foreign key referencing the associated tweet.
        media_id (int): Foreign key referencing the associated media file.

    Relationships:
        tweet: Many-to-one relationship with the `Tweets` model.
        media: Many-to-one relationship with the `Media` model.

    Constraints:
        unique_tweet_media: Ensures that a tweet-media combination is unique.
    """

    __tablename__ = "tweet_media"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    tweet_id = mapped_column(Integer, ForeignKey("tweets.id"), nullable=False)
    media_id = mapped_column(Integer, ForeignKey("media.id"), nullable=False)

    tweet = relationship("Tweets", back_populates="media", lazy="selectin")
    media = relationship("Media", back_populates="tweet_media", lazy="selectin")
    __table_args__ = (
        UniqueConstraint("tweet_id", "media_id", name="unique_tweet_media"),
    )

    def __repr__(self):
        return f"{self.tweet_id} - {self.media_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(Base):
    """
    ORM model for the 'likes' table.

    Attributes:
        id (int): Primary key, unique identifier for each like.
        tweet_id (int): Foreign key referencing the liked tweet.
        user_id (int): Foreign key referencing the user who liked the tweet.
        created_at (datetime): Timestamp of when the like was added.

    Relationships:
        tweet: Many-to-one relationship with the `Tweets` model.
        user: Many-to-one relationship with the `Users` model.

    Constraints:
        unique_like_tweet: Ensures that a user can like a tweet only once.
    """

    __tablename__ = "likes"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    tweet_id = mapped_column(Integer, ForeignKey("tweets.id"), nullable=False)
    user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())

    tweet = relationship("Tweets", back_populates="likes")
    user = relationship("Users", lazy="joined")

    __table_args__ = (
        UniqueConstraint("tweet_id", "user_id", name="unique_like_tweet"),
    )

    def __repr__(self):
        return f"{self.user_id} - {self.tweet_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Follower(Base):
    """
    ORM model for the 'followers' table, representing follower-followee relationships.

    Attributes:
        id (int): Primary key, unique identifier for each relationship.
        follower_id (int): Foreign key referencing the user who follows another user.
        followee_id (int): Foreign key referencing the user being followed.
        created_at (datetime): Timestamp of when the relationship was created.

    Relationships:
        follower: Many-to-one relationship with the `Users` model (follower).
        followee: Many-to-one relationship with the `Users` model (followee).

    Constraints:
        unique_follower_followee: Ensures that a user cannot follow another user more than once.
    """

    __tablename__ = "followers"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    follower_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    followee_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())

    follower = relationship(
        "Users", foreign_keys=[follower_id], back_populates="following"
    )
    followee = relationship(
        "Users", foreign_keys=[followee_id], back_populates="followers"
    )

    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="unique_follower_followee"),
    )

    def __repr__(self) -> str:
        return f"{self.follower_id} - {self.followee_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
