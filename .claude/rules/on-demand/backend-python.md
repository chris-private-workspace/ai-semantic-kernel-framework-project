---
paths: backend/**/*.py
---

# Python Backend Rules

> Rules for Python code in the backend.

## Import Order

```python
# 1. Standard library
import os
from typing import Dict, List, Optional

# 2. Third-party packages
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local imports
from src.core.config import settings
from src.domain.agents.service import AgentService
```

## Type Hints

```python
# Required for all public functions
def get_agent(agent_id: str, db: Session) -> Optional[Agent]:
    ...

# Use Optional for nullable
def process(data: Optional[Dict[str, Any]] = None) -> Result:
    ...

# Use Union for multiple types
def handle(input: Union[str, bytes]) -> str:
    ...
```

## Async/Await

```python
# API routes should be async
@router.get("/")
async def list_agents(db: Session = Depends(get_db)):
    return await service.get_all()

# Use asyncio for concurrent operations
results = await asyncio.gather(
    task1(),
    task2(),
    task3(),
)
```

## Error Handling

```python
# Use specific exceptions
from fastapi import HTTPException, status

if not agent:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Agent not found"
    )

# Log errors with context
logger.error(f"Failed to create agent: {e}", exc_info=True)
```

## Logging

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

logger.info(f"Created agent: {agent.id}")
logger.warning(f"Deprecated method called: {method_name}")
logger.error(f"Operation failed: {e}", exc_info=True)
```

## Configuration

```python
# Use settings from config
from src.core.config import settings

database_url = settings.DATABASE_URL
redis_host = settings.REDIS_HOST

# Never hardcode secrets
# ❌ api_key = "sk-xxx"
# ✅ api_key = settings.API_KEY
```
