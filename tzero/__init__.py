"""T-Zero's public Python API and package namespace."""

from importlib import import_module

_EXPORTS = {
    'CodebaseScanner': 'tzero.tzero_v3',
    'TokenReducer': 'tzero.tzero_v3',
    'PolyglotSignatureExtractor': 'tzero.tzero_v3',
    'generate_offline_context': 'tzero.tzero_v3',
    'DependencyAnalyzer': 'tzero.tzero_v3',
    'StaticCodeAnalyzer': 'tzero.tzero_v3',
    'WorkspaceDuplicityFinder': 'tzero.tzero_v3',
    'ContextExportManager': 'tzero.tzero_v3',
    'calculate_token_cost': 'tzero.tzero_v3',
    'count_tokens_precise': 'tzero.tzero_v3',
    'launch_gui': 'tzero.tzero_v3',
    'main': 'tzero.tzero_v3',
    'ChangeImpactAnalyzer': 'tzero.tzero_features',
    'ArchitectureRuleEngine': 'tzero.tzero_features',
    'AgentRulesGenerator': 'tzero.tzero_features',
    'LocalSemanticCodeSearch': 'tzero.tzero_features',
    'TokenROICalculator': 'tzero.tzero_features',
    'GitDiffContextBuilder': 'tzero.tzero_features',
    'superdesign_generate': 'tzero.tzero_superdesign',
    'superdesign_iterate': 'tzero.tzero_superdesign',
    'superdesign_extract_system': 'tzero.tzero_superdesign',
    'superdesign_list': 'tzero.tzero_superdesign',
    'superdesign_gallery': 'tzero.tzero_superdesign',
    'create_mcp_server': 'tzero.tzero_mcp',
}
_OPTIONAL_EXPORTS = {
    'create_mcp_server',
    'superdesign_extract_system',
    'superdesign_gallery',
    'superdesign_generate',
    'superdesign_iterate',
    'superdesign_list',
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        value = getattr(import_module(module_name), name)
    except ImportError:
        if name not in _OPTIONAL_EXPORTS:
            raise
        value = None
    globals()[name] = value
    return value
