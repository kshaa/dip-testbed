package iotfrisbee.protocol

case class ServiceStatus(userCount: Integer, diskGolfTrackCount: Integer)
object ServiceStatus {
  def empty: ServiceStatus = ServiceStatus(0, 0)
}
