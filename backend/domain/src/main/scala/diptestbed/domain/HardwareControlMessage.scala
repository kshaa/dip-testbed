package diptestbed.domain

import diptestbed.domain.HardwareSerialMonitorMessageBinary._
sealed trait HardwareControlMessage

// Any of the non-binary control messages
sealed trait HardwareControlMessageNonBinary extends HardwareControlMessage

/**
  * Internal messages are issued only by the hardware control actor itself
  */
sealed trait HardwareControlMessageInternal extends HardwareControlMessageNonBinary
object HardwareControlMessageInternal {
  // Goes to agent
  case class AuthResult(error: Option[String]) extends HardwareControlMessageInternal

  // Goes back into actor
  case class AuthSuccess(user: User) extends HardwareControlMessageInternal
  case class AuthFailure(reason: String) extends HardwareControlMessageInternal

  case class StartLifecycle() extends HardwareControlMessageInternal
  case class EndLifecycle() extends HardwareControlMessageInternal

  case class SerialMonitorRequestStop() extends HardwareControlMessageInternal

  case class SerialMonitorListenersHeartbeatStart() extends HardwareControlMessageInternal
  case class SerialMonitorListenersHeartbeatPing() extends HardwareControlMessageInternal
  case class SerialMonitorListenersHeartbeatFinish() extends HardwareControlMessageInternal
}

/**
  * Anyone can send or receive external messages
  */
sealed trait HardwareControlMessageExternal extends HardwareControlMessage

/**
  * Messages that can easily be stored as JSON i.e. don't contain binary data
  * N.B. This is kind of protocol specific and is leaking into the domain, but it ain't too bad, I think
  */
sealed trait HardwareControlMessageExternalNonBinary
    extends HardwareControlMessageExternal
    with HardwareControlMessageNonBinary
object HardwareControlMessageExternalNonBinary {
  case class AuthRequest(username: String, password: String) extends HardwareControlMessageExternalNonBinary
  case class UploadSoftwareRequest(softwareId: SoftwareId) extends HardwareControlMessageExternalNonBinary
  case class UploadSoftwareResult(error: Option[String]) extends HardwareControlMessageExternalNonBinary
  object UploadSoftwareResult {
    val unavailable = UploadSoftwareResult(Some("Upload request not available, agent is already doing something"))
  }

  case class SerialMonitorRequest(serialConfig: Option[SerialConfig]) extends HardwareControlMessageExternalNonBinary
  case class SerialMonitorResult(error: Option[String]) extends HardwareControlMessageExternalNonBinary
  case class SerialMonitorUnavailable(reason: String) extends HardwareControlMessageExternalNonBinary
  object SerialMonitorResult {
    val unavailable = SerialMonitorResult(Some("Monitor request not available, agent is already doing something"))
  }

  case class SerialMonitorListenersHeartbeatPong() extends HardwareControlMessageExternalNonBinary

  case class Ping() extends HardwareControlMessageExternalNonBinary

  def isNonPingMessage(message: HardwareControlMessage): Option[HardwareControlMessage] =
    message match {
      case Ping()         => None
      case nonPingMessage => Some(nonPingMessage)
    }
}

/**
  * Messages that can't easily be stored as JSON i.e. contain binary data
  */
sealed trait HardwareControlMessageExternalBinary extends HardwareControlMessageExternal
object HardwareControlMessageExternalBinary {
  case class SerialMonitorMessageToAgent(message: SerialMessageToAgent) extends HardwareControlMessageExternalBinary
  case class SerialMonitorMessageToClient(message: SerialMessageToClient) extends HardwareControlMessageExternalBinary
}
