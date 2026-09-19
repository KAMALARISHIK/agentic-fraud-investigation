# FraudSight AI: Agentic Fraud Investigation on TigerGraph

An AI agent that investigates suspicious card activity like a fraud analyst: it opens a case, gathers evidence from a TigerGraph knowledge graph, assesses risk and uncertainty, requests more evidence when needed, recommends the next best action within policy and approval limits, and stores the case in memory for future investigations.

Built for the TigerGraph Agentic Fraud Investigation hackathon.

## What it does
- Investigates alerts triggered by a risk score, a customer report, or an analyst request
- Finds fraud patterns using GSQL queries and graph algorithms (shared devices, small-authorization sequences, out-of-region use, connected-card rings)
- Reaches the graph through TigerGraph MCP tools
- Uses GraphRAG: connected graph evidence, policy text, and similar past cases are passed to the LLM
- Enforces the bank's fraud policy in code: allowed actions, approval routes (auto / L1 / L2), and when a Suspicious Activity Report is required
- Asks for more evidence (customer validation, step-up authentication) when the signals are uncertain, then updates its recommendation
- Explains its reasoning and writes every case back to the graph

## Tech stack
TigerGraph Savanna, GSQL, TigerGraph MCP, LangGraph, Gemini, FastAPI, Python

## Repository layout
See the sections below for setup, architecture, and the API.
