from importlib import import_module


def try_import(*module_names):
    for module_name in module_names:
        try:
            return import_module(module_name)
        except ImportError:
            continue
