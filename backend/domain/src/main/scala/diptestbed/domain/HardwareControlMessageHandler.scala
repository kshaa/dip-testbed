package diptestbed.domain

import cats.data.NonEmptyList
import diptestbed.domain.HardwareControlAgentState._
import diptestbed.domain.HardwareControlEvent._
import diptestbed.domain.HardwareControlError._
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._

object HardwareControlMessageHandler {
  type HardwareControlResult[A] = Either[
    HardwareControlError,
    NonEmptyList[HardwareControlEvent[A]],
  ]

  def handle[A](
    inquirer: => Option[A],
  )(state: HardwareControlState[A], message: HardwareControlMessage): HardwareControlResult[A] = {
    state.auth match {
      case None =>
        message match {
          case m: AuthRequest   => Right(NonEmptyList.of(CheckingAuth(m.username, m.password)))
          case m: AuthSuccess   => Right(NonEmptyList.of(AuthSucceeded(m.user)))
          case m: AuthFailure   => Right(NonEmptyList.of(AuthFailed(m.reason)))
          case _ => Left(NoReaction)
        }
      case Some(_) =>
        message match {
          case _: StartLifecycle                                => Right(NonEmptyList.of(Started()))
          case _: EndLifecycle                                  => Right(NonEmptyList.of(Ended()))
          case m: UploadSoftwareRequest                         => handleUploadSoftwareRequest(state, inquirer, m)
          case m: UploadSoftwareResult                          => handleUploadSoftwareResult(state, m)
          case m: SerialMonitorRequest                          => handleSerialMonitorRequest(state, inquirer, m)
          case _: SerialMonitorRequestStop                      => handleSerialMonitorRequestStop()
          case m: SerialMonitorResult                           => handleSerialMonitorResult(state, m)
          case m: SerialMonitorMessageToClient                  => handleSerialMonitorMessageToClient(m)
          case m: SerialMonitorMessageToAgent                   => handleSerialMonitorMessageToAgent(m)
          case _: SerialMonitorListenersHeartbeatStart          => handleSerialMonitorListenersHeartbeatStart()
          case _: SerialMonitorListenersHeartbeatPing           => Left(NoReaction)
          case _: SerialMonitorListenersHeartbeatPong           => handleSerialMonitorListenersHeartbeatPong()
          case _: SerialMonitorListenersHeartbeatFinish         => handleSerialMonitorListenersHeartbeatFinish()
          case m: SerialMonitorUnavailable                      => handleMonitorUnavailable(m)
          case _: Ping                                          => Left(NoReaction)
          case _: AuthRequest | _: AuthSuccess | _ :AuthFailure => Left(NoReaction)

        }
    }
  }

  def handleUploadSoftwareRequest[A](
    state: HardwareControlState[A],
    inquirer: Option[A],
    message: UploadSoftwareRequest,
  ): HardwareControlResult[A] =
    if (state.agentState.isInstanceOf[Initial[A]])
      Right(NonEmptyList.of(UploadStarted(inquirer, message.softwareId)))
    else Left(StateForbidsRequest(message))

  def handleUploadSoftwareResult[A](
    state: HardwareControlState[A],
    message: UploadSoftwareResult,
  ): HardwareControlResult[A] =
    state.agentState match {
      case Uploading(oldInquirer) =>
        Right(NonEmptyList.of(UploadFinished[A](oldInquirer, message.error)))
      case _ => Left(StateForbidsRequest(message))
    }

  def handleSerialMonitorRequestStop[A](): HardwareControlResult[A] =
    Right(NonEmptyList.of(MonitorDropExpected[A]()))

  def handleSerialMonitorRequest[A](
    state: HardwareControlState[A],
    inquirer: Option[A],
    message: SerialMonitorRequest,
  ): HardwareControlResult[A] =
    if (state.agentState.isInstanceOf[Initial[A]])
      Right(NonEmptyList.of(MonitorConfigurationStarted[A](inquirer, message.serialConfig)))
    else Left(StateForbidsRequest(message))

  def handleSerialMonitorResult[A](
    state: HardwareControlState[A],
    message: SerialMonitorResult,
  ): HardwareControlResult[A] =
    state.agentState match {
      case ConfiguringMonitor(oldInquirer) =>
        Right(NonEmptyList.of(MonitorConfigurationFinished[A](oldInquirer, message.error)))
      case _ => Left(StateForbidsRequest(message))
    }

  def handleSerialMonitorMessageToClient[A](message: SerialMonitorMessageToClient): HardwareControlResult[A] =
    Right(NonEmptyList.of(MonitorMessageToClient(message.message.bytes)))

  def handleSerialMonitorMessageToAgent[A](message: SerialMonitorMessageToAgent): HardwareControlResult[A] =
    Right(NonEmptyList.of(MonitorMessageToAgent(message.message.bytes)))

  def handleSerialMonitorListenersHeartbeatStart[A](): HardwareControlResult[A] =
    Right(NonEmptyList.of(ListenerHeartbeatStarted[A]()))

  def handleSerialMonitorListenersHeartbeatPong[A](): HardwareControlResult[A] =
    Right(NonEmptyList.of(ListenerHeartbeatReceived[A]()))

  def handleSerialMonitorListenersHeartbeatFinish[A]() =
    Right(NonEmptyList.of(ListenerHeartbeatFinished[A]()))

  def handleMonitorUnavailable[A](message: SerialMonitorUnavailable) =
    Right(NonEmptyList.of(MonitorDropped[A](message.reason)))

}
