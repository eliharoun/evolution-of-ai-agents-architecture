"""
Inventory check tool for verifying product availability and stock levels.
Enables agents to check product variants, colors, sizes, and stock quantities.
"""

from typing import Optional
from langchain_core.tools import tool

from common.logging_config import get_logger
from common.data.inventory import check_availability, get_product_inventory, PRODUCT_INVENTORY

logger = get_logger(__name__)


@tool
def check_inventory(product_name: str, color: str = None, size: str = None) -> str:
    """
    Check product inventory and availability.
    
    Use this tool when customers ask about product availability, stock levels,
    different colors/sizes, or want to know what options are available.
    
    Args:
        product_name: Name or partial name of the product to check
        color: Optional color filter (e.g., "blue", "black", "red")
        size: Optional size filter (e.g., "M", "L", "10", "32x32")
        
    Returns:
        A formatted string with product availability information
        
    Example:
        >>> check_inventory("t-shirt", "blue", "M")
        "Product: Classic Cotton T-Shirt\\nBlue, Size M: 3 in stock..."
    """
    logger.info(f"Inventory check tool called - product: {product_name}, color: {color}, size: {size}")
    
    try:
        # Find matching products by name
        matching_products = []
        
        for item_id, product in PRODUCT_INVENTORY.items():
            if product_name.lower() in product["title"].lower():
                matching_products.append((item_id, product))
        
        if not matching_products:
            return f"No products found matching '{product_name}'. Please try a different product name."
        
        # Check availability for each matching product
        results = []
        
        for item_id, product in matching_products:
            availability = check_availability(item_id, color, size)
            
            if availability["available"]:
                result = f"✅ {availability['title']}\n"
                result += f"Available Options ({availability['total_variants']} variants):\n"
                
                for variant in availability["variants"]:
                    stock_status = "✅ In Stock" if variant["stock"] > 5 else f"⚠️ Low Stock ({variant['stock']} left)"
                    result += f"- {variant['color'].title()}, Size {variant['size']}: ${variant['price']:.2f} - {stock_status}\n"
                    
                results.append(result)
            else:
                # Show out of stock message but still show the product exists
                result = f"❌ {product['title']}\n"
                if color or size:
                    result += f"Not available in requested color/size ({color or 'any'}/{size or 'any'})\n"
                else:
                    result += "Currently out of stock\n"
                results.append(result)
        
        if not results:
            return f"'{product_name}' exists but no variants match your criteria (color: {color or 'any'}, size: {size or 'any'})."
        
        # Combine all results
        final_result = "Product Availability Check:\n\n" + "\n".join(results)
        
        # Add helpful suggestions
        if not any("✅" in r for r in results):
            final_result += "\n💡 Suggestions:\n"
            final_result += "- Try different colors or sizes\n"
            final_result += "- Check similar products in the same category\n"
            final_result += "- Sign up for restock notifications"
        
        logger.info(
            f"Inventory check completed - product: {product_name}, matches: {len(matching_products)}, available: {len([r for r in results if '✅' in r])}"
        )
        
        return final_result
        
    except Exception as e:
        logger.error(f"Inventory check error for {product_name}: {str(e)}")
        return f"An error occurred while checking inventory for '{product_name}'. Please try again later."


@tool  
def find_similar_products(item_id: str, criteria: str = "category") -> str:
    """
    Find products similar to a given item.
    
    Use this tool when customers want alternatives or similar items,
    especially when their preferred item is out of stock.
    
    Args:
        item_id: The original item ID to find alternatives for
        criteria: Similarity criteria ("category", "price_range", "color")
        
    Returns:
        A formatted string with similar product suggestions
        
    Example:
        >>> find_similar_products("ITEM001", "category")
        "Similar Products (Tops category):\\n- ITEM007: Cashmere Sweater..."
    """
    logger.info(f"Similar products tool called - item: {item_id}, criteria: {criteria}")
    
    try:
        original_product = PRODUCT_INVENTORY.get(item_id)
        if not original_product:
            return f"Original product {item_id} not found. Cannot find similar products."
        
        similar_items = []
        
        for other_id, other_product in PRODUCT_INVENTORY.items():
            if other_id == item_id:
                continue  # Skip the original item
            
            if criteria == "category":
                if other_product["category"] == original_product["category"]:
                    similar_items.append((other_id, other_product))
            elif criteria == "price_range":
                price_diff = abs(other_product["base_price"] - original_product["base_price"])
                if price_diff <= 20:  # Within $20 price range
                    similar_items.append((other_id, other_product))
            elif criteria == "color":
                # Find products with similar color options
                orig_colors = set()
                for variant in original_product["variants"].values():
                    orig_colors.add(variant["color"].lower())
                
                other_colors = set()
                for variant in other_product["variants"].values():
                    other_colors.add(variant["color"].lower())
                
                if orig_colors & other_colors:  # Common colors
                    similar_items.append((other_id, other_product))
        
        if not similar_items:
            return f"No similar products found for {original_product['title']} using criteria '{criteria}'."
        
        # Format results
        result = f"Similar Products to {original_product['title']} ({criteria}):\n\n"
        
        for item_id, product in similar_items[:5]:  # Limit to 5 suggestions
            availability = check_availability(item_id)
            stock_status = "✅ Available" if availability["available"] else "❌ Out of stock"
            
            result += f"- {product['title']} (${product['base_price']:.2f}) - {stock_status}\n"
            result += f"  {product['description']}\n"
        
        logger.info(f"Similar products found - original: {item_id}, matches: {len(similar_items)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Similar products error for {item_id}: {str(e)}")
        return f"An error occurred while finding similar products. Please try again later."
