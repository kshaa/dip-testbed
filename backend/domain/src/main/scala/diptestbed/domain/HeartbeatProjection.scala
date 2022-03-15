package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.implicits._
import scala.concurrent.duration.FiniteDuration

object HeartbeatProjection {
  def expectHeartbeats[F[_]: Temporal, A](
    requestHeartbeats: F[Unit],
    finishHeartbeats: F[Unit],
    expectTimeout: FiniteDuration,
    heartbeatsInCycle: Int
  ): F[Unit] = {
    def requestAndWait(time: FiniteDuration) =
      requestHeartbeats >> implicitly[Temporal[F]].sleep(time)

    def partialRequestAndWait: F[Unit] = requestAndWait(expectTimeout / heartbeatsInCycle)

    List.fill(heartbeatsInCycle)(partialRequestAndWait).sequence.void >> finishHeartbeats
  }
}
