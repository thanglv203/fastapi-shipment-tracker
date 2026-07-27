
from app.database.models import Shipment, ShipmentEvent, ShipmentStatus
from app.services.base import BaseService


class ShipmentEventService(BaseService):
    def __init__(self, session):
        super().__init__(ShipmentEvent, session)
    
    async def add(
        self, 
        shipment: Shipment,
        location: str,
        status: ShipmentStatus = None,
        description: str = None,
    ) -> ShipmentEvent:
        if not location or not status:
            last_event = await self.get_lastest_event(shipment)
            
            location = location if location else last_event.location
            status = status if status else last_event.status

        new_event = ShipmentEvent(
            location=location,
            status=status,
            description=description 
            if description else self._generate_description(
                status,
                location,
            ),
            shipment_id=shipment.id,
        )
        return await self._add(new_event)
    
    async def get_lastest_event(self, shipment: Shipment):
        timeline = shipment.timeline
        
        timeline.sort(key=lambda event: event.created_at)
        return timeline[-1]
    
    def _generate_description(self, status: ShipmentStatus, location: int):
        match status:
            case ShipmentStatus.placed:
                return "assigned delivery partner"
            case ShipmentStatus.out_for_delivery:
                return "shipment out for delivery"
            case ShipmentStatus.delivered:
                return "successfully deliveried"
            case _: # and ShipmentStatus.in_transit
                return f"scanned at {location}"