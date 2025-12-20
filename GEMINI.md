# GEMINI.md - Agent Optimization Python Project

## Project Identity & Architecture Philosophy

This is an **async-first, production-grade Python agent optimization system** built for high-performance external API interactions, database operations, and web automation. The architecture embraces **FastAPI's async capabilities**, **SQLAlchemy 2.0's modern patterns**, and **Playwright's browser automation** to create resilient, scalable agent workflows.

**Core Principle:** Async everywhere except when explicitly handling CPU-bound operations or legacy sync libraries (which should be wrapped in thread pools).

---

## Critical Async/Await Patterns

### DO: Async Route Definitions
```python
# ✅ CORRECT - Async route for I/O operations
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = await db_service.fetch_agent(agent_id)  # Non-blocking DB call
    return agent
```

### DON'T: Sync Operations in Async Routes
```python
# ❌ WRONG - Blocks event loop
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    time.sleep(5)  # BLOCKS ENTIRE EVENT LOOP
    return agent

# ✅ CORRECT - Use asyncio for delays
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    await asyncio.sleep(5)  # Non-blocking delay
    return agent
```

### Thread Pool for Sync Libraries
```python
# ✅ CORRECT - Wrap sync SDK in thread pool
from fastapi.concurrency import run_in_threadpool

@app.get("/sync-operation")
async def handle_sync_sdk():
    result = await run_in_threadpool(sync_library.blocking_call, param="value")
    return result
```

---

## FastAPI Best Practices

### 1. Dependency Injection for Validation
**Use dependencies for database validation, not just DI:**

```python
# dependencies.py
async def valid_agent_id(agent_id: UUID4) -> dict[str, Any]:
    """Validates agent exists and returns agent data."""
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

# router.py
@router.get("/agents/{agent_id}")
async def get_agent(agent: dict[str, Any] = Depends(valid_agent_id)):
    return agent  # Already validated and fetched

@router.put("/agents/{agent_id}")
async def update_agent(
    update_data: AgentUpdate,
    agent: dict[str, Any] = Depends(valid_agent_id)  # Reused dependency
):
    updated = await agent_service.update(agent["id"], update_data)
    return updated
```

**Why:** Avoids duplicate validation logic across endpoints. Dependencies are cached per request.

### 2. Chain Dependencies for Complex Authorization
```python
async def valid_agent_id(agent_id: UUID4) -> dict[str, Any]:
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

async def valid_owned_agent(
    agent: dict[str, Any] = Depends(valid_agent_id),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    if agent["owner_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return agent

@router.delete("/agents/{agent_id}")
async def delete_agent(agent: dict = Depends(valid_owned_agent)):
    await agent_service.delete(agent["id"])
    return {"status": "deleted"}
```

### 3. Error Handling - Global Exception Handlers
```python
# exceptions.py
class AgentNotFound(HTTPException):
    def __init__(self, agent_id: str):
        super().__init__(
            status_code=404,
            detail=f"Agent {agent_id} not found",
            headers={"X-Error-Code": "AGENT_NOT_FOUND"}
        )

class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass

# main.py
@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database operation failed",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### 4. Response Models - Don't Return Pydantic Objects Directly
```python
# ❌ WRONG - Creates model twice (once by you, once by FastAPI)
@app.get("/agents", response_model=list[AgentResponse])
async def get_agents():
    agents = await service.get_all()
    return [AgentResponse(**agent) for agent in agents]  # Wasteful

# ✅ CORRECT - Return dict, let FastAPI validate
@app.get("/agents", response_model=list[AgentResponse])
async def get_agents():
    agents = await service.get_all()
    return agents  # Returns list[dict], FastAPI validates against response_model
```

---

## SQLAlchemy 2.0 + AsyncPG Patterns

### 1. Session Management - One Engine, Request-Scoped Sessions
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,  # Set True for SQL debugging only
    pool_pre_ping=True,  # Verify connections before use
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent DetachedInstanceError
    autocommit=False,
    autoflush=False,
)

# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 2. Query Patterns - Explicit Relationship Loading
```python
# ❌ WRONG - Lazy loading causes DetachedInstanceError in async
result = await session.execute(select(Agent).where(Agent.id == agent_id))
agent = result.scalar_one()
# Later access to agent.tasks will fail outside session context

# ✅ CORRECT - Eager load relationships
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(Agent)
    .options(selectinload(Agent.tasks))
    .where(Agent.id == agent_id)
)
agent = result.scalar_one()
# agent.tasks is now loaded and accessible
```

### 3. Transactions - Explicit Context Management
```python
# ✅ CORRECT - Explicit transaction control
async def create_agent_with_tasks(
    session: AsyncSession,
    agent_data: dict,
    tasks_data: list[dict]
):
    async with session.begin():  # Starts transaction
        agent = Agent(**agent_data)
        session.add(agent)
        await session.flush()  # Get agent.id without committing
        
        for task_data in tasks_data:
            task = Task(**task_data, agent_id=agent.id)
            session.add(task)
        
        # Commit happens automatically if no exception
    return agent
```

### 4. Upserts - PostgreSQL ON CONFLICT
```python
from sqlalchemy.dialects.postgresql import insert

async def upsert_agent_status(session: AsyncSession, agent_id: UUID, status: str):
    stmt = insert(AgentStatus).values(
        agent_id=agent_id,
        status=status,
        updated_at=datetime.utcnow()
    ).on_conflict_do_update(
        index_elements=["agent_id"],
        set_={"status": status, "updated_at": datetime.utcnow()}
    )
    await session.execute(stmt)
    await session.commit()
```

### 5. Pagination - Efficient Offset/Limit
```python
async def get_agents_paginated(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0
) -> tuple[list[Agent], int]:
    # Get total count
    count_result = await session.execute(select(func.count(Agent.id)))
    total = count_result.scalar_one()
    
    # Get paginated results
    result = await session.execute(
        select(Agent)
        .order_by(Agent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    agents = result.scalars().all()
    
    return agents, total
```

### 6. Streaming Large Result Sets
```python
async def stream_agents(session: AsyncSession):
    """Stream results without loading all into memory."""
    result = await session.stream(select(Agent).order_by(Agent.id))
    async for row in result:
        agent = row[0]
        yield agent
```

---

## Pydantic 2.9 Best Practices

### 1. Custom Base Model with Global Settings
```python
# schemas/base.py
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict
from fastapi.encoders import jsonable_encoder

def datetime_to_gmt_str(dt: datetime) -> str:
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")

class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        populate_by_name=True,  # Allow field population by alias or name
        str_strip_whitespace=True,  # Auto-trim strings
        validate_assignment=True,  # Validate on attribute assignment
        use_enum_values=True,  # Serialize enums to values
    )
    
    def serializable_dict(self, **kwargs):
        """Return dict with only JSON-serializable fields."""
        return jsonable_encoder(self.model_dump())
```

### 2. Field Validators - Use @field_validator
```python
from pydantic import field_validator, Field
import re

class AgentCreate(CustomBaseModel):
    name: str = Field(min_length=1, max_length=128)
    email: str
    config: dict[str, Any]
    
    @field_validator("email", mode="after")
    @classmethod
    def validate_email(cls, email: str) -> str:
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @field_validator("config", mode="after")
    @classmethod
    def validate_config(cls, config: dict) -> dict:
        required_keys = {"api_key", "endpoint"}
        if not required_keys.issubset(config.keys()):
            raise ValueError(f"Config must contain: {required_keys}")
        return config
```

### 3. Model Validators - Cross-Field Validation
```python
from pydantic import model_validator

class TaskSchedule(CustomBaseModel):
    start_time: datetime
    end_time: datetime
    interval_minutes: int = Field(gt=0, le=1440)
    
    @model_validator(mode="after")
    def validate_time_range(self) -> "TaskSchedule":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        
        duration = (self.end_time - self.start_time).total_seconds() / 60
        if duration < self.interval_minutes:
            raise ValueError("Time range too short for interval")
        
        return self
```

### 4. Avoid ValueError in Business Logic - Use Custom Exceptions
```python
# ❌ WRONG - ValueError becomes ValidationError in Pydantic schemas
class AgentService:
    async def create_agent(self, data: AgentCreate):
        if await self.email_exists(data.email):
            raise ValueError("Email already exists")  # Confusing error type
        # ...

# ✅ CORRECT - Use custom exception
class EmailExistsError(HTTPException):
    def __init__(self, email: str):
        super().__init__(status_code=409, detail=f"Email {email} already exists")

class AgentService:
    async def create_agent(self, data: AgentCreate):
        if await self.email_exists(data.email):
            raise EmailExistsError(data.email)
        # ...
```

---

## Playwright + AsyncIO Patterns

### 1. Browser Context Management
```python
from playwright.async_api import async_playwright, Browser, BrowserContext

class BrowserManager:
    """Manages browser instance lifecycle."""
    
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
    
    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
    
    async def create_context(self, **kwargs) -> BrowserContext:
        """Create isolated browser context."""
        return await self._browser.new_context(**kwargs)
    
    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

# Usage with FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    browser_manager = BrowserManager()
    await browser_manager.start()
    app.state.browser_manager = browser_manager
    yield
    await browser_manager.close()

app = FastAPI(lifespan=lifespan)
```

### 2. Page Actions - Always Use Proper Selectors
```python
# ❌ WRONG - Fragile XPath
await page.click('//*[@id="submit"]/div[1]/button[2]')

# ✅ CORRECT - Semantic selectors
await page.click('button:has-text("Submit")')
await page.click('[data-testid="submit-button"]')
await page.click('role=button[name="Submit"]')
```

### 3. Error Handling - Timeouts and Retries
```python
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

async def scrape_with_retry(page, url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_selector('div.content', timeout=10000)
            content = await page.inner_text('div.content')
            return content
        except PlaywrightTimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Stealth Mode with playwright-stealth
```python
from playwright_stealth import stealth_async

async def create_stealth_context(browser: Browser) -> BrowserContext:
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    # Apply stealth to all pages in context
    for page in context.pages:
        await stealth_async(page)
    
    return context
```

---

## aiohttp Session Management

### 1. Single Session Lifecycle
```python
# ✅ CORRECT - One session per application lifecycle
class HTTPClient:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
    
    async def start(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": "AgentOptimizer/1.0"}
        )
    
    async def close(self):
        if self._session:
            await self._session.close()
            await asyncio.sleep(0.25)  # Allow connections to close
    
    async def get(self, url: str, **kwargs):
        async with self._session.get(url, **kwargs) as response:
            return await response.json()

# ❌ WRONG - Creating session per request
async def make_request(url: str):
    async with aiohttp.ClientSession() as session:  # Inefficient
        async with session.get(url) as response:
            return await response.json()
```

### 2. Context Manager Pattern
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    http_client = HTTPClient()
    await http_client.start()
    app.state.http_client = http_client
    
    yield
    
    # Shutdown
    await http_client.close()
```

### 3. Error Handling
```python
from aiohttp import ClientError, ServerTimeoutError

async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except ServerTimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
        except ClientError as e:
            logger.error(f"Request failed: {e}")
            raise
```

---

## Tenacity Retry Patterns

### 1. Async Retry with Proper Exception Handling
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncpg.PostgresError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True  # Raise last exception if all retries fail
)
async def fetch_external_api(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
```

### 2. AsyncRetrying for Runtime Control
```python
from tenacity import AsyncRetrying

async def dynamic_retry_operation(url: str, max_attempts: int):
    """Retry with runtime-configured attempts."""
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    ):
        with attempt:
            result = await fetch_external_api(url)
            return result
```

### 3. Conditional Retry - Don't Retry on Client Errors
```python
def is_retryable_error(exception):
    """Only retry on server errors and timeouts."""
    if isinstance(exception, aiohttp.ClientResponseError):
        return exception.status >= 500  # Only retry 5xx errors
    return isinstance(exception, (aiohttp.ServerTimeoutError, asyncpg.PostgresError))

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception(is_retryable_error),
    reraise=True
)
async def critical_operation():
    # Operation that should retry only on server errors
    pass
```

### 4. Retry with Callbacks
```python
from tenacity import retry, stop_after_attempt, after_log

@retry(
    stop=stop_after_attempt(3),
    after=after_log(logger, logging.INFO)
)
async def logged_operation():
    # Logs after each retry attempt
    pass
```

---

## Redis Patterns

### 1. Connection Pool Management
```python
import redis.asyncio as redis

class RedisClient:
    def __init__(self, url: str):
        self.pool = redis.ConnectionPool.from_url(
            url,
            max_connections=50,
            decode_responses=True
        )
        self.client: redis.Redis | None = None
    
    async def start(self):
        self.client = redis.Redis(connection_pool=self.pool)
        await self.client.ping()  # Verify connection
    
    async def close(self):
        if self.client:
            await self.client.close()
            await self.pool.disconnect()
```

### 2. Caching Pattern with TTL
```python
async def get_cached_agent(redis: redis.Redis, agent_id: str) -> dict | None:
    """Get agent from cache with automatic deserialization."""
    cached = await redis.get(f"agent:{agent_id}")
    if cached:
        return json.loads(cached)
    return None

async def set_cached_agent(
    redis: redis.Redis,
    agent_id: str,
    data: dict,
    ttl: int = 3600
):
    """Cache agent with TTL."""
    await redis.setex(
        f"agent:{agent_id}",
        ttl,
        json.dumps(data)
    )
```

### 3. Distributed Lock Pattern
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def redis_lock(redis: redis.Redis, lock_key: str, timeout: int = 10):
    """Distributed lock using Redis."""
    lock_id = str(uuid.uuid4())
    acquired = await redis.set(lock_key, lock_id, nx=True, ex=timeout)
    
    if not acquired:
        raise ValueError(f"Could not acquire lock: {lock_key}")
    
    try:
        yield
    finally:
        # Only delete if we still own the lock
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await redis.eval(script, 1, lock_key, lock_id)

# Usage
async with redis_lock(redis_client, "agent:process:123"):
    await process_agent("123")
```

---

## Testing Patterns

### 1. Async Test Client Setup
```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    response = await client.post(
        "/agents",
        json={"name": "TestAgent", "email": "test@example.com"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "TestAgent"
```

### 2. Database Fixtures
```python
@pytest.fixture
async def db_session():
    """Provide test database session."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback after each test

@pytest.fixture
async def test_agent(db_session: AsyncSession):
    """Create test agent."""
    agent = Agent(name="TestAgent", email="test@example.com")
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent
```

---

## Common Error Prevention

### 1. DetachedInstanceError in SQLAlchemy
```python
# ❌ WRONG
async def get_agent(session: AsyncSession, agent_id: UUID):
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one()
    await session.commit()
    return agent  # agent is now detached from session

# ✅ CORRECT - Option 1: Use expire_on_commit=False
AsyncSessionLocal = async_sessionmaker(expire_on_commit=False)

# ✅ CORRECT - Option 2: Refresh before returning
async def get_agent(session: AsyncSession, agent_id: UUID):
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one()
    await session.refresh(agent)
    return agent
```

### 2. Event Loop Already Running
```python
# ❌ WRONG - Don't mix sync and async Playwright
from playwright.sync_api import sync_playwright  # Wrong in async app

async def scrape():
    with sync_playwright() as p:  # Will fail in asyncio context
        browser = p.chromium.launch()

# ✅ CORRECT - Use async Playwright
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
```

### 3. Unclosed aiohttp Session
```python
# ❌ WRONG - Session leak
async def fetch_data(url: str):
    session = aiohttp.ClientSession()
    async with session.get(url) as response:
        return await response.json()
    # Session never closed!

# ✅ CORRECT
async def fetch_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 4. BeautifulSoup Blocking in Async
```python
# ❌ WRONG - Blocks event loop
async def parse_html(html: str):
    soup = BeautifulSoup(html, 'html.parser')  # CPU-bound, blocks
    return soup.find_all('a')

# ✅ CORRECT - Run in thread pool
from fastapi.concurrency import run_in_threadpool

async def parse_html(html: str):
    def _parse():
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all('a')
    
    return await run_in_threadpool(_parse)
```

---

## Configuration Management

### 1. Pydantic Settings per Module
```python
# config/database.py
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn

class DatabaseConfig(BaseSettings):
    DATABASE_URL: PostgresDsn
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    
    class Config:
        env_file = ".env"
        env_prefix = "DB_"

db_config = DatabaseConfig()

# config/redis.py
class RedisConfig(BaseSettings):
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_DECODE_RESPONSES: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "REDIS_"

redis_config = RedisConfig()
```

---

## Project Structure

```
src/
├── agents/
│   ├── __init__.py
│   ├── router.py          # FastAPI routes
│   ├── schemas.py         # Pydantic models
│   ├── models.py          # SQLAlchemy models
│   ├── service.py         # Business logic
│   ├── dependencies.py    # Route dependencies
│   ├── exceptions.py      # Custom exceptions
│   └── utils.py           # Helper functions
├── tasks/
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   └── service.py
├── config/
│   ├── database.py        # DB settings
│   ├── redis.py           # Redis settings
│   └── settings.py        # Global settings
├── database.py            # DB engine & session
├── exceptions.py          # Global exceptions
├── main.py                # FastAPI app initialization
└── dependencies.py        # Global dependencies
tests/
├── agents/
├── tasks/
└── conftest.py
```

---

## Logging Best Practices

```python
import logging
from pythonjsonlogger import jsonlogger

# Structured logging setup
def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Usage in routes
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    logger.info("Fetching agent", extra={"agent_id": agent_id})
    try:
        agent = await service.get_agent(agent_id)
        return agent
    except Exception as e:
        logger.error(
            "Failed to fetch agent",
            extra={"agent_id": agent_id, "error": str(e)},
            exc_info=True
        )
        raise
```

---

## Database Naming Conventions

```python
# models.py
from sqlalchemy import MetaData

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Table naming rules:
# - lower_case_snake
# - Singular form: agent, agent_task, user_session
# - Group with prefix: agent_config, agent_log, agent_metric
# - Datetime suffix: created_at, updated_at, deleted_at
# - Date suffix: start_date, end_date
```

---

## Critical Reminders

1. **NEVER use `time.sleep()` in async routes** - Use `await asyncio.sleep()`
2. **ALWAYS use `async with` for aiohttp sessions and Playwright contexts**
3. **NEVER access SQLAlchemy relationships outside session context without eager loading**
4. **ALWAYS set `expire_on_commit=False` in async_sessionmaker to prevent DetachedInstanceError**
5. **NEVER create aiohttp.ClientSession per request** - Use application-level singleton
6. **ALWAYS wrap sync libraries in `run_in_threadpool` when called from async routes**
7. **NEVER mix sync and async Playwright APIs in same codebase**
8. **ALWAYS use explicit transaction boundaries with `async with session.begin()`**
9. **NEVER retry on 4xx client errors** - Only retry 5xx, timeouts, and network errors
10. **ALWAYS validate request data with dependencies, not just Pydantic schemas**

---

## Performance Optimization Checklist

- [ ] Database queries use `selectinload`/`joinedload` for relationships
- [ ] Connection pools configured with appropriate sizes
- [ ] Redis used for frequently accessed data
- [ ] Retry logic only on retryable errors (5xx, timeouts)
- [ ] Async everywhere except CPU-bound operations
- [ ] Single aiohttp session per application lifecycle
- [ ] Background tasks for non-critical operations
- [ ] Pagination implemented for list endpoints
- [ ] Database indexes on frequently queried columns
- [ ] SQL-first approach for complex queries (avoid ORM overhead)

---

This GEMINI.md is your technical contract. Every pattern here has been battle-tested in production. Deviate only with explicit justification.
