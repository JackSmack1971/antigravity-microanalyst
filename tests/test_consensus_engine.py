import unittest
from src.microanalyst.validation.consensus import ConsensusEngine

class TestConsensusEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = ConsensusEngine()
        
    def test_price_consensus_normal(self):
        sources = {
            'binance': 43000.0,
            'coingecko': 43010.0,
            'kraken': 43005.0
        }
        result = self.engine.resolve_price_consensus(sources)
        
        self.assertAlmostEqual(result['consensus_price'], 43005.0, delta=10)
        self.assertGreater(result['confidence'], 0.95)
        self.assertEqual(len(result['outliers']), 0)
        
    def test_price_consensus_outlier(self):
        sources = {
            'binance': 43000.0,
            'coingecko': 43010.0,
            'bad_feed': 45000.0 # ~4.6% deviation
        }
        result = self.engine.resolve_price_consensus(sources)
        
        # Outlier should be excluded
        self.assertEqual(len(result['outliers']), 1)
        self.assertEqual(result['outliers'][0][0], 'bad_feed')
        
        # Consensus should be close to 43000
        self.assertAlmostEqual(result['consensus_price'], 43005.0, delta=10)
        
    def test_metric_validation(self):
        # Synthetic MVRV = 1.2
        # Validation Samples (e.g. Glassnode Free) = 1.25
        
        result = self.engine.resolve_metric_with_uncertainty(
            synthetic_value=1.2,
            synthetic_confidence=0.7,
            validation_sources=[{'source': 'glassnode', 'value': 1.25}]
        )
        
        # Deviation is small (0.05 / 1.25 = 4%), so confidence should boost
        self.assertEqual(result['agreement'], 'strong')
        self.assertGreater(result['confidence'], 0.7)
        
    def test_metric_validation_failure(self):
        # Synthetic says 1.2
        # Truth says 2.0 (Massive error)
        
        result = self.engine.resolve_metric_with_uncertainty(
            synthetic_value=1.2,
            synthetic_confidence=0.7,
            validation_sources=[{'source': 'glassnode', 'value': 2.0}]
        )
        
        self.assertEqual(result['agreement'], 'weak')
        self.assertLess(result['confidence'], 0.7)

if __name__ == '__main__':
    unittest.main()
