package iotfrisbee.domain

case class DiskGolfTrack(
  id: DiskGolfTrackId,
  ownerId: UserId,
  name: String,
  timezoneId: DomainTimeZoneId,
)
