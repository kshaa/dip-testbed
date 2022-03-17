package diptestbed.domain

import cats.Monad
import cats.implicits._
import diptestbed.domain.HardwareCameraEvent._
import diptestbed.domain.HardwareCameraMessage._

object HardwareCameraAuthProjection {
  def project[F[_]: Monad, A](
    auth: (String, String) => F[Either[String, User]],
    send: (A, HardwareCameraMessage) => F[Unit]
  )(state: HardwareCameraState[A], event: HardwareCameraEvent[A]): Option[F[Unit]] = {
    event match {
      case CheckingAuth(username, password) =>
        Some(auth(username, password).flatMap(_.bimap(
          error => send(state.self, AuthFailure(error)),
          user => send(state.self, AuthSuccess(user))
        ).merge))
      case _ => None
    }
  }
}
