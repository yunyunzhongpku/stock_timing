# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese stock index timing strategy system based on CSI All Share Index (中证全指) and SWHY Level-1 industry data. The system implements three classic technical pattern recognition strategies with both individual and combined backtesting capabilities.

## Architecture

### Core Structure
- `stock_timing/` - Main package containing core modules
  - `data_loader.py` - Wind API data loading with fallback to simulated data
  - `metrics/` - Pure calculation functions (follows I/O separation principle)
    - `atr.py` - ATR calculation and threshold adjustment
    - `strategy1_definitions.py` - Multiple Strategy 1 pattern definitions
- `strategy1_validator.py` - Strategy validation and backtesting
- `final_visualization.py` - Results visualization
- `tests/` - Unit tests using pytest

### Data Flow
1. **Data Loading** (`WindDataLoader`): Connects to Wind API or generates demo data
2. **Metrics Calculation** (pure functions): Calculate ATR, strategy signals
3. **Strategy Validation**: Test different pattern definitions against known signals
4. **Visualization**: Generate charts and reports

## Strategy Implementations

### Strategy 1: Decline-Rebound Pattern (with ATR correction)
- Multiple definitions in `Strategy1Definitions` class (5 different approaches)
- ATR-based dynamic threshold adjustment
- Known signals: 52 historical dates for validation

### Strategy 2: Top Switch Pattern
- Based on SWHY industry 52-week high data
- Dual condition filtering: industry count reduction + index decline

### Strategy 3: Triangle Breakout
- Convergence detection with breakout confirmation
- Triple condition validation: convergence + breakout + range narrowing

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
pytest tests/
```

### Strategy Validation
```bash
python strategy1_validator.py
```

### Generate Visualizations
```bash
python final_visualization.py
python visualize_results.py
```

## Key Dependencies
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- scipy >= 1.10.0
- pytest >= 7.0.0
- WindPy (optional, for real data)

## Development Guidelines

### Coding Standards (from Agents.md)
- **I/O Separation**: Data loading (`io/`) vs pure calculations (`metrics/`)
- **Pure Functions**: Metrics should only accept Series/DataFrame, no network access
- **Error Handling**: Explicit protection for NaN/Inf/edge cases
- **Chinese Documentation**: Use Chinese docstrings for domain-specific explanations
- **Reproducibility**: Fixed random seeds (seed=42 in demo data)

### Testing Strategy
- Minimum unit tests for core functions
- Edge case coverage (empty/NaN/short windows)
- Visual validation with PNG outputs
- Offline reproducibility support

## Data Sources
- **Primary**: Wind API (万得) for real market data
- **Fallback**: Geometric Brownian motion simulation with market characteristics
- **Validation**: 52 known signal dates for Strategy 1 pattern matching

## File Structure Notes
- No build configuration files (pure Python project)
- Tests follow pytest conventions
- Results saved as PNG files for manual inspection
- Demo data generation ensures consistent testing environment