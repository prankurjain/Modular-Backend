import os

# Oracle Database connection settings
# Set these as environment variables / secrets before running
ORACLE_HOST = os.environ.get("ORACLE_HOST", "localhost")
ORACLE_PORT = int(os.environ.get("ORACLE_PORT", "1521"))
ORACLE_SERVICE_NAME = os.environ.get("ORACLE_SERVICE_NAME", "ORCL")
ORACLE_USER = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")

# Convenience DSN string: host:port/service
ORACLE_DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}"

# OpenAI API key - optional, embeddings are skipped when not provided
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ST AI Bridge / chat settings
API_KEY = os.environ.get("API_KEY", OPENAI_API_KEY)
CLIENT_APP_NAME = os.environ.get("CLIENT_APP_NAME", "stm32-cube-client-app")
REMOTE_USER = os.environ.get("REMOTE_USER", "local.user@st.com")

EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "https://chat.st.com/api/client-apps")
EMBEDDING_SERVICE_NAME = os.environ.get("EMBEDDING_SERVICE_NAME", "embedding")

CHAT_URL = os.environ.get("CHAT_URL", "https://chat.st.com/api/client-apps")
CHAT_SERVICE_NAME = os.environ.get("CHAT_SERVICE_NAME", "chat")
CHAT_PERSONA = os.environ.get("CHAT_PERSONA", "st_copilot")
CHAT_TEMPERATURE = float(os.environ.get("CHAT_TEMPERATURE", "0.2"))
CHAT_MAX_RESPONSE_TOKENS = int(os.environ.get("CHAT_MAX_RESPONSE_TOKENS", "4096"))

# Embedding model to use
EMBEDDING_MODEL = "text-embedding-3-small"

# Embedding vector dimension for the model above
EMBEDDING_DIMENSION = 1536

# Number of top alternatives to return by default
TOP_N_RESULTS = 10


# Vector DB settings
VECTOR_DB_PROVIDER = os.environ.get("VECTOR_DB_PROVIDER", "oracle").lower()
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_COLLECTION_PREFIX = os.environ.get("QDRANT_COLLECTION_PREFIX", "products")
