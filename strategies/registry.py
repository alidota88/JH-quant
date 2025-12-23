# strategies/registry.py
STRATEGY_REGISTRY = {}

def register_strategy(name: str, default_params: dict = None):
    def decorator(func):
        STRATEGY_REGISTRY[name] = {
            'func': func,
            'default_params': default_params or {}
        }
        return func
    return decorator

def get_registered_strategies():
    return list(STRATEGY_REGISTRY.keys())
