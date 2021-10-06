package iotfrisbee.protocol

case class ServiceStatus(
  userCount: Integer,
  hardwareCount: Integer,
  hardwareMessageCount: Integer,
)
object ServiceStatus {
  def empty: ServiceStatus = ServiceStatus(0, 0, 0)
}
