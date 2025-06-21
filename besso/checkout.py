import logging
from datetime import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def checkout(client, building_id: str, device_id: str) -> bool:
    try:
        ref = client.collection("CheckInCheckOut").document(building_id)

        update_data = {
            "status": 2,
            "checkOut": datetime.utcnow(),
            "lastDevice": device_id
        }
        ref.update(update_data)
        logger.info(f"Document {building_id} updated with {update_data}")

        # Reset cleaning sub-collections
        ref.collection("cleaning").document("outCheckList").update({"inCheck": False})
        ref.collection("cleaning").document("inCheckList").update({"outCheck": False})
        logger.info("Cleaning sub-collections reset")

        return True
    except Exception as e:
        logger.error(f"Error performing Firestore update: {e}", exc_info=True)
        return False