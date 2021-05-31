package iotfrisbee.domain

case class DiskGolfDisk(
  id: DiskGolfDiskId,
  trackId: DiskGolfTrackId,
  hardwareId: Option[HardwareId],
)
