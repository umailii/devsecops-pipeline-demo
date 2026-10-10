def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_and_search_note(client):
    created = client.post("/notes", json={"title": "groceries", "body": "milk, eggs"})
    assert created.status_code == 201

    found = client.get("/notes", query_string={"q": "groc"})
    assert [n["title"] for n in found.get_json()] == ["groceries"]


def test_note_requires_title_and_body(client):
    response = client.post("/notes", json={"title": "no body"})
    assert response.status_code == 400


def test_search_input_is_not_treated_as_sql(client):
    client.post("/notes", json={"title": "alpha", "body": "first"})

    # If this string were pasted into the query, it would match every row.
    response = client.get("/notes", query_string={"q": "' OR '1'='1"})
    assert response.get_json() == []


def test_resolve_rejects_shell_metacharacters(client):
    response = client.get("/resolve", query_string={"host": "example.com; id"})
    assert response.status_code == 400
