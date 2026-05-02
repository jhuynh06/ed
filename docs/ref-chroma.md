# Chroma Python Client — Quick Reference for Ed

Source: docs.trychroma.com

## Setup

```python
import chromadb

# In-memory (for testing)
client = chromadb.Client()

# Persistent (for dev)
client = chromadb.PersistentClient(path="./chroma_data")

# Client-server (for production / Docker)
client = chromadb.HttpClient(host="localhost", port=8000)
```

## Collections

```python
# Create
collection = client.get_or_create_collection(
    name="episodic",
    metadata={"hnsw:space": "cosine"}  # cosine similarity
)

# List
client.list_collections()

# Delete
client.delete_collection("episodic")
```

## Add Data

```python
collection.add(
    ids=["ep-001", "ep-002"],
    documents=["Margaret was restless at 4pm", "Margaret calmed after grandson's voice"],
    metadatas=[
        {"timestamp": 1714000000, "agitation": 72, "outcome": "calm_restored", "confidence": 0.3},
        {"timestamp": 1714003600, "agitation": 35, "outcome": "calm_restored", "confidence": 0.45}
    ]
)

# Upsert (add or update)
collection.upsert(ids=["ep-001"], documents=["Updated text"], metadatas=[{...}])
```

## Query

```python
results = collection.query(
    query_texts=["user is agitated in the afternoon"],
    n_results=5,
    where={"confidence": {"$gte": 0.2}},           # metadata filter
    where_document={"$contains": "agitated"},        # document text filter
)

# Results structure:
# results["ids"]        → [["ep-001", "ep-002"]]
# results["documents"]  → [["text1", "text2"]]
# results["distances"]  → [[0.23, 0.45]]           # lower = more similar (cosine)
# results["metadatas"]  → [[{...}, {...}]]
```

## Metadata Filtering

```python
# Comparison operators
where={"agitation": {"$gte": 60}}
where={"outcome": {"$eq": "calm_restored"}}
where={"timestamp": {"$gte": 1714000000}}

# Logical operators
where={"$and": [
    {"agitation": {"$gte": 60}},
    {"outcome": {"$eq": "calm_restored"}}
]}

where={"$or": [
    {"outcome": {"$eq": "calm_restored"}},
    {"outcome": {"$eq": "no_change"}}
]}
```

## Get (by ID, no embedding search)

```python
results = collection.get(
    ids=["ep-001"],
    # or filter:
    where={"consolidated": False},
    limit=10
)
```

## Update

```python
collection.update(
    ids=["ep-001"],
    metadatas=[{"confidence": 0.6, "consolidated": True}]
)
```

## Delete

```python
collection.delete(ids=["ep-001"])
collection.delete(where={"consolidated": True})
```

## Ed's Collections

| Collection | Documents | Key Metadata |
|-----------|-----------|-------------|
| `episodic` | sensor_summary + user_speech | timestamp, agitation_before, outcome, confidence, consolidated |
| `semantic` | pattern text | confidence, keywords, created_at, last_reinforced |
| `recipes` | trigger_pattern | success_rate, times_used, last_used |
