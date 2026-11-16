"""Local execution policy; future provider/account boundaries are deliberately inactive."""


def compute_policy(timeout_s, memory_mb):
    common = {'execution': 'local_cpu', 'price': 0, 'concurrent_jobs': 1,
              'timeout_s': timeout_s, 'memory_mb': memory_mb}
    return {
        'schema_version': 1,
        'accounts_enabled': False,
        'payments_enabled': False,
        'tiers': [
            {'id': 'local_educational', **common,
             'kinds': ['physics', 'photonics', 'connected', 'research'],
             'description': 'Small physical models and bounded instrument experiments.'},
            {'id': 'local_advanced', **common,
             'kinds': ['circuit', 'machine', 'experiment', 'optimization', 'qubo'],
             'description': 'Bounded statevector and optimization jobs with per-model size limits.'},
        ],
        'remote': {'enabled': False, 'providers': [],
                   'description': 'Future extension only; no remote execution, credentials or billing is implemented.'},
        'metering': {'scope': 'per executed worker',
                     'fields': ['worker_wall_s', 'peak_rss_bytes'],
                     'purpose': 'Local resource diagnostics, not billing.'},
    }
