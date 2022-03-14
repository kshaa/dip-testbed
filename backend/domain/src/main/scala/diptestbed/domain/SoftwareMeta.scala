package diptestbed.domain

case class SoftwareMeta(
  id: SoftwareId,
  ownerId: UserId,
  name: String,
  isPublic: Boolean
)
