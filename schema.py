import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


rd_schema = (
    TextField("$.link", no_stem=True, as_name="link"),
    TextField("$.thumbnail_key", no_stem=True, as_name="thumbnail_key"),
    TextField("$.title", no_stem=True, as_name="title"),
    VectorField(
        "$.image_embedding",
        "FLAT",
        {
            "TYPE": "FLOAT32",
            "DIM": 512,
            # in redis, orthogonal (different) vectors will have high COSINE similarity of 1
            # and similar vectors will have low COSINE similarity of 0
            "DISTANCE_METRIC": "COSINE",
        },
        as_name="image_embedding",
    ),
)
definition = IndexDefinition(prefix=[""], index_type=IndexType.JSON)
