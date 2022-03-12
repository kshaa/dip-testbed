package diptestbed.web.control

import cats.Monad
import cats.data.EitherT
import diptestbed.database.driver.DatabaseOutcome.{DatabaseException, DatabaseResult}
import play.api.mvc._
import diptestbed.database.services.UserService
import diptestbed.domain.{HashedPassword, User}
import diptestbed.protocol.WebResult.Failure
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls.PipelineTypes.PipelineRes
import play.api.http.Status.UNAUTHORIZED
import cats.implicits._
import java.util.Base64
import scala.io.Source
import scala.util.Try

trait AuthController[F[_]] { self: ResultsController[F] =>
  val effectMonad: Monad[F]
  val userService: UserService[F]

  val authorizationErrorResult: Result = Failure("Failed to authenticate request")
    .withHttpStatus(UNAUTHORIZED)
    .withHeaders("WWW-Authenticate" -> "Basic")

  def withRequestAuthn[R, H](request: Request[R])(handler: (Request[R], DatabaseResult[Option[User]]) => F[H]): F[H] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    AuthController
      .extractRequestUser(
        request,
        userService.getUserByName,
      )
      .flatMap(handler(request, _))
  }

  def withRequestAuthnOrFail[R](request: Request[R])(handler: (Request[R], User) => PipelineRes[F]): PipelineRes[F] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    EitherT(
      withRequestAuthn(request)((request: Request[R], userResult: DatabaseResult[Option[User]]) =>
        userResult
          .toEitherT[F]
          .leftMap(databaseErrorResult)
          .flatMap(_.toRight(authorizationErrorResult).toEitherT[F])
          .flatMap(handler(request, _))
          .value,
      ),
    )
  }
}

object AuthController {
  type Username = String
  type Password = String

  def extractRequestBasicAuth[R](request: Request[R]): Option[(Username, Password)] = {
    val auth = request.headers.get("Authorization")
    val authParts = auth.map(_.trim.split(" +").toList)
    val usernamePassword = authParts.flatMap {
      case "Basic" :: secret :: Nil =>
        Try(Base64.getDecoder.decode(secret)).toOption
          .map(bytes => Source.fromBytes(bytes, "UTF-8").mkString)
          .flatMap(_.split(":").toList match {
            case username :: password :: Nil => Some((username, password))
            case _                           => None
          })
      case _ => None
    }

    usernamePassword
  }

  def extractRequestUser[F[_]: Monad, E, R](
    request: Request[R],
    getUserByName: Username => F[DatabaseResult[Option[(User, HashedPassword)]]],
  ): F[DatabaseResult[Option[User]]] =
    extractRequestBasicAuth(request) match {
      case None => Right[DatabaseException, Option[User]](None).pure[F].widen
      case Some((username, password)) =>
        getUserByName(username).map(_.map(_.flatMap {
          case (user, hashedPassword) =>
            val hashedPasswordFromRequest = HashedPassword.fromPassword(password, hashedPassword.salt)
            Option.when(hashedPasswordFromRequest == hashedPassword)(user)
        }))
    }
}
