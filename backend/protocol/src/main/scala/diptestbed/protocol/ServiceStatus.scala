package diptestbed.protocol

case class ServiceStatus(
  userCount: Integer,
  hardwareCount: Integer,
  softwareCount: Integer,
)
object ServiceStatus {
  def empty: ServiceStatus = ServiceStatus(0, 0, 0)
}
