package iotfrisbee.protocol.messages.diskGolfTrack

import iotfrisbee.domain.{DomainTimeZoneId, UserId}

case class CreateDiskGolfTrack(ownerId: UserId, name: String, timezoneId: DomainTimeZoneId)
