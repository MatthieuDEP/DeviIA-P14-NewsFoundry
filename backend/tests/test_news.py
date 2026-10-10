import asyncio
from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelResponse, SystemPromptPart, TextPart
from pydantic_ai.models.function import FunctionModel
from sqlmodel import Session, select

import chat_agent as agent_module
import database
import news
from chat_agent import chat_agent
from models import Chat


@pytest.fixture
def mock_news_http(monkeypatch):
    monkeypatch.setenv("WORLD_NEWS_API_KEY", "private-news-test-key")
    monkeypatch.setattr(news, "today", lambda: date(2026, 10, 10))
    original_client = httpx.AsyncClient

    def install(handler):
        monkeypatch.setattr(news.httpx, "AsyncClient", lambda **kwargs: original_client(
            transport=httpx.MockTransport(handler), **kwargs,
        ))

    return install


def test_top_news_request_and_short_selection(mock_news_http):
    def respond(request):
        assert request.url.path == "/top-news"
        assert dict(request.url.params) == {"source-country": "fr", "language": "fr", "date": "2026-10-10"}
        assert request.headers["x-api-key"] == "private-news-test-key"
        assert "private-news-test-key" not in str(request.url)
        topics = [{"news": [
            {"title": "Sans résumé", "text": "CONTENU COMPLET SECRET"},
            {"title": "  Un sujet  ", "summary": "Un\n résumé.", "text": "CONTENU COMPLET SECRET"},
        ]}]
        topics += [{"news": [{"title": "UN SUJET", "summary": "Doublon"}]}]
        topics += [{"news": [{"title": f"Sujet {i}", "summary": "x" * 1200}]} for i in range(12)]
        return httpx.Response(200, json={"top_news": topics})

    mock_news_http(respond)
    snapshot = asyncio.run(news.fetch_top_news())
    assert snapshot["date"] == "2026-10-10"
    assert len(snapshot["articles"]) == 10
    assert snapshot["articles"][0] == {"title": "Un sujet", "summary": "Un résumé."}
    assert all(len(article["summary"]) <= 800 for article in snapshot["articles"])
    assert "CONTENU COMPLET SECRET" not in news.news_context(snapshot)


def test_missing_summary_does_not_use_full_text(mock_news_http):
    mock_news_http(lambda request: httpx.Response(200, json={"top_news": [
        {"news": [{"title": "Un titre", "summary": None, "text": "Texte interdit"}]},
    ]}))
    snapshot = asyncio.run(news.fetch_top_news())
    assert snapshot["articles"] == [{"title": "Un titre", "summary": "Résumé non fourni."}]


def test_invalid_json_is_rejected(mock_news_http):
    mock_news_http(lambda request: httpx.Response(200, text="not json"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(news.fetch_top_news())
    assert error.value.status_code == 502


@pytest.mark.parametrize("status,expected", [(401, 503), (402, 503), (429, 503), (500, 503)])
def test_api_errors_are_safe(mock_news_http, status, expected):
    mock_news_http(lambda request: httpx.Response(status, json={"message": "private provider detail"}))
    with pytest.raises(HTTPException) as error:
        asyncio.run(news.fetch_top_news())
    assert error.value.status_code == expected
    assert "private" not in error.value.detail


@pytest.mark.parametrize("payload,expected", [
    ({"top_news": []}, 503), ({"top_news": [{"news": []}]}, 503),
    ({"unexpected": []}, 502), ({"top_news": "invalid"}, 502),
])
def test_empty_or_invalid_payload_is_rejected(mock_news_http, payload, expected):
    mock_news_http(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(HTTPException) as error:
        asyncio.run(news.fetch_top_news())
    assert error.value.status_code == expected


@pytest.mark.parametrize("exception,expected", [
    (httpx.ReadTimeout("private timeout"), 504),
    (httpx.ConnectError("private network detail"), 502),
    (TimeoutError(), 504),
])
def test_network_errors(mock_news_http, exception, expected):
    def fail(request):
        raise exception

    mock_news_http(fail)
    with pytest.raises(HTTPException) as error:
        asyncio.run(news.fetch_top_news())
    assert error.value.status_code == expected


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("WORLD_NEWS_API_KEY", raising=False)
    with pytest.raises(HTTPException) as error:
        asyncio.run(news.fetch_top_news())
    assert error.value.status_code == 503


def stored_prompt(chat_id):
    with Session(database.engine) as session:
        history = ModelMessagesTypeAdapter.validate_python(session.get(Chat, chat_id).messages)
        return [part.content for message in history for part in message.parts if isinstance(part, SystemPromptPart)]


def test_prompt_saved_at_creation_and_reused_next_day(client, owner_headers, monkeypatch):
    old_id = client.post("/chats", headers=owner_headers).json()["id"]
    original = stored_prompt(old_id)
    assert len(original) == 1
    assert "2026-10-10" in original[0]
    assert "Actualité de test" in original[0]

    fetch = AsyncMock(return_value={"date": "2026-10-11", "articles": [
        {"title": "Nouvelle actualité", "summary": "Le lendemain."},
    ]})
    monkeypatch.setattr(agent_module, "fetch_top_news", fetch)
    seen = []

    def respond(messages, info):
        seen.append([part.content for message in messages for part in message.parts if isinstance(part, SystemPromptPart)])
        assert "Actualité de test" in seen[-1][0]
        return ModelResponse(parts=[TextPart("Actualité de test : Résumé de test. (10 octobre 2026)")])

    with chat_agent.override(model=FunctionModel(respond)):
        for question in ("Quelles sont les actualités du jour ?", "Peux-tu détailler ?"):
            response = client.post(f"/chats/{old_id}/messages", headers=owner_headers, json={"content": question})
            assert response.status_code == 200
            assert "Actualité de test : Résumé de test." in response.json()["reply"]
    fetch.assert_not_awaited()
    assert seen == [original, original]
    assert stored_prompt(old_id) == original
    new_id = client.post("/chats", headers=owner_headers).json()["id"]
    fetch.assert_awaited_once()
    assert "2026-10-11" in stored_prompt(new_id)[0]
    assert "Nouvelle actualité" in stored_prompt(new_id)[0]
    assert "actualites_json" not in response.text


def test_news_failure_does_not_create_incomplete_chat(client, owner_headers, monkeypatch):
    monkeypatch.setattr(agent_module, "fetch_top_news", AsyncMock(side_effect=HTTPException(503, "Actualités indisponibles.")))
    assert client.post("/chats", headers=owner_headers).status_code == 503
    with Session(database.engine) as session:
        assert session.exec(select(Chat)).all() == []


def test_failed_llm_keeps_saved_news_context(client, owner_headers):
    from unittest.mock import patch

    chat_id = client.post("/chats", headers=owner_headers).json()["id"]
    original = stored_prompt(chat_id)
    with patch.object(chat_agent, "run", side_effect=TimeoutError()):
        response = client.post(f"/chats/{chat_id}/messages", headers=owner_headers, json={"content": "Actualités ?"})
    assert response.status_code == 504
    assert stored_prompt(chat_id) == original
    assert client.get(f"/chats/{chat_id}", headers=owner_headers).json()["messages"] == []


def test_legacy_empty_chat_gets_news_on_first_message(client, owner_headers):
    with Session(database.engine) as session:
        chat = Chat(user_id=1)
        session.add(chat)
        session.commit()
        chat_id = chat.id
    response = client.post(f"/chats/{chat_id}/messages", headers=owner_headers, json={"content": "Actualités ?"})
    assert response.status_code == 200
    assert "Actualité de test" in stored_prompt(chat_id)[0]
    assert response.json()["title"] == "Actualités ?"


def test_legacy_chat_keeps_its_original_prompt(client, owner_headers, monkeypatch):
    from pydantic_ai.messages import ModelRequest

    with Session(database.engine) as session:
        chat = Chat(user_id=1, messages=ModelMessagesTypeAdapter.dump_python([
            ModelRequest(parts=[SystemPromptPart("Ancien prompt sauvegardé")]),
        ], mode="json"))
        session.add(chat)
        session.commit()
        chat_id = chat.id
    fetch = AsyncMock(side_effect=AssertionError("No news refresh allowed"))
    monkeypatch.setattr(agent_module, "fetch_top_news", fetch)
    assert client.post(f"/chats/{chat_id}/messages", headers=owner_headers, json={"content": "Suite"}).status_code == 200
    assert stored_prompt(chat_id) == ["Ancien prompt sauvegardé"]
    fetch.assert_not_awaited()
