package diptestbed.domain

case class User(
  id: UserId,
  username: String,
  isManager: Boolean, // Managers can assign permissions
  isLabOwner: Boolean, // Lab owners can create and manage hardware
  isDeveloper: Boolean // Developers can upload their own software
) {
  def canAccessHardware: Boolean = isLabOwner || isDeveloper
  def canAccessSoftware: Boolean = isLabOwner || isDeveloper
}
