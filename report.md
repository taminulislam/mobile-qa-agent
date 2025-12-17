# Framework Analysis: Decision Memo

## Objective
Select the most suitable agent framework for building a Mobile QA Multi-Agent System to automate testing of the Obsidian mobile app on Android.


## Architecture with Google ADK

```
┌─────────────────────────────────────────────────────────────┐
│                     SUPERVISOR AGENT                        │
│  • Orchestrates test execution                              │
│  • Manages Planner and Executor coordination                │
│  • Logs results (Pass/Fail)                                 │
│  • Distinguishes step failures vs test assertion failures   │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   PLANNER AGENT     │       │   EXECUTOR AGENT    │
│                     │       │                     │
│ • Analyzes screen   │       │ • Executes ADB      │
│ • Decides actions   │◄─────►│   commands          │
│ • Uses Gemini       │       │ • Captures screens  │
│   vision            │       │ • Reports status    │
└─────────────────────┘       └─────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │   ADB TOOLS         │
                              │ • tap(x, y)         │
                              │ • type_text(str)    │
                              │ • screenshot()      │
                              │ • swipe()           │
                              │ • press_back()      │
                              └─────────────────────┘
```

---
## Frameworks Evaluated

| Criteria | Google ADK | Agent S3 |
|----------|------------|----------|
| **Multi-Agent Support** | ✅ Native (Supervisor-Worker patterns) | ⚠️ Single agent focus |
| **Free LLM Access** | ✅ Gemini free tier | ❌ Requires paid APIs |
| **Setup Complexity** | ✅ Simple pip install | ❌ Requires grounding model |
| **Documentation** | ✅ Comprehensive | ✅ Good |
| **Customization** | ✅ Highly flexible | ⚠️ More opinionated |
| **Learning Curve** | ✅ Moderate | ❌ Steeper |

---

## Decision: Google ADK

### Primary Reasons

1. **Native Multi-Agent Architecture**: ADK is specifically <mark>designed for building multi-agent systems with clear patterns for agent coordination, delegation, and communication.</mark> This directly aligns with the Supervisor-Planner-Executor architecture required by this challenge.

2. **Free Gemini API Access**: ADK integrates seamlessly with Google's Gemini models, which <mark>offer a generous free tier.</mark> This eliminates API costs during development and testing.

3. **Flexibility for Custom Tools**: ADK's tool system allows <mark>easy integration of custom ADB commands for Android emulator</mark> interaction. We can define tap, swipe, type, and screenshot tools that the agents can use.

4. **Simpler Setup**: A single `pip install google-adk` compared to Agent S3's requirement for multiple model endpoints (main LLM + UI-TARS grounding model).


### Why Not Agent S3?

While Agent S3 achieves impressive benchmarks on AndroidWorld (71.6% accuracy), it presents several challenges for this project:

- **Grounding Model Requirement**: Agent S3 requires UI-TARS-1.5-7B for optimal performance, adding infrastructure complexity
- **Cost**: Requires paid API keys (OpenAI/Anthropic) for the main reasoning model
- **Overkill for Task**: Agent S3 is optimized for complex, long-horizon tasks; our QA tests are relatively focused
- **Single-Agent Focus**: While powerful, it doesn't naturally support the multi-agent Supervisor-Planner-Executor pattern requested

---

## Conclusion

Google ADK provides the ideal balance of multi-agent capabilities, ease of use, and cost-effectiveness for this Mobile QA automation project. Its native support for agent hierarchies and tool integration, combined with free Gemini API access, makes it the clear choice for delivering a production-ready solution within the project timeline.

---
