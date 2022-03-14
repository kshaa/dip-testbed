package diptestbed.domain

case class User(
  id: UserId,
  username: String,
  isManager: Boolean, // Managers can assign permissions
  isLabOwner: Boolean, // Lab owners can create and manage hardware
  isDeveloper: Boolean // Developers can upload their own software
) {
  def canInteractHardware: Boolean = isManager || isLabOwner || isDeveloper
  def canCreateSoftware: Boolean = isManager || isLabOwner || isDeveloper
}
