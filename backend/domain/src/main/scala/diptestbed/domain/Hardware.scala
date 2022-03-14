package diptestbed.domain

case class Hardware(
  id: HardwareId,
  name: String,
  ownerId: UserId,
  isPublic: Boolean
)
