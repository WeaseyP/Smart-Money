Dual-Signal 'Smart Money' Tracker
Project Objective

This project aims to develop a sophisticated signal generation tool that systematically identifies potential investment opportunities in the stock market. It is designed to create an analytical edge by filtering the vast universe of equities based on two distinct and powerful indicators: long-term institutional conviction ("smart money" or "whales") and short-term, high-conviction insider buying.

The core thesis is that the alignment of these two signals—a stock validated by long-term, sophisticated capital that is simultaneously being purchased by its most informed insiders—represents a potent, actionable event.
The Core Strategy: A Two-Layered Approach

The system's logic is built on a dual-filter-and-trigger mechanism that leverages different SEC filings and operates on different timescales.
Layer 1: The "Whale Watchlist" (The Strategic Filter)

    Data Source: Quarterly SEC Form 13F filings.

    Process: The system first identifies a high-conviction "hunting ground" by analyzing the holdings of a curated list of elite institutional investment managers. A stock is added to the "Whale Watchlist" if one or more of these funds initiates a new position, significantly increases an existing one, or shows "whale clustering" (multiple tracked funds owning the same stock).

    Outcome: A dynamic, high-potential list of stocks that is refreshed quarterly, providing a stable universe for monitoring.

Layer 2: The Insider Action (The Tactical Trigger)

    Data Source: Daily SEC Form 4 filings.

    Process: The system monitors the "Whale Watchlist" in near real-time for significant insider purchases. The logic is highly selective, focusing exclusively on open-market buys (Transaction Code 'P') made by C-suite executives (CEO, CFO, COO) or notable "cluster buys" from multiple insiders.

    Outcome: An alert is generated only when a significant insider buy occurs in a stock that is currently on the "Whale Watchlist".

Technical Stack

    Core Language: Python

    Data Analysis & Manipulation: Pandas, NumPy

    Database: PostgreSQL (chosen for its concurrency management and JSONB support)

    Database Interaction: SQLAlchemy

    Configuration: python-dotenv

    Data Acquisition: requests, python-socketio (for potential real-time streams)

Project Status & Execution Plan

The project is being developed in distinct phases, with the initial focus on creating a robust backend and a historical simulator.

    Phase 1: Core Engine & Historical Simulator (MVP): Build the core analysis logic and a command-line tool to validate the strategy against historical data. This allows for refinement of the signal criteria before live deployment.

    Phase 2: Live Data Acquisition: Develop automated scripts to fetch live 13F (quarterly) and Form 4 (daily) data to keep the database current.

    Future Enhancements: The product backlog includes developing a signal scoring system, an automated alerting mechanism (e.g., via Telegram or email), and a user-friendly web-based dashboard for data visualization.
