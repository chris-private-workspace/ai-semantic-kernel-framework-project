# F5. Learning-based Collaboration

**Category**: Learning & Intelligence  
**Priority**: P1 (Should Have - Competitive Advantage)  
**Development Time**: 1.5 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), F2 (Checkpointing), Vector Database (Pinecone/Qdrant), Azure OpenAI GPT-4o  
**Risk Level**: Medium (LLM quality dependency, data privacy concerns)

---

## 📑 Navigation

- [← Features Overview](../prd-appendix-a-features-overview.md)
- [← F4: Cross-Scenario Collaboration](./feature-04-collaboration.md)
- **F5: Learning-based Collaboration** ← You are here
- [→ F6: Agent Marketplace](./feature-06-marketplace.md)

---

## 5.1 Feature Overview

**What is Learning-based Collaboration?**

Learning-based Collaboration enables agents to **learn from past successful executions** and **improve future performance** through AI-powered few-shot learning. When an agent encounters a similar scenario it has seen before, the system automatically injects relevant historical examples into the LLM prompt, improving accuracy and consistency.

**Why This Matters**:
- **Continuous Improvement**: Agents get better over time as they accumulate successful cases
- **Reduced Errors**: Learning from past mistakes prevents recurring issues
- **Faster Resolution**: Leverage proven solutions instead of trial-and-error
- **Knowledge Transfer**: Capture institutional knowledge that would otherwise be lost
- **Personalization**: Adapt agent behavior to specific use cases and customer patterns

**Key Capabilities**:
1. **Case Recording**: Automatically capture successful agent executions as "learning cases"
2. **Semantic Search**: Find similar past cases using vector embeddings (cosine similarity)
3. **Few-Shot Injection**: Inject top-K similar cases into LLM prompt for context
4. **Human Feedback Loop**: Users can mark cases as "good" or "bad" to refine learning
5. **Learning Analytics**: Track learning effectiveness (accuracy improvement, case reuse rate)
6. **Privacy Protection**: Anonymize sensitive data (PII) before storing cases

**Business Value**:
- **Quality Improvement**: Agent accuracy increases from 70% → 85% after 1 month
- **Cost Reduction**: Fewer LLM retries = 30% lower OpenAI costs
- **Faster Onboarding**: New agents learn from existing knowledge base
- **Auditability**: Full history of what influenced each decision
- **Competitive Advantage**: Proprietary knowledge becomes a moat

**Real-World Example**:

```
Scenario: Customer Service Refund Decision

Without Learning (Cold Start):
Input: "Customer wants refund for defective product"
Agent: Analyzes from scratch, inconsistent decisions
Result: 60% approval accuracy (too lenient or too strict)

With Learning (After 100 cases):
Input: "Customer wants refund for defective product purchased 15 days ago"
System finds similar past cases:
  - Case #47: "Defective product, 10 days old" → Approved (customer loyalty)
  - Case #89: "Defective product, 20 days old" → Approved (within policy)
  - Case #102: "Defective product, 35 days old" → Rejected (outside policy)

Agent sees patterns: "Approve if <30 days, prioritize premium customers"
Result: 85% approval accuracy (consistent with company policy)
```

**Architecture Overview**:

```
┌─────────────────┐
│  Agent Execution│
│   (Step N)      │
└────────┬────────┘
         │
         │ 1. Extract input
         ▼
┌─────────────────┐         ┌──────────────┐
│  Learning       │────────►│ Vector DB    │
│  Service        │         │ (Pinecone)   │
└────────┬────────┘         └──────────────┘
         │                         ▲
         │ 2. Find similar cases   │
         ▼                         │ 3. Store embeddings
┌─────────────────┐                │
│  Top-K Cases    │                │
│  (Few-shot)     │                │
└────────┬────────┘                │
         │                         │
         │ 4. Inject into prompt   │
         ▼                         │
┌─────────────────┐                │
│  Enhanced LLM   │                │
│  Prompt         │                │
└────────┬────────┘                │
         │                         │
         │ 5. Execute & get result │
         ▼                         │
┌─────────────────┐                │
│  Agent Output   │────────────────┘
│  (Record case)  │
└─────────────────┘
```

---

## 5.2 User Stories (Complete)

### **US-F5-001: Automatically Record Successful Executions as Learning Cases**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** System (automated)
- **I want to** automatically record successful agent executions (with input, output, and context) as learning cases in a vector database
- **So that** future similar executions can benefit from past successful patterns

**Acceptance Criteria**:
1. ✅ **Auto-Recording**: After successful execution, system automatically creates learning case
2. ✅ **Case Structure**: Each case includes:
   - Input data (customer query, ticket details, etc.)
   - Output data (agent decision, resolution steps, etc.)
   - Execution metadata (timestamp, agent ID, execution time, success/failure)
   - Human feedback (thumbs up/down, optional notes)
3. ✅ **Vector Embedding**: Input text converted to vector embedding (1536-dim for OpenAI ada-002)
4. ✅ **Storage**: Case + embedding stored in vector database (Pinecone/Qdrant)
5. ✅ **PII Anonymization**: Sensitive data (customer names, emails, phone numbers) automatically redacted
6. ✅ **Deduplication**: Similar cases (>95% similarity) merged to avoid redundancy
7. ✅ **TTL**: Old cases (>1 year) automatically archived

**Case Recording Flow**:

```python
# After agent execution completes
async def record_learning_case(
    agent_id: str,
    execution_id: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    success: bool
):
    if not success:
        return  # Only record successful cases
    
    # 1. Anonymize PII
    input_anonymized = anonymize_pii(input_data)
    output_anonymized = anonymize_pii(output_data)
    
    # 2. Create case text (for embedding)
    case_text = f"""
    Agent: {agent_id}
    Input: {json.dumps(input_anonymized, indent=2)}
    Output: {json.dumps(output_anonymized, indent=2)}
    """
    
    # 3. Generate embedding
    embedding = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=case_text
    )
    
    # 4. Store in vector DB
    case_id = f"case_{uuid.uuid4().hex[:12]}"
    await vector_db.upsert(
        id=case_id,
        values=embedding.data[0].embedding,
        metadata={
            "agent_id": agent_id,
            "execution_id": execution_id,
            "input": input_anonymized,
            "output": output_anonymized,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": None  # To be filled by human later
        }
    )
    
    logger.info(f"Learning case recorded: {case_id}")
```

**Case Structure (Stored in Vector DB)**:

```json
{
  "id": "case_a1b2c3d4e5f6",
  "vector": [0.0234, -0.0456, 0.0789, ...],  // 1536 dimensions
  "metadata": {
    "agent_id": "CS.RefundDecision",
    "execution_id": "exec_xyz789",
    "input": {
      "customer_id": "CUST-****",  // Anonymized
      "product": "Wireless Headphones",
      "issue": "Defective product",
      "purchase_date": "2025-10-15",
      "days_since_purchase": 15
    },
    "output": {
      "decision": "Approved",
      "reasoning": "Customer is premium member, product defective within 30-day policy",
      "refund_amount": 99.99,
      "follow_up_action": "Send return label"
    },
    "timestamp": "2025-11-18T10:30:00Z",
    "execution_time_ms": 2340,
    "feedback": {
      "rating": "good",  // good | bad | neutral
      "notes": "Correct decision, customer satisfied",
      "rated_by": "sarah.martinez@example.com",
      "rated_at": "2025-11-18T11:00:00Z"
    }
  }
}
```

**PII Anonymization (Example)**:

```python
import re

def anonymize_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize personally identifiable information
    
    Replaces:
    - Customer names with "CUST-****"
    - Emails with "****@example.com"
    - Phone numbers with "(***) ***-****"
    - Credit card numbers with "**** **** **** 1234"
    """
    data_str = json.dumps(data)
    
    # Email pattern
    data_str = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '****@example.com', data_str)
    
    # Phone pattern (US)
    data_str = re.sub(r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})', '(***) ***-****', data_str)
    
    # Credit card pattern
    data_str = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?(\d{4})\b', r'**** **** **** \1', data_str)
    
    # Customer ID pattern (preserve partial)
    data_str = re.sub(r'CUST-\d+', 'CUST-****', data_str)
    
    return json.loads(data_str)
```

**Definition of Done**:
- [ ] Successful executions automatically recorded as learning cases
- [ ] Each case includes input, output, metadata, feedback placeholder
- [ ] Input text converted to 1536-dim vector embedding
- [ ] Cases stored in Pinecone/Qdrant with metadata
- [ ] PII automatically anonymized (emails, phones, names)
- [ ] Duplicate cases (>95% similarity) merged
- [ ] Unit tests for anonymization logic

---

### **US-F5-002: Inject Similar Past Cases into LLM Prompt (Few-Shot Learning)**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Agent Developer (Emily Zhang)
- **I want to** automatically inject top-K similar past cases into the LLM prompt when executing an agent
- **So that** the agent learns from past successful patterns and produces more accurate, consistent results

**Acceptance Criteria**:
1. ✅ **Query Trigger**: Before executing agent, system queries vector DB for similar cases
2. ✅ **Semantic Search**: Use cosine similarity to find top-K (default: 3) most similar cases
3. ✅ **Similarity Threshold**: Only inject cases with similarity ≥ 0.75 (configurable)
4. ✅ **Prompt Enhancement**: Inject cases into LLM prompt using few-shot format
5. ✅ **Performance**: Vector search completes in <200ms (P95)
6. ✅ **Fallback**: If no similar cases found, proceed without few-shot examples
7. ✅ **Configuration**: Enable/disable learning per agent via YAML

**Few-Shot Prompt Template**:

```python
FEW_SHOT_PROMPT_TEMPLATE = """
You are an AI agent helping with customer service refund decisions.

Here are some similar past cases for reference:

{few_shot_examples}

Now, analyze the current case:

Input:
{current_input}

Provide your decision in JSON format:
{{
  "decision": "Approved" or "Rejected",
  "reasoning": "Brief explanation",
  "refund_amount": number,
  "follow_up_action": "string"
}}
"""

FEW_SHOT_EXAMPLE_TEMPLATE = """
Example {index}:
Input: {input}
Output: {output}
Reasoning: {reasoning}
---
"""
```

**Enhanced Prompt (With Few-Shot Examples)**:

```
You are an AI agent helping with customer service refund decisions.

Here are some similar past cases for reference:

Example 1:
Input: {"product": "Wireless Headphones", "issue": "Defective product", "days_since_purchase": 15}
Output: {"decision": "Approved", "refund_amount": 99.99}
Reasoning: Customer is premium member, product defective within 30-day policy
---

Example 2:
Input: {"product": "Bluetooth Speaker", "issue": "Defective product", "days_since_purchase": 10}
Output: {"decision": "Approved", "refund_amount": 49.99}
Reasoning: Defective product within return window, customer loyalty
---

Example 3:
Input: {"product": "USB Cable", "issue": "Defective product", "days_since_purchase": 35}
Output: {"decision": "Rejected"}
Reasoning: Product purchased 35 days ago, outside 30-day return policy
---

Now, analyze the current case:

Input:
{"product": "Wireless Earbuds", "issue": "Defective product", "days_since_purchase": 18}

Provide your decision in JSON format:
{
  "decision": "Approved" or "Rejected",
  "reasoning": "Brief explanation",
  "refund_amount": number,
  "follow_up_action": "string"
}
```

**Learning Service Implementation**:

```python
class LearningService:
    """
    Service for learning-based collaboration using few-shot learning
    """
    
    def __init__(
        self,
        vector_db_client,
        openai_client,
        config: Dict[str, Any]
    ):
        self.vector_db = vector_db_client
        self.openai = openai_client
        self.config = config
        
        # Configuration
        self.top_k = config.get("top_k_cases", 3)
        self.similarity_threshold = config.get("similarity_threshold", 0.75)
        self.embedding_model = config.get("embedding_model", "text-embedding-ada-002")
    
    async def enhance_prompt_with_learning(
        self,
        agent_id: str,
        current_input: Dict[str, Any],
        base_prompt: str
    ) -> str:
        """
        Enhance LLM prompt with similar past cases (few-shot learning)
        
        Args:
            agent_id: ID of agent being executed
            current_input: Current input data
            base_prompt: Original prompt template
            
        Returns:
            Enhanced prompt with few-shot examples
        """
        # 1. Convert current input to embedding
        input_text = json.dumps(current_input, indent=2)
        embedding_response = await self.openai.embeddings.create(
            model=self.embedding_model,
            input=f"Agent: {agent_id}\nInput: {input_text}"
        )
        query_vector = embedding_response.data[0].embedding
        
        # 2. Query vector DB for similar cases
        similar_cases = await self.vector_db.query(
            vector=query_vector,
            top_k=self.top_k,
            filter={"agent_id": agent_id},  # Only cases from same agent
            include_metadata=True
        )
        
        # 3. Filter by similarity threshold
        filtered_cases = [
            case for case in similar_cases.matches
            if case.score >= self.similarity_threshold
        ]
        
        if not filtered_cases:
            logger.info(f"No similar cases found for agent {agent_id} (threshold: {self.similarity_threshold})")
            return base_prompt  # No few-shot examples
        
        logger.info(f"Found {len(filtered_cases)} similar cases for agent {agent_id}")
        
        # 4. Build few-shot examples
        few_shot_examples = []
        for idx, case in enumerate(filtered_cases, start=1):
            example = f"""
Example {idx} (similarity: {case.score:.2f}):
Input: {json.dumps(case.metadata['input'], indent=2)}
Output: {json.dumps(case.metadata['output'], indent=2)}
Reasoning: {case.metadata['output'].get('reasoning', 'N/A')}
---
"""
            few_shot_examples.append(example)
        
        few_shot_text = "\n".join(few_shot_examples)
        
        # 5. Inject into prompt
        enhanced_prompt = f"""
{base_prompt}

Here are some similar past cases for reference:

{few_shot_text}

Now, analyze the current case:

Input:
{input_text}
"""
        
        return enhanced_prompt
```

**Agent Execution with Learning (Integration)**:

```python
async def execute_agent_with_learning(
    agent_id: str,
    input_data: Dict[str, Any],
    learning_service: LearningService,
    enable_learning: bool = True
):
    """
    Execute agent with learning-based few-shot enhancement
    """
    # 1. Load base prompt
    agent_config = load_agent_config(agent_id)
    base_prompt = agent_config["prompt_template"]
    
    # 2. Enhance prompt with learning (if enabled)
    if enable_learning:
        enhanced_prompt = await learning_service.enhance_prompt_with_learning(
            agent_id=agent_id,
            current_input=input_data,
            base_prompt=base_prompt
        )
    else:
        enhanced_prompt = base_prompt
    
    # 3. Execute agent with enhanced prompt
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": json.dumps(input_data)}
        ],
        temperature=0.3
    )
    
    output = json.loads(response.choices[0].message.content)
    
    # 4. Record as learning case (if successful)
    if output.get("decision") in ["Approved", "Rejected"]:
        await learning_service.record_case(
            agent_id=agent_id,
            input_data=input_data,
            output_data=output,
            success=True
        )
    
    return output
```

**YAML Configuration (Enable/Disable Learning)**:

```yaml
agents:
  - id: "CS.RefundDecision"
    name: "Customer Service Refund Decision"
    learning:
      enabled: true
      top_k_cases: 3
      similarity_threshold: 0.75
      auto_record: true
      anonymize_pii: true
    
  - id: "IT.PasswordReset"
    name: "IT Password Reset"
    learning:
      enabled: false  # Disable learning for sensitive agents
```

**Definition of Done**:
- [ ] Vector DB queried for similar cases before agent execution
- [ ] Top-K cases (default: 3) retrieved with similarity ≥ 0.75
- [ ] Few-shot examples injected into LLM prompt
- [ ] Vector search completes in <200ms (P95)
- [ ] Agent execution works without learning if no cases found
- [ ] Learning can be enabled/disabled per agent via YAML
- [ ] Integration tests comparing accuracy with/without learning

---

### **US-F5-003: Human Feedback Loop for Case Quality**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐

**User Story**:
- **As a** Customer Service Manager (Sarah Martinez)
- **I want to** rate learning cases as "good" or "bad" and add notes
- **So that** the system prioritizes high-quality cases and filters out incorrect examples

**Acceptance Criteria**:
1. ✅ **Feedback UI**: After execution, user sees "Was this helpful?" prompt
2. ✅ **Rating Options**: Thumbs up (good), thumbs down (bad), neutral (skip)
3. ✅ **Optional Notes**: User can add text notes explaining rating
4. ✅ **Case Update**: Feedback stored in vector DB metadata
5. ✅ **Quality Filtering**: Bad cases (rating = "bad") excluded from future queries
6. ✅ **Analytics**: Track feedback rate, good/bad ratio per agent

**Feedback UI (Post-Execution)**:

```
┌──────────────────────────────────────────────────────────────┐
│ Agent Execution Complete: CS.RefundDecision                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Decision: ✓ Refund Approved ($99.99)                        │
│ Reasoning: Customer is premium member, within 30-day policy │
│                                                              │
│ ────────────────────────────────────────────────────────────│
│                                                              │
│ 💡 Was this decision helpful?                               │
│                                                              │
│ [👍 Good Decision]  [👎 Bad Decision]  [Skip]              │
│                                                              │
│ Optional: Add notes (visible to other CS managers)          │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Correct decision, customer was satisfied                 ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ [Submit Feedback]                                            │
└──────────────────────────────────────────────────────────────┘
```

**API: Submit Feedback**:

```bash
POST /api/learning/cases/{case_id}/feedback
{
  "rating": "good",  // good | bad | neutral
  "notes": "Correct decision, customer was satisfied",
  "rated_by": "sarah.martinez@example.com"
}

Response:
{
  "message": "Feedback recorded successfully",
  "case_id": "case_a1b2c3d4e5f6",
  "rating": "good",
  "total_feedback_count": 1
}
```

**Quality Filtering (Exclude Bad Cases)**:

```python
# When querying for similar cases
similar_cases = await vector_db.query(
    vector=query_vector,
    top_k=10,  # Query more, filter later
    filter={
        "agent_id": agent_id,
        "feedback.rating": {"$ne": "bad"}  # Exclude bad cases
    }
)

# Further prioritize good cases
good_cases = [c for c in similar_cases.matches if c.metadata.get("feedback", {}).get("rating") == "good"]
neutral_cases = [c for c in similar_cases.matches if c.metadata.get("feedback") is None]

# Return good cases first, then neutral
final_cases = (good_cases + neutral_cases)[:top_k]
```

**Feedback Analytics Dashboard**:

```
┌──────────────────────────────────────────────────────────────┐
│ Learning Analytics: CS.RefundDecision                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 📊 Case Quality Metrics                                     │
│   Total Cases: 234                                           │
│   With Feedback: 89 (38%)                                    │
│   Good Cases: 67 (75%)  ████████████████░░░░                │
│   Bad Cases: 22 (25%)   ████░░░░░░░░░░░░░░░░                │
│                                                              │
│ 🎯 Learning Effectiveness                                   │
│   Accuracy (without learning): 70%                           │
│   Accuracy (with learning): 85%  (+15% improvement)          │
│   Cases Reused: 156 times (avg 0.67 reuse per case)         │
│                                                              │
│ 👥 Top Feedback Contributors                                │
│   1. Sarah Martinez: 45 ratings                              │
│   2. John Smith: 23 ratings                                  │
│   3. Emma Wilson: 21 ratings                                 │
└──────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Post-execution UI shows feedback prompt (thumbs up/down)
- [ ] User can add optional notes with rating
- [ ] Feedback stored in vector DB case metadata
- [ ] Bad cases excluded from future similarity queries
- [ ] Good cases prioritized over neutral cases
- [ ] Analytics dashboard tracks feedback rate and quality

---

### **US-F5-004: Learning Analytics and Effectiveness Tracking**

**Priority**: P2 (Nice to Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Product Manager (David Chen)
- **I want to** view analytics showing learning effectiveness (accuracy improvement, case reuse rate, cost savings)
- **So that** I can measure ROI of the learning system and identify agents that benefit most

**Acceptance Criteria**:
1. ✅ **Accuracy Tracking**: Compare agent accuracy with vs. without learning
2. ✅ **Case Reuse Rate**: Track how often each case is used in few-shot prompts
3. ✅ **Cost Savings**: Calculate OpenAI cost reduction from fewer retries
4. ✅ **Agent Comparison**: Identify which agents benefit most from learning
5. ✅ **Trend Analysis**: Show accuracy improvement over time (weekly/monthly)
6. ✅ **Export**: Download analytics as CSV/PDF

**Analytics Metrics**:

```json
{
  "agent_id": "CS.RefundDecision",
  "period": "2025-11-01 to 2025-11-30",
  "metrics": {
    "accuracy": {
      "without_learning": 0.70,
      "with_learning": 0.85,
      "improvement": 0.15,
      "improvement_percentage": 21.4
    },
    "case_stats": {
      "total_cases": 234,
      "good_cases": 67,
      "bad_cases": 22,
      "neutral_cases": 145,
      "avg_similarity_score": 0.82
    },
    "reuse_stats": {
      "total_executions": 1247,
      "executions_with_learning": 1089,
      "learning_usage_rate": 0.87,
      "avg_cases_per_execution": 2.8,
      "total_case_reuses": 3049
    },
    "cost_savings": {
      "avg_retry_count_without_learning": 1.8,
      "avg_retry_count_with_learning": 0.4,
      "retry_reduction": 1.4,
      "cost_per_execution_usd": 0.05,
      "monthly_savings_usd": 87.29
    },
    "performance": {
      "avg_vector_search_time_ms": 145,
      "p95_vector_search_time_ms": 198,
      "prompt_token_increase": 456  // Tokens added by few-shot examples
    }
  }
}
```

**Trend Chart (Accuracy Over Time)**:

```
┌──────────────────────────────────────────────────────────────┐
│ Agent Accuracy Trend: CS.RefundDecision                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 100%│                                              ●──●      │
│     │                                         ●───●           │
│  90%│                                    ●───●                │
│     │                               ●───●                     │
│  80%│                          ●───●                          │
│     │                     ●───●                               │
│  70%│ ●──●──●──●────●───●  (Learning enabled here)           │
│     │                    ↑                                    │
│  60%│                    Week 2                               │
│     └────┬────┬────┬────┬────┬────┬────┬────┬───            │
│         W1   W2   W3   W4   W5   W6   W7   W8                │
│                                                              │
│ ● Without Learning (baseline: 70%)                          │
│ ● With Learning (current: 85%, +15% improvement)            │
└──────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Analytics API returns accuracy, reuse rate, cost savings
- [ ] Dashboard displays trend chart (accuracy over time)
- [ ] Agent comparison table shows which agents benefit most
- [ ] Export analytics as CSV/PDF
- [ ] Scheduled report sent weekly to stakeholders

---

## 5.3 Technical Implementation (Detailed)

### 5.3.1 Vector Database Setup (Pinecone)

```python
import pinecone
from pinecone import Pinecone

# Initialize Pinecone client
pc = Pinecone(api_key="your-api-key")

# Create index for learning cases
index_name = "learning-cases"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI ada-002 embedding size
        metric="cosine",  # Cosine similarity
        spec={
            "pod": {
                "environment": "us-east-1",
                "pod_type": "p1.x1"
            }
        }
    )

index = pc.Index(index_name)

# Upsert learning case
index.upsert(
    vectors=[
        {
            "id": "case_a1b2c3d4e5f6",
            "values": embedding_vector,  # 1536-dim list
            "metadata": {
                "agent_id": "CS.RefundDecision",
                "input": {...},
                "output": {...},
                "timestamp": "2025-11-18T10:30:00Z",
                "feedback": None
            }
        }
    ]
)

# Query similar cases
results = index.query(
    vector=query_embedding,
    top_k=3,
    filter={"agent_id": "CS.RefundDecision"},
    include_metadata=True
)
```

---

## 5.4 Database Schema

```sql
CREATE TABLE learning_cases (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    execution_id VARCHAR(100),
    
    -- Case data (anonymized)
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    
    -- Embedding
    embedding_vector VECTOR(1536),  -- pgvector extension
    
    -- Metadata
    similarity_score FLOAT,
    reuse_count INTEGER DEFAULT 0,
    
    -- Feedback
    feedback_rating VARCHAR(20),  -- good | bad | neutral
    feedback_notes TEXT,
    feedback_by VARCHAR(100),
    feedback_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_learning_agent ON learning_cases(agent_id, created_at DESC);
CREATE INDEX idx_learning_feedback ON learning_cases(feedback_rating);
CREATE INDEX idx_learning_reuse ON learning_cases(reuse_count DESC);

-- Vector similarity search (requires pgvector extension)
CREATE INDEX idx_learning_embedding ON learning_cases USING ivfflat (embedding_vector vector_cosine_ops);
```

---

## 5.5 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Vector search latency | P95 < 200ms | APM monitoring |
| | Embedding generation | < 500ms | OpenAI API logs |
| | Case recording | < 1 second (async) | Background job monitoring |
| **Scalability** | Total cases | Support 100K+ cases per agent | Vector DB capacity |
| | Concurrent queries | 500+ per second | Load testing |
| **Quality** | Accuracy improvement | +10-20% after 1 month | A/B testing |
| | Case reuse rate | ≥60% executions use learning | Analytics |
| | Similarity threshold | ≥0.75 for useful cases | Tuning |
| **Privacy** | PII anonymization | 100% of sensitive data redacted | Automated tests |
| | Data retention | Cases archived after 1 year | TTL policy |
| **Cost** | Vector DB cost | <$200/month for 100K cases | Pinecone billing |
| | Embedding cost | <$50/month (1M queries) | OpenAI billing |

---

## 5.6 Testing Strategy

**Unit Tests**:
- PII anonymization (emails, phones, names)
- Vector embedding generation
- Similarity score calculation
- Feedback rating storage

**Integration Tests**:
- End-to-end case recording flow
- Few-shot prompt enhancement
- Vector search with filtering
- Feedback loop (submit + retrieve)

**A/B Testing**:
- Group A: Agent without learning (baseline)
- Group B: Agent with learning (treatment)
- Measure: Accuracy, retry count, cost per execution

---

## 5.7 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Low-quality cases degrade performance | Medium | High | Human feedback loop, bad case filtering, similarity threshold |
| PII leakage in learning cases | Low | Critical | Automated PII anonymization, regular audits, encryption at rest |
| Vector DB cost explosion | Medium | Medium | TTL policy (1-year archival), case deduplication, usage monitoring |
| LLM context window overflow | Low | Medium | Limit few-shot examples to top-3, token budget monitoring |
| Learning bias from imbalanced data | Medium | Medium | Balanced sampling, diversity scoring, regular retraining |

---

## 5.8 Future Enhancements (Post-MVP)

1. **Active Learning**: System suggests which cases need human review
2. **Multi-Agent Learning**: Share cases across related agents (e.g., CS ↔ Sales)
3. **Negative Examples**: Inject "what not to do" examples for contrast
4. **Dynamic K-Tuning**: Automatically adjust top-K based on agent complexity
5. **Learning Explainability**: Show which past case influenced current decision
6. **Federated Learning**: Learn from multiple deployments without sharing raw data

---

**Next Feature**: [F6. Agent Marketplace →](./feature-06-marketplace.md)
