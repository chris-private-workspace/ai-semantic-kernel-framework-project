# F3. Cross-System Correlation

**Category**: Integration & Intelligence  
**Priority**: P0 (Must Have - Core Differentiator)  
**Development Time**: 2 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), ServiceNow API, Dynamics 365 API, SharePoint API, Azure OpenAI, Redis  
**Risk Level**: Medium (External API rate limits and availability)

---

## 📑 Navigation

- [← Features Overview](../prd-appendix-a-features-overview.md)
- [← F2: Human-in-the-loop Checkpointing](./feature-02-checkpointing.md)
- **F3: Cross-System Correlation** ← You are here
- [→ F4: Cross-Scenario Collaboration](./feature-04-collaboration.md)

---

## 3.1 Feature Overview

**What is Cross-System Correlation?**

Cross-System Correlation is the **core differentiator** that enables agents to query multiple enterprise systems simultaneously (ServiceNow, Dynamics 365, SharePoint), correlate the data using AI, and present a unified "Customer 360 View" in under 5 seconds. This eliminates the manual process of switching between systems, copying data, and piecing together customer context.

**Why This Matters**:
- **Time Savings**: Reduces data gathering from 10-15 minutes to <5 seconds (95% faster)
- **Complete Context**: Provides holistic view by combining support tickets, CRM data, and documents
- **AI-Powered Insights**: Uses GPT-4o to identify patterns, anomalies, and correlations humans might miss
- **Reduced Errors**: Eliminates manual copy-paste errors and outdated information
- **Better Decisions**: Customer service agents can make informed decisions with complete historical context

**Key Capabilities**:
1. **Parallel Querying**: Simultaneously query 3+ enterprise systems (5s timeout per system)
2. **Intelligent Caching**: Redis-based caching (1-day TTL) for frequently accessed customer data
3. **AI Correlation**: GPT-4o analyzes cross-system data to identify patterns and relationships
4. **Graceful Degradation**: Return partial results if one system is unavailable
5. **Confidence Scoring**: AI provides confidence score for each correlation insight
6. **Real-time Freshness**: Cache invalidation on data updates (future enhancement)

**Business Value**:
- **Productivity**: CS agents handle 40-50% more tickets per day
- **CSAT Improvement**: Customer satisfaction increases from 3.5/5 to 4.5/5 due to faster, more accurate responses
- **Revenue Protection**: Identify at-risk customers early by correlating support issues with purchase patterns
- **Cost Reduction**: Reduce average ticket resolution time from 24 hours to 2-3 hours
- **Compliance**: Centralized audit trail of all cross-system data access

**Real-World Example**:
```
CS Agent Scenario: Customer calls about product issue

Traditional Process (10-15 minutes):
1. Open ServiceNow → Search customer tickets → Copy ticket IDs
2. Open Dynamics 365 → Search by customer email → Copy purchase history
3. Open SharePoint → Search customer name → Find product manuals
4. Manually piece together timeline in Excel
5. Analyze patterns and identify root cause

With Cross-System Correlation (<5 seconds):
1. Enter customer ID in IPA
2. System queries all 3 systems in parallel
3. AI correlates data and generates insights:
   - "Customer purchased Premium Plan on 2025-10-15"
   - "3 similar support tickets in past month (pattern detected)"
   - "Recent product documentation update may have caused confusion"
   - "Recommendation: Offer refund + updated user guide"
```

---

## 3.2 User Stories (Complete)

### **US-F3-001: Query Customer 360 View in <5 Seconds**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Customer Service Agent (Sarah Martinez)
- **I want to** enter a customer ID and get a complete 360-degree view of the customer from ServiceNow, Dynamics 365, and SharePoint in under 5 seconds
- **So that** I can quickly understand the customer's history and context without manually searching 3 different systems

**Acceptance Criteria**:
1. ✅ **Fast Query**: System returns complete customer 360 view in P95 < 5 seconds
2. ✅ **Parallel Execution**: System queries all 3 systems simultaneously (not sequentially)
3. ✅ **Comprehensive Data**: Response includes:
   - **ServiceNow**: Open/closed tickets, average resolution time, ticket categories
   - **Dynamics 365**: Customer profile (name, email, phone, tier), purchase history (orders, amounts, products), account status
   - **SharePoint**: Customer-related documents (contracts, proposals, correspondence)
4. ✅ **Structured Response**: Data returned in consistent JSON format for easy rendering
5. ✅ **Error Handling**: If one system times out, return partial results with clear indication of missing data
6. ✅ **Cache Hit**: Subsequent queries for same customer ID return from cache (<200ms)
7. ✅ **UI Display**: Customer 360 page shows data in organized cards with visual hierarchy

**API Request Example**:
```bash
POST /api/correlation/customer-360
{
  "customer_id": "CUST-5678"
}
```

**API Response Example**:
```json
{
  "customer_id": "CUST-5678",
  "query_time_ms": 4235,
  "cache_hit": false,
  "systems_queried": ["servicenow", "dynamics365", "sharepoint"],
  "data": {
    "servicenow": {
      "success": true,
      "tickets": {
        "open": 2,
        "closed": 15,
        "total": 17
      },
      "recent_tickets": [
        {
          "ticket_id": "CS-1234",
          "subject": "Refund request",
          "status": "Open",
          "priority": 3,
          "created_at": "2025-11-15T10:30:00Z"
        }
      ],
      "avg_resolution_time_hours": 18.5
    },
    "dynamics365": {
      "success": true,
      "profile": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "tier": "Premium",
        "account_status": "Active",
        "member_since": "2022-03-15"
      },
      "purchase_history": {
        "total_orders": 15,
        "total_spent": 1247.50,
        "recent_orders": [
          {
            "order_id": "12345",
            "date": "2025-11-10",
            "amount": 99.99,
            "products": ["Wireless Headphones"]
          }
        ]
      }
    },
    "sharepoint": {
      "success": true,
      "documents": [
        {
          "title": "Service Contract 2025",
          "url": "https://company.sharepoint.com/docs/contract-cust5678.pdf",
          "modified_at": "2025-01-15T09:00:00Z"
        }
      ],
      "document_count": 3
    }
  }
}
```

**UI Mockup**:
```
┌──────────────────────────────────────────────────────────────────┐
│ Customer 360 View: John Doe (CUST-5678)              [Refresh]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌────────────────────┐  ┌────────────────────┐  ┌─────────────┐│
│ │ 🎫 ServiceNow      │  │ 💼 Dynamics 365    │  │ 📄 SharePoint││
│ │                    │  │                    │  │              ││
│ │ Open Tickets: 2    │  │ Name: John Doe     │  │ Documents: 3 ││
│ │ Closed: 15         │  │ Tier: Premium      │  │              ││
│ │ Avg Resolve: 18.5h │  │ Total Spent: $1.2K │  │ ✓ Contract   ││
│ │                    │  │ Orders: 15         │  │ ✓ Proposal   ││
│ │ Recent:            │  │                    │  │ ✓ Email      ││
│ │ • CS-1234 (Refund) │  │ Recent:            │  │              ││
│ │   Priority: High   │  │ • Order #12345     │  │              ││
│ │   Status: Open     │  │   $99.99 (Nov 10)  │  │              ││
│ └────────────────────┘  └────────────────────┘  └─────────────┘│
│                                                                  │
│ 🤖 AI-Generated Insights (Confidence: 87%)                      │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ • Pattern detected: 3 similar tickets in past 30 days      │ │
│ │ • Customer loyalty: Premium member for 3+ years            │ │
│ │ • Recent purchase correlation: Refund request matches      │ │
│ │   product from Order #12345                                │ │
│ │ • Recommendation: Expedite refund to retain premium member │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Query Time: 4.2s  Cache: Miss  Systems: 3/3 successful          │
└──────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] API returns customer 360 view in P95 < 5 seconds
- [ ] All 3 systems queried in parallel (not sequential)
- [ ] Response includes all required data fields (tickets, profile, orders, documents)
- [ ] Cache hit returns data in <200ms
- [ ] Partial results returned if one system fails
- [ ] UI displays data in organized card layout
- [ ] Load testing confirms 50+ concurrent queries supported

**Technical Notes**:
- Use `asyncio.gather()` for parallel API calls
- Implement per-system 5-second timeout
- Cache full response in Redis with key `customer_360:{customer_id}`
- Use TTL of 86400 seconds (1 day)

---

### **US-F3-002: AI-Powered Correlation and Insights**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Customer Service Agent (Sarah Martinez)
- **I want to** see AI-generated insights that correlate data across all 3 systems and identify patterns, anomalies, or recommendations
- **So that** I can make better decisions based on holistic analysis rather than just raw data

**Acceptance Criteria**:
1. ✅ **AI Analysis**: After fetching raw data, system sends it to GPT-4o for correlation analysis
2. ✅ **Insight Types**: AI identifies:
   - **Patterns**: Recurring issues, seasonal trends, behavior patterns
   - **Anomalies**: Unusual activity (e.g., sudden spike in support tickets, large purchase followed by refund request)
   - **Correlations**: Relationships between data points (e.g., support ticket matches recent purchase)
   - **Timeline**: Chronological events across systems
   - **Recommendations**: Actionable next steps based on analysis
3. ✅ **Confidence Scoring**: Each insight includes confidence score (0-100%)
4. ✅ **Explanation**: AI provides reasoning for each insight
5. ✅ **Fast Generation**: Insights generated in <2 seconds (included in 5-second total)
6. ✅ **Structured Output**: Insights returned in JSON format for easy rendering
7. ✅ **Fallback**: If AI call fails, return raw data without insights (graceful degradation)

**LLM Prompt Template**:
```python
CORRELATION_PROMPT = """
You are an AI assistant analyzing customer data from multiple enterprise systems.

Customer ID: {customer_id}

ServiceNow Data (Support Tickets):
{servicenow_data}

Dynamics 365 Data (CRM):
{dynamics365_data}

SharePoint Data (Documents):
{sharepoint_data}

Analyze this data and provide:
1. **Patterns**: Any recurring issues, trends, or behavior patterns
2. **Anomalies**: Unusual activity that requires attention
3. **Correlations**: Relationships between data across systems (e.g., ticket related to recent purchase)
4. **Timeline**: Key events in chronological order
5. **Recommendations**: Actionable next steps for customer service agent

For each insight, provide:
- Description (1-2 sentences)
- Confidence score (0-100%)
- Supporting evidence (which data points led to this insight)

Output as JSON:
{{
  "patterns": [
    {{"description": "...", "confidence": 85, "evidence": ["ticket CS-1234", "order #12345"]}}
  ],
  "anomalies": [...],
  "correlations": [...],
  "timeline": [...],
  "recommendations": [...]
}}
"""
```

**AI Response Example**:
```json
{
  "insights": {
    "patterns": [
      {
        "description": "Customer has submitted 3 refund-related tickets in past 30 days, suggesting product dissatisfaction",
        "confidence": 87,
        "evidence": ["CS-1234", "CS-1189", "CS-1145"],
        "type": "recurring_issue"
      }
    ],
    "anomalies": [
      {
        "description": "Large purchase ($299.99) followed by immediate refund request (same day) - unusual for premium members",
        "confidence": 92,
        "evidence": ["Order #12350", "CS-1234"],
        "type": "suspicious_activity"
      }
    ],
    "correlations": [
      {
        "description": "Current refund request (CS-1234) directly relates to Order #12345 placed 5 days ago",
        "confidence": 95,
        "evidence": ["CS-1234 mentions Order #12345", "Ticket created Nov 15, Order placed Nov 10"],
        "type": "ticket_order_match"
      }
    ],
    "timeline": [
      {"date": "2025-11-10", "event": "Order #12345 placed ($99.99)", "system": "Dynamics 365"},
      {"date": "2025-11-12", "event": "Order #12345 delivered", "system": "Dynamics 365"},
      {"date": "2025-11-15", "event": "Ticket CS-1234 opened (Refund request)", "system": "ServiceNow"},
      {"date": "2025-11-15", "event": "Service contract renewed", "system": "SharePoint"}
    ],
    "recommendations": [
      {
        "description": "Expedite refund approval to retain premium member (3+ year customer, $1.2K lifetime value)",
        "confidence": 88,
        "action": "approve_refund",
        "rationale": "Customer loyalty justifies fast resolution"
      },
      {
        "description": "Investigate product quality issue - pattern of 3 similar tickets suggests systemic problem",
        "confidence": 75,
        "action": "escalate_to_product_team",
        "rationale": "Recurring issue may affect other customers"
      }
    ]
  },
  "generation_time_ms": 1850,
  "model": "gpt-4o",
  "tokens_used": 1250,
  "cost_usd": 0.0375
}
```

**UI Display**:
```
🤖 AI-Generated Insights (Confidence: 87%)

📊 Patterns Detected:
  • Recurring issue: 3 refund-related tickets in 30 days (87% confidence)
    Evidence: CS-1234, CS-1189, CS-1145

⚠️  Anomalies:
  • Large purchase ($299.99) + immediate refund (same day) - unusual (92% confidence)
    Evidence: Order #12350, Ticket CS-1234

🔗 Correlations:
  • Current ticket CS-1234 directly relates to Order #12345 (95% confidence)
    Timeline: Order Nov 10 → Delivered Nov 12 → Ticket Nov 15

💡 Recommendations:
  1. Expedite refund to retain premium member (88% confidence)
     Rationale: 3+ year customer, $1.2K lifetime value
  
  2. Escalate to product team for quality investigation (75% confidence)
     Rationale: 3 similar tickets suggest systemic issue
```

**Definition of Done**:
- [ ] AI analysis completes in <2 seconds
- [ ] All 5 insight types generated (patterns, anomalies, correlations, timeline, recommendations)
- [ ] Each insight includes confidence score and evidence
- [ ] Insights displayed in organized UI sections
- [ ] Graceful fallback if AI call fails
- [ ] LLM costs tracked and logged

**Technical Notes**:
- Use Azure OpenAI GPT-4o (fastest model)
- Max tokens: 2000 (balance between detail and speed)
- Temperature: 0.3 (more deterministic analysis)
- Implement retry logic (3 attempts) for transient failures

---

### **US-F3-003: Graceful Degradation with Partial Results**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** ensure the system returns partial results if one or two enterprise systems are down or timing out
- **So that** customer service agents can still access available data rather than seeing a complete failure

**Acceptance Criteria**:
1. ✅ **Partial Success**: If 1 out of 3 systems fails, return data from successful 2 systems
2. ✅ **Clear Indication**: Response clearly indicates which systems failed and why
3. ✅ **Timeout Handling**: Each system has 5-second timeout; failures don't block other systems
4. ✅ **Error Logging**: All failures logged to database for monitoring
5. ✅ **UI Indication**: Failed system cards show error state with retry option
6. ✅ **Retry Logic**: User can click "Retry" to re-query failed system
7. ✅ **AI Adjustment**: AI analysis adjusts confidence scores based on missing data

**Partial Failure Response Example**:
```json
{
  "customer_id": "CUST-5678",
  "query_time_ms": 5234,
  "success_rate": "2/3",
  "systems_queried": ["servicenow", "dynamics365", "sharepoint"],
  "data": {
    "servicenow": {
      "success": true,
      "tickets": {...}
    },
    "dynamics365": {
      "success": false,
      "error": "Connection timeout after 5 seconds",
      "error_code": "TIMEOUT",
      "retry_available": true
    },
    "sharepoint": {
      "success": true,
      "documents": {...}
    }
  },
  "insights": {
    "warning": "Analysis based on partial data (Dynamics 365 unavailable)",
    "confidence_adjusted": true,
    "patterns": [...],  // Lower confidence scores due to missing CRM data
    "recommendations": [
      {
        "description": "Retry Dynamics 365 query for complete customer profile",
        "action": "retry_dynamics365",
        "priority": "high"
      }
    ]
  }
}
```

**UI Mockup (Partial Failure)**:
```
┌──────────────────────────────────────────────────────────────────┐
│ Customer 360 View: John Doe (CUST-5678)              [Refresh]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ⚠️  Warning: 1 system unavailable (Dynamics 365)                │
│                                                                  │
│ ┌────────────────────┐  ┌────────────────────┐  ┌─────────────┐│
│ │ 🎫 ServiceNow      │  │ ❌ Dynamics 365    │  │ 📄 SharePoint││
│ │ ✓ Connected        │  │ ⚠️  Timeout Error  │  │ ✓ Connected  ││
│ │                    │  │                    │  │              ││
│ │ Open Tickets: 2    │  │ Connection timeout │  │ Documents: 3 ││
│ │ Closed: 15         │  │ after 5 seconds    │  │              ││
│ │ Avg Resolve: 18.5h │  │                    │  │ ✓ Contract   ││
│ │                    │  │ [Retry Query]      │  │ ✓ Proposal   ││
│ └────────────────────┘  └────────────────────┘  └─────────────┘│
│                                                                  │
│ 🤖 AI Insights (Partial - Confidence Reduced)                   │
│ ⚠️  Analysis based on ServiceNow + SharePoint only              │
│                                                                  │
│ • Pattern detected: 2 open tickets (CRM data unavailable)       │
│ • Recommendation: Retry Dynamics 365 for purchase history       │
└──────────────────────────────────────────────────────────────────┘
```

**Error Handling Matrix**:

| Scenario | Systems Available | Behavior |
|----------|------------------|----------|
| All succeed | 3/3 | Return full data, normal confidence scores |
| 1 system fails | 2/3 | Return partial data, lower confidence, show error UI |
| 2 systems fail | 1/3 | Return minimal data, warning banner, suggest manual lookup |
| All fail | 0/3 | Return error page with retry button, log critical alert |

**Definition of Done**:
- [ ] System returns partial results when 1-2 systems fail
- [ ] Each system has independent 5-second timeout
- [ ] Failed systems clearly indicated in response and UI
- [ ] User can retry individual failed systems
- [ ] AI adjusts confidence scores based on available data
- [ ] All failures logged for monitoring dashboard

**Technical Notes**:
- Use `asyncio.gather(return_exceptions=True)` to capture individual failures
- Implement per-system error categorization (timeout, auth error, rate limit, server error)
- Store failure events in `audit_logs` table

---

### **US-F3-004: Intelligent Caching with Redis**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** System Admin (Michael Wong)
- **I want to** cache frequently accessed customer data in Redis to reduce external API calls and improve response times
- **So that** the system can handle more concurrent users and reduce costs (API call charges)

**Acceptance Criteria**:
1. ✅ **Cache Hit**: Subsequent queries for same customer return from Redis in <200ms
2. ✅ **TTL Configuration**: Cache expires after 1 day (86400 seconds) by default
3. ✅ **Cache Key**: Use format `customer_360:{customer_id}` for consistency
4. ✅ **Cache Miss Handling**: On cache miss, query all systems and populate cache
5. ✅ **Cache Stats**: Track cache hit rate in monitoring dashboard (target ≥60%)
6. ✅ **Manual Invalidation**: Admin can manually clear cache for specific customer
7. ✅ **Automatic Invalidation**: Cache clears when customer data is updated (future enhancement)

**Caching Strategy**:
```python
# Cache flow
1. Check Redis for key `customer_360:{customer_id}`
2. If found (cache hit):
   - Return cached data immediately (<200ms)
   - Update cache metadata (last_accessed, hit_count)
3. If not found (cache miss):
   - Query all 3 systems in parallel
   - Run AI correlation analysis
   - Store complete response in Redis (TTL 1 day)
   - Return response to user
```

**Cache Statistics Dashboard**:
```
┌──────────────────────────────────────────────────────────────┐
│ Cross-System Correlation - Cache Performance                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Cache Hit Rate: 67% ████████████░░░░░░░ (Target: ≥60%)     │
│                                                              │
│ Today's Stats:                                               │
│   Total Queries: 1,247                                       │
│   Cache Hits: 835                                            │
│   Cache Misses: 412                                          │
│                                                              │
│ Average Response Time:                                       │
│   Cache Hit: 185ms                                           │
│   Cache Miss: 4,320ms                                        │
│                                                              │
│ Cost Savings:                                                │
│   API Calls Avoided: 2,505 (835 hits × 3 systems)          │
│   Estimated Savings: $12.53/day                             │
│                                                              │
│ Top Cached Customers (by hit count):                        │
│   1. CUST-5678: 45 hits                                      │
│   2. CUST-1234: 38 hits                                      │
│   3. CUST-9012: 29 hits                                      │
└──────────────────────────────────────────────────────────────┘
```

**Cache Invalidation API**:
```python
@router.delete("/api/correlation/cache/{customer_id}")
async def invalidate_cache(customer_id: str):
    """
    Manually invalidate cache for specific customer
    
    Use cases:
    - Customer data was updated in source system
    - Admin wants to force fresh query
    - Testing/debugging
    """
    cache_key = f"customer_360:{customer_id}"
    deleted = await redis.delete(cache_key)
    
    return {
        "message": "Cache invalidated" if deleted else "Cache key not found",
        "customer_id": customer_id,
        "cache_key": cache_key
    }
```

**Definition of Done**:
- [ ] Cache hit returns data in <200ms (P95)
- [ ] Cache hit rate ≥60% after 1 week of production use
- [ ] Admin can manually invalidate cache via API
- [ ] Cache stats displayed in monitoring dashboard
- [ ] TTL configuration easily adjustable (environment variable)

**Technical Notes**:
- Use Redis `SETEX` command for atomic set + TTL
- Store as compressed JSON to save memory
- Implement cache warming for VIP customers (background job)

---

## 3.3 Technical Implementation (Detailed)

### 3.3.1 CrossSystemCorrelationAgent Class

```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SystemQueryResult:
    """Result from querying a single system"""
    system_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    query_time_ms: int = 0

class CrossSystemCorrelationAgent:
    """
    Agent that queries multiple enterprise systems and correlates data using AI
    """
    
    def __init__(
        self,
        servicenow_adapter,
        dynamics365_adapter,
        sharepoint_adapter,
        llm_service,
        cache_service,
        config: Dict[str, Any]
    ):
        self.servicenow = servicenow_adapter
        self.dynamics365 = dynamics365_adapter
        self.sharepoint = sharepoint_adapter
        self.llm = llm_service
        self.cache = cache_service
        self.config = config
        
        # Configuration
        self.query_timeout = config.get("query_timeout_seconds", 5)
        self.cache_ttl = config.get("cache_ttl_seconds", 86400)  # 1 day
        self.enable_caching = config.get("enable_caching", True)
    
    async def get_customer_360_view(
        self,
        customer_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive customer view by querying all systems
        
        Args:
            customer_id: Customer ID to query
            force_refresh: Skip cache and force fresh query
            
        Returns:
            Complete customer 360 view with AI insights
        """
        start_time = datetime.utcnow()
        
        # 1. Check cache (unless force_refresh)
        if self.enable_caching and not force_refresh:
            cached_result = await self._check_cache(customer_id)
            if cached_result:
                logger.info(f"Cache hit for customer {customer_id}")
                cached_result["cache_hit"] = True
                return cached_result
        
        logger.info(f"Cache miss for customer {customer_id}, querying systems")
        
        # 2. Query all systems in parallel
        system_results = await self._query_all_systems(customer_id)
        
        # 3. Calculate success rate
        successful_systems = sum(1 for r in system_results if r.success)
        total_systems = len(system_results)
        success_rate = f"{successful_systems}/{total_systems}"
        
        # 4. Build response data
        response_data = {}
        for result in system_results:
            response_data[result.system_name] = {
                "success": result.success,
                **({"data": result.data} if result.success else {}),
                **({"error": result.error, "error_code": result.error_code} if not result.success else {}),
                "query_time_ms": result.query_time_ms
            }
        
        # 5. Run AI correlation analysis (if at least 1 system succeeded)
        insights = None
        if successful_systems > 0:
            insights = await self._generate_insights(
                customer_id,
                response_data,
                successful_systems,
                total_systems
            )
        
        # 6. Build final response
        query_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        final_response = {
            "customer_id": customer_id,
            "query_time_ms": query_time_ms,
            "cache_hit": False,
            "success_rate": success_rate,
            "systems_queried": [r.system_name for r in system_results],
            "data": response_data,
            "insights": insights,
            "timestamp": start_time.isoformat()
        }
        
        # 7. Cache result (if full success)
        if self.enable_caching and successful_systems == total_systems:
            await self._save_to_cache(customer_id, final_response)
        
        logger.info(
            f"Customer 360 query completed for {customer_id}: "
            f"{query_time_ms}ms, {success_rate} systems successful"
        )
        
        return final_response
    
    async def _query_all_systems(
        self,
        customer_id: str
    ) -> List[SystemQueryResult]:
        """
        Query all enterprise systems in parallel with timeout
        
        Returns list of SystemQueryResult (success or failure for each)
        """
        # Create tasks for parallel execution
        tasks = {
            "servicenow": self._query_servicenow(customer_id),
            "dynamics365": self._query_dynamics365(customer_id),
            "sharepoint": self._query_sharepoint(customer_id)
        }
        
        # Execute all tasks in parallel (with timeouts)
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        
        # Convert results to SystemQueryResult objects
        system_results = []
        for system_name, result in zip(tasks.keys(), results):
            if isinstance(result, SystemQueryResult):
                system_results.append(result)
            elif isinstance(result, Exception):
                # Query raised exception
                system_results.append(SystemQueryResult(
                    system_name=system_name,
                    success=False,
                    error=str(result),
                    error_code="EXCEPTION"
                ))
            else:
                # Should not happen, but handle gracefully
                system_results.append(SystemQueryResult(
                    system_name=system_name,
                    success=False,
                    error="Unknown error",
                    error_code="UNKNOWN"
                ))
        
        return system_results
    
    async def _query_servicenow(self, customer_id: str) -> SystemQueryResult:
        """Query ServiceNow for customer tickets"""
        start_time = datetime.utcnow()
        
        try:
            # Query with timeout
            tickets = await asyncio.wait_for(
                self.servicenow.get_customer_tickets(customer_id),
                timeout=self.query_timeout
            )
            
            query_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return SystemQueryResult(
                system_name="servicenow",
                success=True,
                data={
                    "tickets": {
                        "open": len([t for t in tickets if t["status"] == "Open"]),
                        "closed": len([t for t in tickets if t["status"] == "Closed"]),
                        "total": len(tickets)
                    },
                    "recent_tickets": tickets[:5],  # Last 5 tickets
                    "avg_resolution_time_hours": self._calculate_avg_resolution(tickets)
                },
                query_time_ms=query_time_ms
            )
            
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="servicenow",
                success=False,
                error=f"Connection timeout after {self.query_timeout} seconds",
                error_code="TIMEOUT"
            )
        except Exception as e:
            logger.error(f"ServiceNow query failed: {e}", exc_info=True)
            return SystemQueryResult(
                system_name="servicenow",
                success=False,
                error=str(e),
                error_code="API_ERROR"
            )
    
    async def _query_dynamics365(self, customer_id: str) -> SystemQueryResult:
        """Query Dynamics 365 for customer profile and purchase history"""
        start_time = datetime.utcnow()
        
        try:
            # Query with timeout
            profile, orders = await asyncio.wait_for(
                asyncio.gather(
                    self.dynamics365.get_customer_profile(customer_id),
                    self.dynamics365.get_purchase_history(customer_id)
                ),
                timeout=self.query_timeout
            )
            
            query_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return SystemQueryResult(
                system_name="dynamics365",
                success=True,
                data={
                    "profile": profile,
                    "purchase_history": {
                        "total_orders": len(orders),
                        "total_spent": sum(o["amount"] for o in orders),
                        "recent_orders": orders[:5]  # Last 5 orders
                    }
                },
                query_time_ms=query_time_ms
            )
            
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="dynamics365",
                success=False,
                error=f"Connection timeout after {self.query_timeout} seconds",
                error_code="TIMEOUT"
            )
        except Exception as e:
            logger.error(f"Dynamics 365 query failed: {e}", exc_info=True)
            return SystemQueryResult(
                system_name="dynamics365",
                success=False,
                error=str(e),
                error_code="API_ERROR"
            )
    
    async def _query_sharepoint(self, customer_id: str) -> SystemQueryResult:
        """Query SharePoint for customer documents"""
        start_time = datetime.utcnow()
        
        try:
            # Query with timeout
            documents = await asyncio.wait_for(
                self.sharepoint.search_customer_documents(customer_id),
                timeout=self.query_timeout
            )
            
            query_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return SystemQueryResult(
                system_name="sharepoint",
                success=True,
                data={
                    "documents": documents[:10],  # Top 10 documents
                    "document_count": len(documents)
                },
                query_time_ms=query_time_ms
            )
            
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="sharepoint",
                success=False,
                error=f"Connection timeout after {self.query_timeout} seconds",
                error_code="TIMEOUT"
            )
        except Exception as e:
            logger.error(f"SharePoint query failed: {e}", exc_info=True)
            return SystemQueryResult(
                system_name="sharepoint",
                success=False,
                error=str(e),
                error_code="API_ERROR"
            )
    
    async def _generate_insights(
        self,
        customer_id: str,
        system_data: Dict[str, Any],
        successful_systems: int,
        total_systems: int
    ) -> Dict[str, Any]:
        """
        Use GPT-4o to correlate data and generate insights
        
        Returns dict with patterns, anomalies, correlations, timeline, recommendations
        """
        start_time = datetime.utcnow()
        
        try:
            # Build LLM prompt
            prompt = self._build_correlation_prompt(customer_id, system_data)
            
            # Call GPT-4o with 2-second timeout
            response = await asyncio.wait_for(
                self.llm.generate(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                ),
                timeout=2.0
            )
            
            insights = json.loads(response["content"])
            
            # Add metadata
            generation_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            insights["generation_time_ms"] = generation_time_ms
            insights["model"] = response.get("model", "gpt-4o")
            insights["tokens_used"] = response.get("tokens_used", 0)
            insights["cost_usd"] = response.get("cost_usd", 0)
            
            # Add warning if partial data
            if successful_systems < total_systems:
                failed_systems = [name for name, data in system_data.items() if not data["success"]]
                insights["warning"] = f"Analysis based on partial data ({', '.join(failed_systems)} unavailable)"
                insights["confidence_adjusted"] = True
            
            return insights
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM insight generation timed out for customer {customer_id}")
            return {"error": "Insight generation timed out", "fallback": True}
        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}", exc_info=True)
            return {"error": str(e), "fallback": True}
    
    def _build_correlation_prompt(
        self,
        customer_id: str,
        system_data: Dict[str, Any]
    ) -> str:
        """Build structured prompt for LLM correlation analysis"""
        
        # Extract successful system data
        servicenow_data = system_data.get("servicenow", {}).get("data", {})
        dynamics365_data = system_data.get("dynamics365", {}).get("data", {})
        sharepoint_data = system_data.get("sharepoint", {}).get("data", {})
        
        prompt = f"""
You are an AI assistant analyzing customer data from multiple enterprise systems.

Customer ID: {customer_id}

ServiceNow Data (Support Tickets):
{json.dumps(servicenow_data, indent=2) if servicenow_data else "Data unavailable"}

Dynamics 365 Data (CRM):
{json.dumps(dynamics365_data, indent=2) if dynamics365_data else "Data unavailable"}

SharePoint Data (Documents):
{json.dumps(sharepoint_data, indent=2) if sharepoint_data else "Data unavailable"}

Analyze this data and provide:
1. **Patterns**: Any recurring issues, trends, or behavior patterns
2. **Anomalies**: Unusual activity that requires attention
3. **Correlations**: Relationships between data across systems
4. **Timeline**: Key events in chronological order
5. **Recommendations**: Actionable next steps for customer service agent

For each insight, provide:
- description: Brief explanation (1-2 sentences)
- confidence: Score 0-100 (higher = more confident)
- evidence: List of data points supporting this insight
- type: Category (e.g., "recurring_issue", "suspicious_activity")

Output as JSON:
{{
  "patterns": [
    {{"description": "...", "confidence": 85, "evidence": ["..."], "type": "..."}}
  ],
  "anomalies": [...],
  "correlations": [...],
  "timeline": [
    {{"date": "2025-11-15", "event": "...", "system": "..."}}
  ],
  "recommendations": [
    {{"description": "...", "confidence": 88, "action": "...", "rationale": "..."}}
  ]
}}
"""
        return prompt
    
    async def _check_cache(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for customer data"""
        cache_key = f"customer_360:{customer_id}"
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def _save_to_cache(self, customer_id: str, data: Dict[str, Any]):
        """Save customer data to Redis cache with TTL"""
        cache_key = f"customer_360:{customer_id}"
        await self.cache.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(data)
        )
        logger.info(f"Cached customer 360 data for {customer_id} (TTL: {self.cache_ttl}s)")
    
    def _calculate_avg_resolution(self, tickets: List[Dict[str, Any]]) -> float:
        """Calculate average ticket resolution time in hours"""
        resolved_tickets = [
            t for t in tickets 
            if t["status"] == "Closed" and t.get("resolved_at")
        ]
        
        if not resolved_tickets:
            return 0.0
        
        total_hours = 0
        for ticket in resolved_tickets:
            created = datetime.fromisoformat(ticket["created_at"])
            resolved = datetime.fromisoformat(ticket["resolved_at"])
            hours = (resolved - created).total_seconds() / 3600
            total_hours += hours
        
        return round(total_hours / len(resolved_tickets), 1)
```

---

## 3.4 API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/correlation", tags=["correlation"])

@router.post("/customer-360")
async def get_customer_360(
    customer_id: str,
    force_refresh: bool = Query(default=False, description="Skip cache"),
    correlation_agent: CrossSystemCorrelationAgent = Depends(get_correlation_agent)
):
    """
    Get comprehensive customer 360 view
    
    **Request Body**:
    ```json
    {
      "customer_id": "CUST-5678"
    }
    ```
    
    **Query Parameters**:
    - `force_refresh`: Skip cache and force fresh query (default: false)
    
    **Response**: Complete customer 360 view with AI insights
    """
    try:
        result = await correlation_agent.get_customer_360_view(
            customer_id=customer_id,
            force_refresh=force_refresh
        )
        return result
    except Exception as e:
        logger.error(f"Customer 360 query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query customer data: {str(e)}"
        )

@router.delete("/cache/{customer_id}")
async def invalidate_cache(
    customer_id: str,
    cache_service = Depends(get_cache_service)
):
    """
    Manually invalidate cache for specific customer
    
    **Use cases**:
    - Customer data updated in source system
    - Admin wants to force fresh query
    - Testing/debugging
    
    **Response**:
    ```json
    {
      "message": "Cache invalidated",
      "customer_id": "CUST-5678"
    }
    ```
    """
    cache_key = f"customer_360:{customer_id}"
    deleted = await cache_service.delete(cache_key)
    
    return {
        "message": "Cache invalidated" if deleted else "Cache key not found",
        "customer_id": customer_id,
        "cache_key": cache_key,
        "deleted": deleted
    }

@router.get("/cache/stats")
async def get_cache_stats(
    cache_service = Depends(get_cache_service),
    db_session = Depends(get_db_session)
):
    """
    Get cache performance statistics
    
    **Response**:
    ```json
    {
      "hit_rate": 0.67,
      "total_queries": 1247,
      "cache_hits": 835,
      "cache_misses": 412,
      "avg_response_time_hit_ms": 185,
      "avg_response_time_miss_ms": 4320
    }
    ```
    """
    # Query stats from database (logged in audit_logs or metrics table)
    stats = await db_session.execute("""
        SELECT 
            COUNT(*) as total_queries,
            SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) as cache_hits,
            SUM(CASE WHEN cache_hit = false THEN 1 ELSE 0 END) as cache_misses,
            AVG(CASE WHEN cache_hit = true THEN query_time_ms END) as avg_time_hit,
            AVG(CASE WHEN cache_hit = false THEN query_time_ms END) as avg_time_miss
        FROM correlation_queries
        WHERE created_at >= NOW() - INTERVAL '1 day'
    """)
    row = stats.fetchone()
    
    return {
        "hit_rate": round(row["cache_hits"] / row["total_queries"], 2) if row["total_queries"] > 0 else 0,
        "total_queries": row["total_queries"],
        "cache_hits": row["cache_hits"],
        "cache_misses": row["cache_misses"],
        "avg_response_time_hit_ms": round(row["avg_time_hit"]) if row["avg_time_hit"] else 0,
        "avg_response_time_miss_ms": round(row["avg_time_miss"]) if row["avg_time_miss"] else 0
    }
```

---

## 3.5 External System Adapters

### ServiceNow Adapter

```python
import httpx
from typing import List, Dict, Any

class ServiceNowAdapter:
    """Adapter for ServiceNow REST API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = (username, password)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            auth=self.auth,
            timeout=5.0
        )
    
    async def get_customer_tickets(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all tickets for customer
        
        ServiceNow REST API:
        GET /api/now/table/incident?sysparm_query=caller_id={customer_id}
        """
        response = await self.client.get(
            "/api/now/table/incident",
            params={
                "sysparm_query": f"caller_id={customer_id}",
                "sysparm_limit": 100,
                "sysparm_fields": "number,short_description,state,priority,sys_created_on,sys_updated_on"
            }
        )
        response.raise_for_status()
        
        data = response.json()
        tickets = data.get("result", [])
        
        # Transform to standard format
        return [
            {
                "ticket_id": t["number"],
                "subject": t["short_description"],
                "status": self._map_state(t["state"]),
                "priority": int(t.get("priority", 3)),
                "created_at": t["sys_created_on"],
                "updated_at": t["sys_updated_on"]
            }
            for t in tickets
        ]
    
    def _map_state(self, state: str) -> str:
        """Map ServiceNow state to standard status"""
        state_map = {
            "1": "New",
            "2": "In Progress",
            "3": "On Hold",
            "6": "Resolved",
            "7": "Closed"
        }
        return state_map.get(state, "Unknown")
```

### Dynamics 365 Adapter

```python
class Dynamics365Adapter:
    """Adapter for Dynamics 365 Web API"""
    
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self.headers,
            timeout=5.0
        )
    
    async def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer profile
        
        Dynamics 365 Web API:
        GET /api/data/v9.2/contacts({customer_id})
        """
        response = await self.client.get(f"/api/data/v9.2/contacts({customer_id})")
        response.raise_for_status()
        
        data = response.json()
        return {
            "name": data.get("fullname"),
            "email": data.get("emailaddress1"),
            "phone": data.get("telephone1"),
            "tier": data.get("customertypecode"),  # Custom field
            "account_status": "Active" if data.get("statecode") == 0 else "Inactive",
            "member_since": data.get("createdon")
        }
    
    async def get_purchase_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer purchase history
        
        Dynamics 365 Web API:
        GET /api/data/v9.2/salesorders?$filter=_customerid_value eq {customer_id}
        """
        response = await self.client.get(
            "/api/data/v9.2/salesorders",
            params={
                "$filter": f"_customerid_value eq {customer_id}",
                "$top": 50,
                "$orderby": "createdon desc"
            }
        )
        response.raise_for_status()
        
        data = response.json()
        orders = data.get("value", [])
        
        return [
            {
                "order_id": o.get("ordernumber"),
                "date": o.get("createdon"),
                "amount": float(o.get("totalamount", 0)),
                "currency": o.get("transactioncurrencyid"),
                "status": o.get("statecode")
            }
            for o in orders
        ]
```

### SharePoint Adapter

```python
class SharePointAdapter:
    """Adapter for SharePoint Search API"""
    
    def __init__(self, site_url: str, access_token: str):
        self.site_url = site_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=5.0
        )
    
    async def search_customer_documents(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Search SharePoint for customer documents
        
        SharePoint Search API:
        GET /_api/search/query?querytext='customer_id:{customer_id}'
        """
        search_url = f"{self.site_url}/_api/search/query"
        
        response = await self.client.get(
            search_url,
            params={
                "querytext": f"'{customer_id}'",
                "selectproperties": "'Title,Path,LastModifiedTime,FileType'",
                "rowlimit": 50
            }
        )
        response.raise_for_status()
        
        data = response.json()
        results = data.get("d", {}).get("query", {}).get("PrimaryQueryResult", {}).get("RelevantResults", {}).get("Table", {}).get("Rows", {}).get("results", [])
        
        documents = []
        for result in results:
            cells = {cell["Key"]: cell["Value"] for cell in result.get("Cells", {}).get("results", [])}
            documents.append({
                "title": cells.get("Title"),
                "url": cells.get("Path"),
                "modified_at": cells.get("LastModifiedTime"),
                "file_type": cells.get("FileType")
            })
        
        return documents
```

---

## 3.6 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Customer 360 query latency (cache miss) | P95 < 5 seconds | APM monitoring |
| | Customer 360 query latency (cache hit) | P95 < 200ms | APM monitoring |
| | AI insight generation time | < 2 seconds | LLM API logging |
| | External API timeout | 5 seconds per system | Configuration |
| **Scalability** | Concurrent queries | 50+ simultaneously | Load testing |
| | External API rate limits | ServiceNow: 1000/hr, Dynamics: 5000/day, SharePoint: throttled | API monitoring |
| **Reliability** | Graceful degradation | Return partial results if 1-2 systems fail | Integration tests |
| | Retry logic | 3 attempts with exponential backoff | Configuration |
| | Circuit breaker | Open after 5 consecutive failures | Resilience library |
| **Caching** | Cache hit rate | ≥60% after 1 week | Redis metrics |
| | Cache TTL | 1 day (configurable) | Configuration |
| | Cache memory usage | <500MB for 10K customers | Redis monitoring |
| **Cost** | LLM cost per query | <$0.05 | Token tracking |
| | External API cost per query | <$0.10 | API billing |
| **Observability** | Query success rate | ≥95% | Monitoring dashboard |
| | System-specific error rate | Track failures by system | Error logging |
| | AI insight accuracy | 80%+ confidence scores | User feedback |

---

## 3.7 Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_customer_360_success():
    """Test successful customer 360 query with all systems"""
    agent = CrossSystemCorrelationAgent(
        servicenow_adapter=AsyncMock(),
        dynamics365_adapter=AsyncMock(),
        sharepoint_adapter=AsyncMock(),
        llm_service=AsyncMock(),
        cache_service=AsyncMock(),
        config={"query_timeout_seconds": 5, "enable_caching": False}
    )
    
    # Mock system responses
    agent.servicenow.get_customer_tickets.return_value = [{"ticket_id": "CS-1234"}]
    agent.dynamics365.get_customer_profile.return_value = {"name": "John Doe"}
    agent.dynamics365.get_purchase_history.return_value = [{"order_id": "12345"}]
    agent.sharepoint.search_customer_documents.return_value = [{"title": "Contract"}]
    
    # Mock LLM response
    agent.llm.generate.return_value = {
        "content": json.dumps({"patterns": [], "anomalies": []}),
        "model": "gpt-4o",
        "tokens_used": 1000
    }
    
    result = await agent.get_customer_360_view("CUST-5678")
    
    assert result["success_rate"] == "3/3"
    assert result["data"]["servicenow"]["success"] is True
    assert result["data"]["dynamics365"]["success"] is True
    assert result["data"]["sharepoint"]["success"] is True
    assert "insights" in result

@pytest.mark.asyncio
async def test_customer_360_partial_failure():
    """Test partial failure (1 system times out)"""
    agent = CrossSystemCorrelationAgent(...)
    
    # Mock: ServiceNow and SharePoint succeed, Dynamics 365 times out
    agent.servicenow.get_customer_tickets.return_value = [{"ticket_id": "CS-1234"}]
    agent.dynamics365.get_customer_profile.side_effect = asyncio.TimeoutError()
    agent.sharepoint.search_customer_documents.return_value = [{"title": "Contract"}]
    
    result = await agent.get_customer_360_view("CUST-5678")
    
    assert result["success_rate"] == "2/3"
    assert result["data"]["servicenow"]["success"] is True
    assert result["data"]["dynamics365"]["success"] is False
    assert result["data"]["dynamics365"]["error_code"] == "TIMEOUT"
    assert result["data"]["sharepoint"]["success"] is True
```

### Integration Tests

- Test end-to-end query with real external APIs (staging environment)
- Test cache hit/miss scenarios
- Test AI insight generation with real LLM
- Test graceful degradation with simulated failures

### Load Tests

- 50 concurrent customer 360 queries
- Measure P50, P95, P99 latencies
- Verify cache hit rate ≥60%
- Monitor external API rate limits

---

## 3.8 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| External API rate limits exceeded | **Medium** | High | Implement rate limiting, caching, circuit breakers |
| One system frequently unavailable | Medium | Medium | Graceful degradation, SLA monitoring, escalation alerts |
| LLM insight generation slow/expensive | Low | Medium | Optimize prompts, cache insights, set token limits |
| Redis cache memory exhaustion | Low | Medium | Set max memory policy (evict LRU), monitor usage |
| Data staleness (cached data outdated) | Medium | Low | 1-day TTL, manual invalidation API, future: webhook invalidation |

---

## 3.9 Future Enhancements (Post-MVP)

1. **Real-time Cache Invalidation**: Webhooks from source systems trigger cache invalidation
2. **More Systems**: Add Salesforce, Zendesk, Slack integration
3. **Predictive Analytics**: ML model predicts customer churn risk based on cross-system patterns
4. **Automated Actions**: AI suggests and executes actions (e.g., "Send apology email")
5. **Historical Trending**: Track customer metrics over time (3-month, 6-month, 1-year views)
6. **Custom Queries**: Allow users to define custom correlation queries
7. **Data Export**: Export customer 360 view to PDF/Excel for offline analysis

---

**Next Feature**: [F4. Cross-Scenario Collaboration →](./feature-04-collaboration.md)
