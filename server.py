# Conversation
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Summary
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI

# API Server
import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session


Base = declarative_base()


# Conversation store
class ConversationMessage(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    query = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_conversation_id", "conversation_id"),
        Index("ix_user_id", "user_id"),
        Index("ix_created_at", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "query": self.query,
            "answer": self.answer
        }


class ConversationStore:
    def __init__(self, db_url: str = "sqlite:///conversation.db") -> None:
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.Session()

    def get_messages(
        self,
        session: Session,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        desc: bool = False
    ) -> List[ConversationMessage]:
        if not conversation_id and not user_id:
            raise Exception("conversation_id or user_id is required")

        query = session.query(ConversationMessage)

        if conversation_id:
            query = query.filter(ConversationMessage.conversation_id == conversation_id)
        if user_id:
            query = query.filter(ConversationMessage.user_id == user_id)
        if since:
            query = query.filter(ConversationMessage.created_at >= since)
        if until:
            query = query.filter(ConversationMessage.created_at <= until)
        if desc:
            query = query.order_by(ConversationMessage.created_at.desc())

        return query.limit(limit).all()

    def add_message(
        self,
        session: Session,
        conversation_id: str,
        user_id: str,
        created_at: datetime,
        query: str,
        answer: str
    ):
        db_record = ConversationMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=created_at,
            query=query,
            answer=answer
        )
        session.add(db_record)


# Summarizer
class Summarizer:
    def __init__(
        self,
        openai_api_key: str,
        persist_directory: str = "./summary",
        embedding_model: str = "text-embedding-3-small",
        summarize_model: str = "gpt-4o-mini",
        summarize_system_prompt: str = None
    ):
        chroma_client = chromadb.PersistentClient(
            path=persist_directory
        )
        openai_ef = OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name=embedding_model
        )
        self.collection = chroma_client.get_or_create_collection(
            "conversation_summaries",
            embedding_function=openai_ef
        )

        self.openai_client = OpenAI(
            api_key=openai_api_key
        )
        self.summarize_model = summarize_model
        self.summarize_system_prompt = summarize_system_prompt or "Summarize given conversation in Japanese. The summary will be used as the data for long-term memory system. If you find remarkable keywords in the conversation, put it in the summary to improve search results."

    def search(self, query: str, user_id: str, limit: int = 10):
        return self.collection.query(
            query_texts=[query],
            n_results=limit,
            where={"user_id": user_id}
        )

    def create_summary(self, conversation_id: str, user_id: str, created_at: str, conversation_text: str):
        summary_resp = self.openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.summarize_system_prompt},
                {"role": "user", "content": conversation_text}
            ],
            model=self.summarize_model
        )
        summarized_content = summary_resp.choices[0].message.content

        metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": created_at
        }
        self.collection.add(
            documents=[summarized_content],
            metadatas=[metadata],
            ids=[conversation_id]
        )

        return summarized_content


# API Server (Schema)
class Message(BaseModel):
    id: Optional[int] = None
    conversation_id: str
    user_id: str
    created_at: str
    query: str
    answer: str


class MessageRequest(BaseModel):
    data: List[Message]


class MessageResponse(BaseModel):
    data: List[Message]


class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    created_at: str


class SearchResult(BaseModel):
    conversation_id: str
    user_id: str
    created_at: str
    summary: str


class SearchResponse(BaseModel):
    results: List[SearchResult]


# API server
conversation_store = ConversationStore(db_url=os.getenv("CONVERSATION_DB_URL") or "sqlite:///conversation.db")
summarizer = Summarizer(os.getenv("OPENAI_API_KEY"))


app = FastAPI()


async def add_message(messages: MessageRequest):
    with conversation_store.get_session() as db:
        last_message = conversation_store.get_messages(
            db,
            user_id=messages.data[0].user_id,
            limit=1,
            desc=True
        )

        if last_message and last_message[0].conversation_id != messages.data[0].conversation_id:
            last_conversation_messages = conversation_store.get_messages(
                db,
                conversation_id=last_message[0].conversation_id,
                limit=100
            )

            last_conversation_text = "\n".join([
                f"User: {m.query}\nAI: {m.answer}" for m in last_conversation_messages]
            )
            summarizer.create_summary(
                last_message[0].conversation_id,
                last_message[0].user_id,
                last_message[0].created_at.isoformat(),
                last_conversation_text
            )

        for m in messages.data:
            conversation_store.add_message(
                db,
                m.conversation_id,
                m.user_id,
                datetime.fromisoformat(m.created_at.replace("Z", "")),
                m.query,
                m.answer
            )
        db.commit()


@app.post("/messages")
async def post_messages(
    messages: MessageRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        add_message,
        messages=messages
    )
    return JSONResponse(content={"result": "accepted"}, status_code=201)


@app.get("/messages", response_model=MessageResponse)
async def get_messages(
    conversation_id: str,
    limit: int = 100,
    db: Session = Depends(conversation_store.get_session)
):
    messages = conversation_store.get_messages(
        db,
        conversation_id=conversation_id,
        limit=limit
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    data = []
    for m in messages:
        md = m.to_dict()
        md["created_at"] = m.created_at.isoformat()
        data.append(md)

    return MessageResponse(data=data)


@app.post("/summaries")
async def post_summaries(
    conversation_id: str,
    db: Session = Depends(conversation_store.get_session)
):
    messages = conversation_store.get_messages(
        db,
        conversation_id=conversation_id,
        limit=100
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No records found for the given conversation_id")

    conversation_text = "\n".join([f"User: {m.query}\nAI: {m.answer}" for m in messages])

    summarized_content = summarizer.create_summary(
        conversation_id,
        messages[0].user_id,
        messages[0].created_at.isoformat(),
        conversation_text
    )

    return SearchResult(
        conversation_id=conversation_id,
        user_id=messages[0].user_id,
        created_at=messages[0].created_at.isoformat(),
        summary=summarized_content
    )


@app.get("/summaries", response_model=SearchResponse)
async def get_summaries(
    query: str,
    user_id: str,
    limit: int = 10
):
    results = summarizer.search(query, user_id, limit)

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not ids:
        raise HTTPException(status_code=404, detail="No records found for the given user_id and query")

    search_results = []
    for i in range(len(ids)):
        metadata = metadatas[i]
        search_result = SearchResult(
            conversation_id=metadata["conversation_id"],
            user_id=metadata["user_id"],
            created_at=metadata["created_at"],
            summary=documents[i]
        )
        search_results.append(search_result)

    return SearchResponse(results=search_results)
