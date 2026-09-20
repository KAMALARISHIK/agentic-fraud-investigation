import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter

import config
from app.schemas import StatsResponse

router = APIRouter(tags=["Stats"])
logger = logging.getLogger("fraud_agent.api.stats")

@router.get("/stats", response_model=StatsResponse)
def get_operational_stats():
    """Retrieve aggregate performance and operational metrics across all investigated cases."""
    cases_dir = config.CASES_OUTPUT_DIR
    
    total_cases = 0
    verdict_counts = Counter()
    pattern_counts = Counter()
    total_exposure = 0.0
    sar_filed_count = 0
    total_latency = 0.0
    total_tokens = 0
    tool_counts = Counter()
    
    for file_path in sorted(cases_dir.glob("HHG-*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            total_cases += 1
            case_obj = data.get("case", {})
            verdict = case_obj.get("verdict", "uncertain")
            pattern = case_obj.get("pattern", "none")
            exp = float(case_obj.get("exposure_usd", 0.0))
            
            verdict_counts[verdict] += 1
            pattern_counts[pattern] += 1
            total_exposure += exp
            
            sar_obj = data.get("sar", {})
            if sar_obj.get("file", False):
                sar_filed_count += 1
                
            total_latency += float(data.get("latency_s", 0.0))
            
            toks = data.get("tokens", 0)
            if isinstance(toks, dict):
                total_tokens += int(toks.get("total", 0))
            elif isinstance(toks, (int, float)):
                total_tokens += int(toks)
            
            tool_calls_data = data.get("tool_calls", [])
            if isinstance(tool_calls_data, list):
                for tc in tool_calls_data:
                    if isinstance(tc, dict):
                        tool_name = tc.get("tool", "unknown")
                        tool_counts[tool_name] += 1
                    elif isinstance(tc, str):
                        tool_counts[tc] += 1
            elif isinstance(tool_calls_data, (int, float)):
                tool_counts["mcp_graph_tools"] += int(tool_calls_data)
                
        except Exception as e:
            logger.error(f"Error reading stats for {file_path.name}: {e}")
            
    avg_latency = round(total_latency / max(1, total_cases), 2)
    
    return StatsResponse(
        total_cases=total_cases,
        verdict_distribution=dict(verdict_counts),
        pattern_distribution=dict(pattern_counts),
        total_exposure_usd=round(total_exposure, 2),
        total_sar_filed=sar_filed_count,
        avg_latency_s=avg_latency,
        total_tokens_used=total_tokens,
        tool_calls_breakdown=dict(tool_counts)
    )
