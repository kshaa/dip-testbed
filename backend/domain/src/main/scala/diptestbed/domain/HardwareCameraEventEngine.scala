package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.Parallel
import diptestbed.domain.EventEngine.{MessageResult, defaultOnError}

object HardwareCameraEventEngine {
  def onMessage[A, F[_]: Temporal: Parallel](
    lastState: => HardwareCameraState[A],
    die: F[Unit],
    send: (A, Any) => F[Unit],
    publish: (PubSubTopic, Any) => F[Unit],
    subscriptionMessage: (PubSubTopic, A) => Any,
    inquirer: => Option[A]
  ): HardwareCameraMessage => MessageResult[F, HardwareCameraEvent[A], HardwareCameraState[A]] = {
    EventEngine.onMessage(
      lastState,
      HardwareCameraMessageHandler.handle(inquirer),
      EventEngine.multiSideeffectProjection(
        List(
          HardwareCameraMailProjection.project(die, send, publish, subscriptionMessage),
          HardwareCameraHeartbeatProjection.project(send, publish),
        ),
      ),
      HardwareCameraEventStateProjection.project,
      defaultOnError[HardwareCameraError, F, A](inquirer, send),
    )
  }
}
