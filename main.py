import functions_framework
import logging
from flask import jsonify, make_response
from utils.order_utils import validate_payload, enrich_payload, simulate_db_save

#functions-framework --target=ecommcloudrun --source=cloudrunfunctionEcom.py --port=8080

logger = logging.getLogger("Ecomm")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

@functions_framework.http

def ecommcloudrun(request):
    try:
        data = request.get_json(silent=True)

        if request.method != "POST":
            logger.warning("Only POST allowed")
            return make_response(jsonify({"error": "Use POST"}), 405)
    
        if not data:
            logger.error("No JSON payload received")
            return make_response(jsonify({"error": "Invalid or missing JSON"}), 400)
        
            
            # 1) Validate
        try:
            validate_payload(data)
        except ValueError as e:
            logger.error("Validation failed: %s", e)
            return make_response(jsonify({"error": str(e)}), 400)

        # 2) Enrich
        enriched = enrich_payload(data)

        # 3) “Save” (fake)
        try:
            if not simulate_db_save(enriched):
                raise RuntimeError("DB save returned False")
        except Exception:
            logger.exception("Error saving to DB")
            return make_response(jsonify({"error": "Internal error"}), 500)

        # 4) Build response
        resp = {
            "status":           "processed",
            "order_id":         enriched["order_id"],
            "processing_id":    enriched["processing_id"],
            "processed_at":     enriched["processed_at"],
            "items_count":      len(enriched["items"]),
            "total_amount":     enriched["total_amount"],
            "payment_method":   enriched["payment_method"],
            "shipping_address": enriched["shipping_address"],
            "message":          "Order received and stored."
        }
        logger.info("Order %s processed successfully", enriched["order_id"])
        return make_response(jsonify(resp), 200)
    
    except Exception as e:
        logging.exception("Internal server Error")
        return make_response(jsonify({"error":"Internal Server Error"}),500)
