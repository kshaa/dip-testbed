package iotfrisbee.domain

import java.util.TimeZone

case class DiskGolfTrack(
  uuid: DiskGolfTrackUUID,
  ownerId: UserId,
  name: String,
  timezone: TimeZone,
)
