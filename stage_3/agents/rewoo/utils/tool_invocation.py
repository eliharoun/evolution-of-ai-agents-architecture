"""
Utility for dynamic tool invocation with parameter mapping.
Provides reusable functions for parsing and invoking tools with multiple parameters.
"""
import inspect
from typing import Any, Dict, Callable


def parse_tool_parameters(tool_input: str) -> list[str]:
    """
    Parse comma-separated tool parameters.
    
    Args:
        tool_input: Comma-separated parameter string
        
    Returns:
        List of parameter values
        
    Example:
        >>> parse_tool_parameters("12345, expedite, 123 Main St")
        ["12345", "expedite", "123 Main St"]
    """
    return [p.strip() for p in tool_input.split(',')]


def invoke_tool_with_params(tool: Callable, tool_input: str) -> Any:
    """
    Invoke a tool with automatic parameter mapping using introspection.
    
    This function:
    1. Parses comma-separated parameters from tool_input
    2. Inspects the tool's signature to get parameter names
    3. Maps positional parameters to their corresponding names
    4. Handles optional parameters with defaults
    5. Invokes the tool with the correct format for LangChain tools
    
    Args:
        tool: The tool function to invoke (LangChain tool)
        tool_input: Comma-separated string of parameter values
        
    Returns:
        Result from tool invocation
        
    Example:
        >>> tool = some_tool_function
        >>> result = invoke_tool_with_params(tool, "value1, value2, value3")
    """
    # Parse comma-separated parameters
    params = parse_tool_parameters(tool_input)
    
    # Get tool signature using introspection
    sig = inspect.signature(tool.func if hasattr(tool, 'func') else tool)
    param_names = list(sig.parameters.keys())
    
    # Build kwargs by mapping params to parameter names
    kwargs = {}
    for i, (param_name, value) in enumerate(zip(param_names, params)):
        # Skip if we've run out of provided values
        if i >= len(params):
            break
            
        param_obj = sig.parameters[param_name]
        
        # Handle type conversion for common types
        if param_obj.annotation != inspect.Parameter.empty:
            try:
                if param_obj.annotation == int:
                    kwargs[param_name] = int(value)
                elif param_obj.annotation == float:
                    kwargs[param_name] = float(value)
                elif param_obj.annotation == bool:
                    kwargs[param_name] = value.lower() in ('true', '1', 'yes', 'y')
                else:
                    kwargs[param_name] = value
            except (ValueError, AttributeError):
                # If conversion fails, use as string
                kwargs[param_name] = value
        else:
            kwargs[param_name] = value
    
    # LangChain tools expect invoke(input) where input is:
    # - A single value for single-parameter tools
    # - A dict for multi-parameter tools
    if len(kwargs) == 1:
        # Single parameter - pass the value directly
        return tool.invoke(list(kwargs.values())[0])
    else:
        # Multiple parameters - pass as dict
        return tool.invoke(kwargs)


def get_tool_signature_info(tool: Callable) -> Dict[str, Any]:
    """
    Get information about a tool's parameters for documentation.
    
    Args:
        tool: The tool function to inspect
        
    Returns:
        Dictionary with parameter names, types, and defaults
        
    Example:
        >>> info = get_tool_signature_info(some_tool)
        >>> print(info)
        {'param1': {'type': 'str', 'default': None, 'required': True}, ...}
    """
    sig = inspect.signature(tool.func if hasattr(tool, 'func') else tool)
    
    param_info = {}
    for param_name, param in sig.parameters.items():
        param_info[param_name] = {
            'type': param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any',
            'default': param.default if param.default != inspect.Parameter.empty else None,
            'required': param.default == inspect.Parameter.empty
        }
    
    return param_info
