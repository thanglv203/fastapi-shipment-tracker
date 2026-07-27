from typing import Sequence

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select, any_
from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from app.database.models import DeliveryPartner, Shipment
from app.services.user import UserService


class DeliveryPartnerService(UserService):
    def __init__(self, session: AsyncSession, tasks: BackgroundTasks):
        super().__init__(DeliveryPartner, session, tasks)
        
    async def add(self, delivery_partner: DeliveryPartnerCreate):
        return await self._add_user(
            delivery_partner.model_dump(),
            "partner"
        )
        
    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        return (
            await self.session.scalars(
                select(DeliveryPartner).where(
                    zipcode == any_(DeliveryPartner.serviceable_zip_codes)
                )
            )
        ).all()
    
    async def assign_shipment(self, shipment: Shipment):
        eligible_partner = await self.get_partners_by_zipcode(shipment.destination)
        
        for partner in eligible_partner:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner
            
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner available", 
        )
                  
    async def update(self, partner: DeliveryPartner):
        return await self._update(partner)
    
    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)