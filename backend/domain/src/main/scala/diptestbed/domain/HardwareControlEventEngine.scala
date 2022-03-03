package diptestbed.domain

import cats.{Applicative, Parallel}
import cats.effect.kernel.Temporal
import cats.implicits._
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareControlError._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._

object HardwareControlEventEngine {

  /**
    * This could be just send(inquirer, error), but backwards compatibility requires workarounds
    */
  def onError[A, F[_]: Applicative](
    send: (A, HardwareControlMessageExternal) => F[Unit],
    inquirer: => Option[A],
  )(error: HardwareControlError): F[Unit] = {
    val message: Option[HardwareControlMessageExternal] = error match {
      case StateForbidsRequest(request: UploadSoftwareRequest) =>
        Some(request)
      case StateForbidsRequest(request: UploadSoftwareResult) =>
        Some(request)
      case StateForbidsRequest(request: SerialMonitorRequest) =>
        Some(request)
      case StateForbidsRequest(request: SerialMonitorResult) =>
        Some(request)
      case StateForbidsRequest(_) => None
      case NoReaction             => None
    }
    (inquirer, message).tupled.traverse(send.tupled).void
  }

  def onMessage[A, F[_]: Temporal: Parallel](
    lastState: => HardwareControlState[A],
    send: (A, HardwareControlMessage) => F[Unit],
    publish: (PubSubTopic, HardwareControlMessage) => F[Unit],
    inquirer: => Option[A],
  ): HardwareControlMessage => MessageResult[F, HardwareControlEvent[A], HardwareControlState[A]] = {
    EventEngine.onMessage(
      lastState,
      HardwareControlMessageHandler.handle(inquirer),
      EventEngine.multiSideeffectProjection(
        List(
          HardwareControlMailProjection.project(send, publish),
          HardwareControlHeartbeatProjection.project(send, publish),
        ),
      ),
      HardwareControlEventStateProjection.project,
      onError[A, F](send, inquirer),
    )
  }
}
