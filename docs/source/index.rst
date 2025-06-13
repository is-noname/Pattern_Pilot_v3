Pattern Pilot 3.0 Trading Terminal Documentation
===============================================

Professional Asset-Pattern-Analysis for Crypto/Stocks with automatic Pattern-Detection.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   api/modules
   architecture
   patterns
   exchanges
   troubleshooting

Architecture Overview
--------------------

.. autosummary::
   :toctree: api/
   :recursive:

   core.market_engine
   analyze.pattern_analyzer
   config.settings

Quick Start
-----------

.. code-block:: python

   from core.market_engine import market_engine
   
   # Get OHLCV data
   df = market_engine.get_ohlcv("BTC/USDT", "1d", 200)
   
   # Detect patterns
   patterns = market_engine.detect_patterns(df)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`