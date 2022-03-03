package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.implicits._
import scala.concurrent.duration.FiniteDuration

object HeartbeatProjection {
  def expectHeartbeats[F[_]: Temporal, A](
    requestHeartbeats: F[Unit],
    finishHeartbeats: F[Unit],
    expectTimeout: FiniteDuration
  ): F[Unit] = {
    def requestAndWait(time: FiniteDuration) =
      requestHeartbeats >> implicitly[Temporal[F]].sleep(time)

    requestAndWait(expectTimeout / 3) >>
      requestAndWait(expectTimeout / 3) >>
      requestAndWait(expectTimeout / 3) >>
      finishHeartbeats
  }
}
