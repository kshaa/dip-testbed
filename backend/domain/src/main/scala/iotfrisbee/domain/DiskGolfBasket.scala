package iotfrisbee.domain

case class DiskGolfBasket(
  id: DiskGolfBasketId,
  trackId: DiskGolfTrackId,
  orderNumber: Int,
  hardwareId: Option[HardwareId],
)
