package iotfrisbee.domain

case class DiskGolfDisk(
  id: DiskGolfDiskId,
  name: String,
  trackId: DiskGolfTrackId,
  hardwareId: Option[HardwareId],
)
