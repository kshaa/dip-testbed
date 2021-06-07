package iotfrisbee.domain

case class DiskGolfBasket(
  id: DiskGolfBasketId,
  trackId: DiskGolfTrackId,
  orderNumber: Int,
  name: String,
  hardwareId: Option[HardwareId],
)
