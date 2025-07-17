"""
Database triggers for automatic price history tracking.
Implements task 2.2 requirement for automatic price history tracking.
"""

from sqlalchemy import text
from app.db.database import engine
import logging

logger = logging.getLogger(__name__)


def create_price_history_trigger():
    """
    Create trigger for automatic price history tracking when current_prices table is updated.
    """
    trigger_sql = """
    -- Function to handle price history tracking
    CREATE OR REPLACE FUNCTION track_price_history()
    RETURNS TRIGGER AS $$
    DECLARE
        price_change_type VARCHAR(20);
        price_change_amount NUMERIC(10,2);
        price_change_percentage NUMERIC(5,2);
    BEGIN
        -- Only track if price actually changed
        IF OLD.price IS DISTINCT FROM NEW.price THEN
            -- Calculate price change metrics
            IF NEW.price > OLD.price THEN
                price_change_type := 'increase';
            ELSIF NEW.price < OLD.price THEN
                price_change_type := 'decrease';
            ELSE
                price_change_type := 'no_change';
            END IF;
            
            price_change_amount := NEW.price - OLD.price;
            
            -- Calculate percentage change (avoid division by zero)
            IF OLD.price > 0 THEN
                price_change_percentage := ((NEW.price - OLD.price) / OLD.price) * 100;
            ELSE
                price_change_percentage := 0;
            END IF;
            
            -- Insert into price history
            INSERT INTO price_history (
                product_id,
                platform_id,
                price,
                original_price,
                discount_percentage,
                currency,
                price_change_type,
                price_change_amount,
                price_change_percentage,
                stock_status,
                recorded_at,
                source
            ) VALUES (
                NEW.product_id,
                NEW.platform_id,
                NEW.price,
                NEW.original_price,
                NEW.discount_percentage,
                NEW.currency,
                price_change_type,
                price_change_amount,
                price_change_percentage,
                NEW.stock_status,
                NEW.last_updated,
                'trigger'
            );
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Create the trigger
    DROP TRIGGER IF EXISTS price_history_trigger ON current_prices;
    CREATE TRIGGER price_history_trigger
        AFTER UPDATE ON current_prices
        FOR EACH ROW
        EXECUTE FUNCTION track_price_history();
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            logger.info("✅ Created price history tracking trigger successfully")
    except Exception as e:
        logger.error(f"❌ Error creating price history trigger: {str(e)}")
        raise


def create_discount_validation_trigger():
    """
    Create trigger to validate discount data and calculate discount percentage.
    """
    trigger_sql = """
    -- Function to validate and calculate discount data
    CREATE OR REPLACE FUNCTION validate_discount_data()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Calculate discount percentage if not provided
        IF NEW.discount_type = 'percentage' AND NEW.discount_percentage IS NULL THEN
            NEW.discount_percentage := NEW.discount_value;
        ELSIF NEW.discount_type = 'fixed_amount' AND NEW.discount_percentage IS NULL THEN
            -- For fixed amount discounts, we can't calculate percentage without knowing the original price
            -- This would need to be calculated at application level
            NEW.discount_percentage := NULL;
        END IF;
        
        -- Validate discount dates
        IF NEW.start_date >= NEW.end_date THEN
            RAISE EXCEPTION 'Discount start date must be before end date';
        END IF;
        
        -- Validate discount values
        IF NEW.discount_type = 'percentage' AND (NEW.discount_value < 0 OR NEW.discount_value > 100) THEN
            RAISE EXCEPTION 'Percentage discount must be between 0 and 100';
        END IF;
        
        IF NEW.discount_type = 'fixed_amount' AND NEW.discount_value < 0 THEN
            RAISE EXCEPTION 'Fixed amount discount cannot be negative';
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Create the trigger
    DROP TRIGGER IF EXISTS discount_validation_trigger ON discounts;
    CREATE TRIGGER discount_validation_trigger
        BEFORE INSERT OR UPDATE ON discounts
        FOR EACH ROW
        EXECUTE FUNCTION validate_discount_data();
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            logger.info("✅ Created discount validation trigger successfully")
    except Exception as e:
        logger.error(f"❌ Error creating discount validation trigger: {str(e)}")
        raise


def create_campaign_usage_trigger():
    """
    Create trigger to update campaign usage counts.
    """
    trigger_sql = """
    -- Function to update campaign usage counts
    CREATE OR REPLACE FUNCTION update_campaign_usage()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Update promotional campaign usage count
        UPDATE promotional_campaigns 
        SET current_usage_count = current_usage_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.campaign_id;
        
        -- Update campaign product stock sold
        UPDATE campaign_products 
        SET stock_sold = stock_sold + 1
        WHERE campaign_id = NEW.campaign_id AND product_id = NEW.product_id;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Note: This trigger would be applied to an orders or transactions table
    -- For now, we'll create the function but not the trigger since we don't have those tables yet
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            logger.info("✅ Created campaign usage tracking function successfully")
    except Exception as e:
        logger.error(f"❌ Error creating campaign usage function: {str(e)}")
        raise


def create_price_update_notification_trigger():
    """
    Create trigger to log significant price changes for monitoring.
    """
    trigger_sql = """
    -- Function to log significant price changes
    CREATE OR REPLACE FUNCTION log_significant_price_changes()
    RETURNS TRIGGER AS $$
    DECLARE
        price_change_percentage NUMERIC(5,2);
        threshold_percentage NUMERIC(5,2) := 10.0; -- 10% threshold
    BEGIN
        -- Only process if price changed
        IF OLD.price IS DISTINCT FROM NEW.price AND OLD.price > 0 THEN
            price_change_percentage := ABS(((NEW.price - OLD.price) / OLD.price) * 100);
            
            -- Log if price change is significant (>10%)
            IF price_change_percentage > threshold_percentage THEN
                -- Insert into a monitoring/alerts table (would be created in task 2.3)
                -- For now, we'll use RAISE NOTICE for logging
                RAISE NOTICE 'Significant price change detected: Product ID %, Platform ID %, Old Price: %, New Price: %, Change: %%%', 
                    NEW.product_id, NEW.platform_id, OLD.price, NEW.price, price_change_percentage;
            END IF;
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Create the trigger
    DROP TRIGGER IF EXISTS price_change_notification_trigger ON current_prices;
    CREATE TRIGGER price_change_notification_trigger
        AFTER UPDATE ON current_prices
        FOR EACH ROW
        EXECUTE FUNCTION log_significant_price_changes();
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            logger.info("✅ Created price change notification trigger successfully")
    except Exception as e:
        logger.error(f"❌ Error creating price change notification trigger: {str(e)}")
        raise


def create_all_pricing_triggers():
    """
    Create all pricing-related triggers.
    """
    logger.info("Creating pricing and discount triggers...")
    
    create_price_history_trigger()
    create_discount_validation_trigger()
    create_campaign_usage_trigger()
    create_price_update_notification_trigger()
    
    logger.info("✅ All pricing triggers created successfully")


def drop_all_pricing_triggers():
    """
    Drop all pricing-related triggers.
    """
    drop_sql = """
    DROP TRIGGER IF EXISTS price_history_trigger ON current_prices;
    DROP TRIGGER IF EXISTS discount_validation_trigger ON discounts;
    DROP TRIGGER IF EXISTS price_change_notification_trigger ON current_prices;
    
    DROP FUNCTION IF EXISTS track_price_history();
    DROP FUNCTION IF EXISTS validate_discount_data();
    DROP FUNCTION IF EXISTS update_campaign_usage();
    DROP FUNCTION IF EXISTS log_significant_price_changes();
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(drop_sql))
            conn.commit()
            logger.info("✅ All pricing triggers dropped successfully")
    except Exception as e:
        logger.error(f"❌ Error dropping pricing triggers: {str(e)}")
        raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create all triggers
    create_all_pricing_triggers()
    
    print("Pricing triggers setup completed successfully!")