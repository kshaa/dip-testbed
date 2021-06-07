package iotfrisbee.protocol

case class ServiceStatus(
  userCount: Integer,
  diskGolfTrackCount: Integer,
  hardwareCount: Integer,
  hardwareMessageCount: Integer,
  diskGolfDiskCount: Integer,
  diskGolfBasketCount: Integer,
)
object ServiceStatus {
  def empty: ServiceStatus = ServiceStatus(0, 0, 0, 0, 0, 0)
}
