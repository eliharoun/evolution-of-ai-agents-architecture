"""
Product inventory data for the online clothing retailer.
Contains product variants, stock levels, and availability information.
"""

from typing import Dict, List, Optional

PRODUCT_INVENTORY = {
    # T-Shirts
    "ITEM001": {
        "item_id": "ITEM001",
        "title": "Classic Cotton T-Shirt",
        "description": "100% organic cotton t-shirt",
        "category": "Tops",
        "base_price": 29.99,
        "variants": {
            "navy-M": {"color": "navy", "size": "M", "stock": 15, "price": 29.99},
            "navy-L": {"color": "navy", "size": "L", "stock": 8, "price": 29.99},
            "black-M": {"color": "black", "size": "M", "stock": 12, "price": 29.99},
            "black-L": {"color": "black", "size": "L", "stock": 5, "price": 29.99},
            "white-M": {"color": "white", "size": "M", "stock": 20, "price": 29.99},
            "white-L": {"color": "white", "size": "L", "stock": 18, "price": 29.99},
            "blue-M": {"color": "blue", "size": "M", "stock": 3, "price": 29.99},  # Low stock
            "blue-L": {"color": "blue", "size": "L", "stock": 0, "price": 29.99}   # Out of stock
        }
    },
    
    # Jeans
    "ITEM002": {
        "item_id": "ITEM002", 
        "title": "Slim Fit Jeans",
        "description": "Modern slim fit denim jeans",
        "category": "Bottoms",
        "base_price": 79.99,
        "variants": {
            "dark-wash-32x32": {"color": "dark wash", "size": "32x32", "stock": 10, "price": 79.99},
            "dark-wash-34x32": {"color": "dark wash", "size": "34x32", "stock": 7, "price": 79.99},
            "light-wash-32x32": {"color": "light wash", "size": "32x32", "stock": 5, "price": 79.99},
            "black-32x32": {"color": "black", "size": "32x32", "stock": 12, "price": 79.99}
        }
    },
    
    # Dresses
    "ITEM003": {
        "item_id": "ITEM003",
        "title": "Summer Dress", 
        "description": "Light and airy summer dress",
        "category": "Dresses",
        "base_price": 59.99,
        "variants": {
            "floral-S": {"color": "floral", "size": "S", "stock": 8, "price": 59.99},
            "floral-M": {"color": "floral", "size": "M", "stock": 6, "price": 59.99},
            "solid-blue-S": {"color": "solid blue", "size": "S", "stock": 4, "price": 59.99},
            "solid-blue-M": {"color": "solid blue", "size": "M", "stock": 2, "price": 59.99}
        }
    },
    
    # Leather Jacket
    "ITEM004": {
        "item_id": "ITEM004",
        "title": "Leather Jacket",
        "description": "Genuine leather jacket", 
        "category": "Outerwear",
        "base_price": 199.99,
        "variants": {
            "black-L": {"color": "black", "size": "L", "stock": 3, "price": 199.99},
            "black-XL": {"color": "black", "size": "XL", "stock": 2, "price": 199.99},
            "brown-L": {"color": "brown", "size": "L", "stock": 1, "price": 199.99},
            "brown-XL": {"color": "brown", "size": "XL", "stock": 0, "price": 199.99}  # Out of stock
        }
    },
    
    # Wool Scarf
    "ITEM005": {
        "item_id": "ITEM005",
        "title": "Wool Scarf",
        "description": "Soft merino wool scarf",
        "category": "Accessories", 
        "base_price": 39.99,
        "variants": {
            "burgundy": {"color": "burgundy", "size": "one-size", "stock": 15, "price": 39.99},
            "navy": {"color": "navy", "size": "one-size", "stock": 10, "price": 39.99},
            "grey": {"color": "grey", "size": "one-size", "stock": 8, "price": 39.99},
            "black": {"color": "black", "size": "one-size", "stock": 12, "price": 39.99}
        }
    },
    
    # Running Shoes
    "ITEM006": {
        "item_id": "ITEM006",
        "title": "Running Shoes",
        "description": "Performance athletic shoes",
        "category": "Footwear",
        "base_price": 89.99,
        "variants": {
            "white-blue-10": {"color": "white/blue", "size": "10", "stock": 6, "price": 89.99},
            "white-blue-11": {"color": "white/blue", "size": "11", "stock": 4, "price": 89.99},
            "black-red-10": {"color": "black/red", "size": "10", "stock": 8, "price": 89.99},
            "black-red-11": {"color": "black/red", "size": "11", "stock": 3, "price": 89.99}
        }
    },
    
    # Cashmere Sweater
    "ITEM007": {
        "item_id": "ITEM007", 
        "title": "Cashmere Sweater",
        "description": "Pure cashmere sweater",
        "category": "Tops",
        "base_price": 149.99,
        "variants": {
            "grey-M": {"color": "grey", "size": "M", "stock": 4, "price": 149.99},
            "grey-L": {"color": "grey", "size": "L", "stock": 2, "price": 149.99},
            "navy-M": {"color": "navy", "size": "M", "stock": 3, "price": 149.99},
            "burgundy-M": {"color": "burgundy", "size": "M", "stock": 1, "price": 149.99}
        }
    }
}


# Global state for tracking inventory changes (stateful behavior)
_inventory_state = PRODUCT_INVENTORY.copy()


def get_product_inventory(item_id: str) -> Optional[Dict]:
    """
    Get current inventory for a product.
    
    Args:
        item_id: Product item ID
        
    Returns:
        Product inventory data or None if not found
    """
    return _inventory_state.get(item_id)


def check_availability(item_id: str, color: str = None, size: str = None) -> Dict:
    """
    Check product availability with optional color/size filters.
    
    Args:
        item_id: Product item ID
        color: Optional color filter
        size: Optional size filter
        
    Returns:
        Dictionary with availability information
    """
    product = _inventory_state.get(item_id)
    if not product:
        return {"available": False, "reason": "Product not found", "variants": []}
    
    available_variants = []
    
    for variant_key, variant_data in product["variants"].items():
        # Apply filters
        if color and color.lower() not in variant_data["color"].lower():
            continue
        if size and size.lower() not in variant_data["size"].lower():
            continue
        
        if variant_data["stock"] > 0:
            available_variants.append({
                "variant": variant_key,
                "color": variant_data["color"],
                "size": variant_data["size"],
                "stock": variant_data["stock"],
                "price": variant_data["price"]
            })
    
    return {
        "item_id": item_id,
        "title": product["title"],
        "available": len(available_variants) > 0,
        "variants": available_variants,
        "total_variants": len(available_variants)
    }


def update_inventory(item_id: str, variant_key: str, quantity_change: int) -> bool:
    """
    Update inventory levels (for stateful behavior).
    
    Args:
        item_id: Product item ID
        variant_key: Specific variant key
        quantity_change: Change in quantity (positive or negative)
        
    Returns:
        True if update successful, False otherwise
    """
    product = _inventory_state.get(item_id)
    if not product or variant_key not in product["variants"]:
        return False
    
    variant = product["variants"][variant_key]
    new_stock = max(0, variant["stock"] + quantity_change)
    variant["stock"] = new_stock
    
    return True


def reset_inventory():
    """Reset inventory to original state (for testing)."""
    global _inventory_state
    _inventory_state = PRODUCT_INVENTORY.copy()
