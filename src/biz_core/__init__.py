"""BizForecast-Shop: Multi-Agent for SMB E-commerce.

Layered architecture (only `framework` is allowed to import agentscope):

  biz_core.framework    — adapter layer (the ONLY importer of agentscope)
  biz_core.agents       — application layer: 4 role agents + orchestrator
  biz_core.tools        — application layer: MCP hub, skill chain
  biz_core.data         — application layer: multi-platform data sources
  biz_core.review       — application layer: review engine + echo detector
  biz_core.router       — LiteLLM multi-model routing (independent)
  biz_core.telemetry    — OTel + Langfuse tracing (independent)
  biz_core.prediction   — Prophet / LSTM forecasting (independent)
"""

__version__ = "0.1.0"
