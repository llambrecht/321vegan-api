from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import sqlite3
import tempfile
import os

from app.database.db import get_db
from app.models.product import Product, ProductState, ProductStatus
from app.models.brand import Brand
from app.models.cosmetic import Cosmetic
from app.routes.dependencies import get_current_user
from app.models.user import User
from app.log import get_logger

router = APIRouter()
log = get_logger(__name__)


def map_status_to_export_format(status: ProductStatus) -> str:
    """Map internal ProductStatus to export format."""
    mapping = {
        ProductStatus.VEGAN: "V",
        ProductStatus.NON_VEGAN: "R", 
        ProductStatus.MAYBE_VEGAN: "M",
        ProductStatus.NOT_FOUND: "N"
    }
    return mapping.get(status, "N")


def extract_brand_name(product: Product) -> Optional[str]:
    """Extract brand name from product - either from brand relationship or description."""
    if product.brand:
        return product.brand.name
    elif product.description:
        return product.description.strip()
    return None


def create_sqlite_database(db_path: str) -> sqlite3.Connection:
    """Create SQLite database with the required table structure."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the products table with the required schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            code TEXT PRIMARY KEY,
            name TEXT,
            brand TEXT,
            status TEXT,
            biodynamie TEXT,
            problem TEXT
        )
    ''')
    
    conn.commit()
    return conn


def create_cosmetics_sqlite_database(db_path: str) -> sqlite3.Connection:
    """Create SQLite database with the required table structure for cosmetics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the cosmetics table with the required schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cosmetics (
            brand TEXT PRIMARY KEY,
            vegan TEXT,
            cf TEXT
        )
    ''')
    
    conn.commit()
    return conn


@router.get("/products/sqlite", summary="Export products to SQLite")
async def export_products_to_sqlite(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export published products to SQLite format.
    
    Returns a downloadable SQLite file containing products with columns:
    - code: barcode (ean)
    - name: product name (trimmed)
    - brand: brand name from brand_id or description if no brand_id
    - status: V (vegan), R (not vegan), M (maybe vegan), N (not found)
    - biodynamie: Y or null
    - problem: problem_description for non-vegan products
    """
    
    try:
        log.info(f"User {current_user.email} requested SQLite export")
        
        # Create temporary SQLite file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='vegan_products_')
        os.close(temp_fd)
        
        # Create SQLite database
        sqlite_conn = create_sqlite_database(temp_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Clear existing data
        sqlite_cursor.execute("DELETE FROM products")
        
        # Query published products with their brands
        published_products = db.query(Product).filter(
            Product.state.in_([
                ProductState.PUBLISHED,
                ProductState.NEED_CONTACT,
                ProductState.WAITING_REPLY
            ])
        ).all()
        
        log.info(f"Found {len(published_products)} products for export (PUBLISHED, NEED_CONTACT, WAITING_REPLY)")
        
        exported_count = 0
        skipped_count = 0
        
        for product in published_products:
            # Skip products without EAN code
            if not product.ean or not product.ean.strip():
                log.warning(f"Skipping product {product.id}: missing EAN code")
                skipped_count += 1
                continue
            
            # Prepare data for export
            code = product.ean.strip()
            name = product.name.strip() if product.name else None
            brand = extract_brand_name(product)
            status = map_status_to_export_format(product.status)
            biodynamie = "Y" if product.biodynamic else None
            problem = product.problem_description if product.status == ProductStatus.NON_VEGAN else None
            
            # Insert into SQLite
            try:
                sqlite_cursor.execute('''
                    INSERT OR REPLACE INTO products 
                    (code, name, brand, status, biodynamie, problem) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (code, name, brand, status, biodynamie, problem))
                
                exported_count += 1
                    
            except Exception as e:
                log.error(f"Error inserting product {code}: {e}")
                skipped_count += 1
        
        # Commit changes
        sqlite_conn.commit()
        sqlite_conn.close()
        
        log.info(f"Export completed: {exported_count} exported, {skipped_count} skipped")
        
        # Return the file as download
        return FileResponse(
            path=temp_path,
            filename="vegan_products.db",
            media_type="application/octet-stream",
            background=lambda: os.unlink(temp_path)  # Clean up temp file after response
        )
        
    except Exception as e:
        log.error(f"Error during SQLite export: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export to SQLite: {str(e)}"
        )


@router.get("/products/sqlite/stats", summary="Get products SQLite export statistics")
async def get_export_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about products that would be exported to SQLite.
    """
    
    try:
        # Query published products
        published_products = db.query(Product).filter(
            Product.state.in_([
                ProductState.PUBLISHED,
                ProductState.NEED_CONTACT,
                ProductState.WAITING_REPLY
            ])
        ).all()
        
        # Calculate statistics
        total_products = len(published_products)
        products_with_ean = len([p for p in published_products if p.ean and p.ean.strip()])
        
        status_counts = {}
        biodynamic_count = 0
        problems_count = 0
        
        for product in published_products:
            if not product.ean or not product.ean.strip():
                continue
                
            # Count by status
            status_key = map_status_to_export_format(product.status)
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
            
            # Count biodynamic
            if product.biodynamic:
                biodynamic_count += 1
                
            # Count problems
            if product.status == ProductStatus.NON_VEGAN and product.problem_description:
                problems_count += 1
        
        return {
            "total_products": total_products,
            "exportable_products": products_with_ean,
            "skipped_products": total_products - products_with_ean,
            "included_states": ["PUBLISHED", "NEED_CONTACT", "WAITING_REPLY"],
            "status_distribution": {
                "vegan": status_counts.get("V", 0),
                "not_vegan": status_counts.get("R", 0),
                "maybe_vegan": status_counts.get("M", 0),
                "not_found": status_counts.get("N", 0)
            },
            "biodynamic_products": biodynamic_count,
            "products_with_problems": problems_count
        }
        
    except Exception as e:
        log.error(f"Error getting export statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export statistics: {str(e)}"
        )


@router.get("/cosmetics/sqlite", summary="Export cosmetics to SQLite")
async def export_cosmetics_to_sqlite(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all cosmetics to SQLite format.
    
    Returns a downloadable SQLite file containing cosmetics with columns:
    - brand: brand name
    - vegan: Y (vegan) or N (not vegan)  
    - cf: Y (cruelty free) or N (not cruelty free)
    """
    
    try:
        log.info(f"User {current_user.email} requested cosmetics SQLite export")
        
        # Temp SQL file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='cosmetics_')
        os.close(temp_fd)
        
        # Create SQLite database
        sqlite_conn = create_cosmetics_sqlite_database(temp_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Clear existing data
        sqlite_cursor.execute("DELETE FROM cosmetics")
        
        # Query all cosmetics
        all_cosmetics = db.query(Cosmetic).all()
        
        log.info(f"Found {len(all_cosmetics)} cosmetics for export")
        
        exported_count = 0
        skipped_count = 0
        
        for cosmetic in all_cosmetics:
            # Skip cosmetics without brand name (should not happen)
            if not cosmetic.brand_name or not cosmetic.brand_name.strip():
                log.warning(f"Skipping cosmetic {cosmetic.id}: missing brand name")
                skipped_count += 1
                continue
            
            # Prepare data for export
            brand = cosmetic.brand_name.strip()
            vegan = "Y" if cosmetic.is_vegan else "N"
            cf = "Y" if cosmetic.is_cruelty_free else "N"
            
            # Insert into SQLite
            try:
                sqlite_cursor.execute('''
                    INSERT OR REPLACE INTO cosmetics 
                    (brand, vegan, cf) 
                    VALUES (?, ?, ?)
                ''', (brand, vegan, cf))
                
                exported_count += 1
                    
            except Exception as e:
                log.error(f"Error inserting cosmetic {brand}: {e}")
                skipped_count += 1
        
        # Commit changes
        sqlite_conn.commit()
        sqlite_conn.close()
        
        log.info(f"Cosmetics export completed: {exported_count} exported, {skipped_count} skipped")
        
        # Return the file as download
        return FileResponse(
            path=temp_path,
            filename="vegan_cosmetics.db",
            media_type="application/octet-stream",
            background=lambda: os.unlink(temp_path)  # Clean up temp file after response
        )
        
    except Exception as e:
        log.error(f"Error during cosmetics SQLite export: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export cosmetics to SQLite: {str(e)}"
        )


@router.get("/cosmetics/sqlite/stats", summary="Get cosmetics SQLite export statistics")
async def get_cosmetics_export_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about cosmetics that would be exported to SQLite.
    """
    
    try:
        # Query all cosmetics
        all_cosmetics = db.query(Cosmetic).all()
        
        # Calculate statistics
        total_cosmetics = len(all_cosmetics)
        cosmetics_with_brand = len([c for c in all_cosmetics if c.brand_name and c.brand_name.strip()])
        
        vegan_count = 0
        cruelty_free_count = 0
        both_vegan_and_cf = 0
        
        for cosmetic in all_cosmetics:
            if not cosmetic.brand_name or not cosmetic.brand_name.strip():
                continue
                
            if cosmetic.is_vegan:
                vegan_count += 1
            if cosmetic.is_cruelty_free:
                cruelty_free_count += 1
            if cosmetic.is_vegan and cosmetic.is_cruelty_free:
                both_vegan_and_cf += 1
                vegan_count -= 1
                cruelty_free_count -= 1

        return {
            "total_cosmetics": total_cosmetics,
            "exportable_cosmetics": cosmetics_with_brand,
            "skipped_cosmetics": total_cosmetics - cosmetics_with_brand,
            "vegan_cosmetics": vegan_count,
            "cruelty_free_cosmetics": cruelty_free_count,
            "both_vegan_and_cruelty_free": both_vegan_and_cf,
            "statistics": {
                "vegan_percentage": round((vegan_count / cosmetics_with_brand * 100), 2) if cosmetics_with_brand > 0 else 0,
                "cruelty_free_percentage": round((cruelty_free_count / cosmetics_with_brand * 100), 2) if cosmetics_with_brand > 0 else 0
            }
        }
        
    except Exception as e:
        log.error(f"Error getting cosmetics export statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cosmetics export statistics: {str(e)}"
        )
