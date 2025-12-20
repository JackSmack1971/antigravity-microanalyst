from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any, Literal
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .healer_agent import HealerAgent
from ..core.adaptive_config import AdaptiveConfigManager

@dataclass
class SourceHealth:
    """Track health metrics for data sources"""
    source_id: str
    success_rate_24h: float
    avg_latency_ms: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    circuit_breaker_open: bool

@dataclass
class RecoveryStrategy:
    """Recovery strategy for failed operations"""
    strategy_type: Literal["retry", "substitute", "degrade", "skip", "heal"]
    max_attempts: int
    backoff_multiplier: float
    fallback_sources: List[str]
    degradation_acceptable: bool

class SelfHealingEngine:
    """
    Autonomous error recovery system for data acquisition.
    Features:
    - Intelligent Retries with Exponential Backoff
    - Source Substitution (Multi-source rotation)
    - Graceful Degradation (Stale/Cache fallback)
    - Circuit Breaker Protection
    """
    
    def __init__(self, cache_dir: str = "workflow_cache"):
        self.source_health: Dict[str, SourceHealth] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Healer Components
        self.healer = HealerAgent()
        self.adaptive_config = AdaptiveConfigManager()
        
        self._init_default_strategies()
        
        logger.info("SelfHealingEngine initialized with Autonomous Healer")
    
    def _init_default_strategies(self):
        """Initialize recovery strategies for known failure modes"""
        
        # Price data: Critical, must have
        self.recovery_strategies['price_data'] = RecoveryStrategy(
            strategy_type="substitute",
            max_attempts=3,
            backoff_multiplier=2.0,
            fallback_sources=[
                "twelvedata",      # Primary
                "coingecko_api",   # Fallback 1
                "binance_api"      # Fallback 2
            ],
            degradation_acceptable=False
        )
        
        # ETF flows: Important but can use stale data temporarily
        self.recovery_strategies['etf_flows'] = RecoveryStrategy(
            strategy_type="degrade",
            max_attempts=2,
            backoff_multiplier=1.5,
            fallback_sources=["bitbo", "btcetffundflow"],
            degradation_acceptable=True  # Can use yesterday's data
        )
        
        # Screenshots: Nice to have, can skip
        self.recovery_strategies['screenshots'] = RecoveryStrategy(
            strategy_type="skip",
            max_attempts=1,
            backoff_multiplier=1.0,
            fallback_sources=[],
            degradation_acceptable=True
        )

        # DOM Scrapers: Vulnerable to layout changes -> HEAL
        self.recovery_strategies['dom_scrape'] = RecoveryStrategy(
            strategy_type="heal",
            max_attempts=2,
            backoff_multiplier=1.0,
            fallback_sources=[],
            degradation_acceptable=False
        )
    
    async def execute_with_recovery(
        self,
        operation: Callable,
        operation_type: str,
        source_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute operation with intelligent retry and fallback logic
        """
        strategy = self.recovery_strategies.get(
            operation_type,
            RecoveryStrategy("retry", 3, 2.0, [], False)
        )
        
        # Check circuit breaker
        if self._is_circuit_open(source_id):
            logger.warning(f"Circuit breaker open for {source_id}. Trying fallbacks.")
            if strategy.fallback_sources:
                return await self._try_fallback_sources(
                    operation, operation_type, strategy.fallback_sources, **kwargs
                )
            else:
                raise CircuitBreakerOpenError(f"Circuit open for {source_id}")
        
        # Attempt primary source with retries
        for attempt in range(strategy.max_attempts):
            try:
                # Start timer for latency tracking
                start_time = datetime.now()
                
                result = await operation(source_id=source_id, **kwargs)
                
                latency = (datetime.now() - start_time).total_seconds() * 1000
                self._record_success(source_id, latency)
                
                return {
                    "status": "success", 
                    "source": source_id, 
                    "data": result,
                    "attempts": attempt + 1
                }
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {source_id}: {e}")
                self._record_failure(source_id, e)
                
                if attempt < strategy.max_attempts - 1:
                    backoff = strategy.backoff_multiplier ** attempt
                    await asyncio.sleep(backoff)
                else:
                    # Final attempt failed
                    logger.warning(f"All primary attempts failed for {source_id}. Strategy: {strategy.strategy_type}")
                    
                    if strategy.strategy_type == "substitute":
                        return await self._try_fallback_sources(
                            operation, operation_type, strategy.fallback_sources, **kwargs
                        )
                    elif strategy.strategy_type == "degrade":
                        try:
                            return await self._use_degraded_data(operation_type, source_id)
                        except NoDegradedDataAvailableError:
                            if strategy.fallback_sources:
                                return await self._try_fallback_sources(
                                    operation, operation_type, strategy.fallback_sources, **kwargs
                                )
                            raise
                    elif strategy.strategy_type == "skip":
                        return {"status": "skipped", "reason": "non_critical", "source": source_id}
                    elif strategy.strategy_type == "heal":
                        # Attempt to heal the selector
                        return await self._attempt_healing(
                            source_id, 
                            kwargs.get('failed_selector'),
                            kwargs.get('target_description'), 
                            kwargs.get('html_content'),
                            kwargs.get('screenshot_path')
                        )
                    else:
                        raise
    
    async def _try_fallback_sources(
        self,
        operation: Callable,
        operation_type: str,
        fallback_sources: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Try fallback sources in order"""
        for fallback_id in fallback_sources:
            if not self._is_circuit_open(fallback_id):
                try:
                    logger.info(f"Trying fallback source: {fallback_id}")
                    start_time = datetime.now()
                    
                    result = await operation(source_id=fallback_id, **kwargs)
                    
                    latency = (datetime.now() - start_time).total_seconds() * 1000
                    self._record_success(fallback_id, latency)
                    
                    return {
                        "status": "success_fallback",
                        "source": fallback_id,
                        "data": result
                    }
                except Exception as e:
                    logger.error(f"Fallback {fallback_id} failed: {e}")
                    self._record_failure(fallback_id, e)
                    continue
        
        # If all fallbacks fail, check if we can degrade
        strategy = self.recovery_strategies.get(operation_type)
        if strategy and strategy.degradation_acceptable:
            try:
                return await self._use_degraded_data(operation_type, "all_failed")
            except NoDegradedDataAvailableError:
                pass
                
        raise AllSourcesFailedError(f"All sources failed for {operation_type}")
    
    async def _use_degraded_data(self, operation_type: str, source_id: str) -> Dict[str, Any]:
        """Use cached or stale data when acceptable"""
        # Look for matching cache files
        cache_files = list(self.cache_dir.glob(f"*{operation_type}*.json"))
        
        if cache_files:
            latest_cache = max(cache_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_cache, 'r') as f:
                    cached_data = json.load(f)
                
                cache_age = (datetime.now() - datetime.fromtimestamp(latest_cache.stat().st_mtime)).total_seconds() / 3600
                
                logger.warning(f"Using degraded data for {operation_type}. Cache age: {cache_age:.2f}h")
                
                return {
                    "status": "degraded",
                    "source": source_id,
                    "data": cached_data,
                    "warning": "Using stale data from cache",
                    "cache_age_hours": cache_age
                }
            except Exception as e:
                logger.error(f"Failed to read cache file {latest_cache}: {e}")
        
        raise NoDegradedDataAvailableError(f"No cached data for {operation_type}")
    
    def _record_success(self, source_id: str, latency: float):
        """Update health metrics after success"""
        if source_id not in self.source_health:
            self.source_health[source_id] = SourceHealth(
                source_id=source_id,
                success_rate_24h=1.0,
                avg_latency_ms=latency,
                last_success=datetime.now(),
                last_failure=None,
                consecutive_failures=0,
                circuit_breaker_open=False
            )
        else:
            health = self.source_health[source_id]
            health.last_success = datetime.now()
            # Moving average for latency
            health.avg_latency_ms = (health.avg_latency_ms * 0.9) + (latency * 0.1)
            health.consecutive_failures = 0
            health.circuit_breaker_open = False
            
        logger.debug(f"Health updated for {source_id}: Success")
    
    def _record_failure(self, source_id: str, error: Exception):
        """Update health metrics after failure"""
        if source_id not in self.source_health:
            self.source_health[source_id] = SourceHealth(
                source_id=source_id,
                success_rate_24h=0.0,
                avg_latency_ms=0,
                last_success=None,
                last_failure=datetime.now(),
                consecutive_failures=1,
                circuit_breaker_open=False
            )
        else:
            health = self.source_health[source_id]
            health.last_failure = datetime.now()
            health.consecutive_failures += 1
            
            # Open circuit breaker after 3 consecutive failures
            if health.consecutive_failures >= 3:
                health.circuit_breaker_open = True
                logger.critical(f"CIRCUIT BREAKER OPENED for {source_id}")
        
        logger.debug(f"Health updated for {source_id}: Failure ({error})")
    
    def _is_circuit_open(self, source_id: str) -> bool:
        """Check if circuit breaker is open for source"""
        if source_id not in self.source_health:
            return False
        
        health = self.source_health[source_id]
        if not health.circuit_breaker_open:
            return False
        
        # Auto-reset after 5 minutes
        if health.last_failure:
            time_since_failure = datetime.now() - health.last_failure
            if time_since_failure > timedelta(minutes=5):
                logger.info(f"Circuit naturally reset for {source_id}")
                health.circuit_breaker_open = False
                health.consecutive_failures = 0
                return False
        
        return True

    async def _attempt_healing(
        self, 
        source_id: str, 
        failed_selector: str, 
        target_description: str,
        html_content: str,
        screenshot_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Invoke the Healer Agent to fix the broken selector
        """
        if not (failed_selector and html_content):
            logger.warning(f"Cannot heal {source_id}: missing selector or HTML context")
            raise AllSourcesFailedError(f"Healing impossible for {source_id}")

        logger.info(f"🚑 STARTING HEALER PROTOCOL for {source_id}")
        
        result = await self.healer.heal_selector(
            failed_selector,
            target_description or f"Data for {source_id}",
            html_content,
            screenshot_path
        )
        
        if result and result.new_selector:
            logger.info(f"✅ HEALER SUCCESS: Replaced '{failed_selector}' with '{result.new_selector}'")
            
            # Persist the fix
            self.adaptive_config.update_selector(source_id, result.new_selector)
            
            return {
                "status": "healed",
                "source": source_id,
                "new_selector": result.new_selector,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
        else:
            logger.error(f"❌ HEALER FAILED for {source_id}")
            raise AllSourcesFailedError(f"Healer could not fix {source_id}")

class CircuitBreakerOpenError(Exception): pass
class AllSourcesFailedError(Exception): pass
class NoDegradedDataAvailableError(Exception): pass
